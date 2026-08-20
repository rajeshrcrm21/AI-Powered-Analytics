#!/usr/bin/env python3
"""
Build the standard Advanced Analytics "Important Metrics Dashboard" for a
Recruit CRM account, replicating the reference dashboard (Metabase dashboard
12708) onto that account's own data.

Every Metabase operation goes through the `mb` CLI via subprocess - this
script never calls the Metabase REST API directly and never touches a
database driver. It never fabricates data: every table/field/filter value it
uses is discovered live from the target account's own tables, and any entity
that doesn't exist for this account is skipped (not faked).

This script only ever adds new content - it never deletes, archives, or
modifies anything (per CLAUDE.md hard constraint 7). A card whose query
fails dry-run validation is simply never created - nothing gets created and
then torn down. If an "Important Metrics Dashboard" already exists for the
account, the script stops rather than touching it (see
check_existing_dashboard).

Every card this script creates lives in an "Important Metrics Dashboard
Charts" sub-collection under the account's own collection (see
resolve_charts_collection) - the dashboard itself sits directly in the
account collection, one level up, mirroring the Default Dashboard flow's
"Default Dashboard Charts" convention (see create_default_dashboard.py).

Unlike the Default Dashboard's cards, several of this dashboard's cards
reference more than one entity (e.g. a job/assignment join for ratio cards),
and one card ("Average Time Spent On Each Hiring Stage") is native SQL that
uses a window function (LEAD) to measure time between consecutive stage
changes - genuinely not expressible in MBQL, per CLAUDE.md's chart-creation
guidance. Its account-suffixed table name is a literal substring in the SQL
text and is substituted per-account (see native_table_refs handling in
build_card_query) in addition to the usual field-id remapping.

Usage:
    python3 scripts/create_important_metrics_dashboard.py --profile <mb-profile> [--account <number>]

If --account is omitted, the script prompts for it interactively.
"""
import argparse
import copy
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent / "important_metrics_dashboard_template.json"
LOG_PATH = Path(__file__).parent.parent / "logs" / "history.jsonl"
PARENT_COLLECTION_ID = 199  # "Data Team WIP" - see CLAUDE.md
DASHBOARD_NAME = "Important Metrics Dashboard"
CHARTS_COLLECTION_NAME = "Important Metrics Dashboard Charts"


def log_event(event_type, **fields):
    """Append one entry to logs/history.jsonl - see CLAUDE.md "History log"."""
    entry = {"timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "type": event_type, **fields}
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

# Every Recruit CRM account's data lives in "Production Starrocks" (this is
# the live, queryable copy). Some accounts also have an older, unreachable
# copy of the same tables in the legacy "Recruit CRM" Redshift database
# (id 13371338) - that one must never be used.
STARROCKS_DATABASE_ID = 13371569


class MbError(RuntimeError):
    pass


def mb(profile, *args, allow_fail=False):
    """Shell out to the mb CLI. Never talks to Metabase any other way."""
    cmd = ["mb", *args, "--profile", profile, "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode not in (0,) and not allow_fail:
        raise MbError(
            f"mb {' '.join(args)} failed (exit {result.returncode}):\n{result.stderr.strip() or result.stdout.strip()}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        if allow_fail:
            return None
        raise MbError(f"mb {' '.join(args)} did not return JSON:\n{result.stdout}\n{result.stderr}")


def mb_body(profile, *args, body):
    """Same as mb(), but writes `body` to a temp JSON file passed via --file."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(body, f)
        tmp_path = f.name
    try:
        return mb(profile, *args, "--file", tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def verify_auth(profile):
    status = mb(profile, "auth", "status", allow_fail=True)
    if status is None or not status.get("present") or status.get("user") is None:
        print(
            "Metabase authentication could not be verified. "
            "Please check the Metabase API key/configuration."
        )
        sys.exit(1)
    return status["url"]


def discover_table(profile, table_name):
    """Find a table by its exact underlying name (e.g. 'jobs_662') on
    Production Starrocks specifically. Returns the table id, or None if not
    found there. Some accounts also have an older, unreachable copy of the
    same tables in the legacy Redshift database ("Recruit CRM", id
    13371338) - that copy must never be used, so the search is scoped to
    Starrocks and the result's database is double-checked defensively."""
    results = mb(profile, "search", table_name, "--models", "table", "--db-id", str(STARROCKS_DATABASE_ID), "--limit", "10")
    for item in results.get("data", []):
        table = mb(profile, "table", "get", str(item["id"]), "--fields", "id,name,db_id")
        if table.get("name") == table_name and table.get("db_id") == STARROCKS_DATABASE_ID:
            return table["id"]
    return None


def get_fields(profile, table_id):
    """name -> field id map for a table, paginating if needed."""
    fields = {}
    offset = 0
    while True:
        resp = mb(profile, "table", "fields", str(table_id), "--offset", str(offset))
        for f in resp.get("data", []):
            fields[f["name"]] = f["id"]
        if not resp.get("has_more"):
            break
        offset = resp["next_offset"]
    return fields


def resolve_entities(profile, account, template):
    """For every entity referenced by the template, find this account's real
    table + field map. Entities that don't exist are omitted (not faked)."""
    resolved = {}
    for entity, prefix in template["entity_table_prefix"].items():
        table_name = f"{prefix}_{account}"
        table_id = discover_table(profile, table_name)
        if table_id is None:
            print(f"  - {table_name}: not found on Production Starrocks, skipping cards for '{entity}'")
            continue
        fields = get_fields(profile, table_id)
        resolved[entity] = {"table_id": table_id, "fields": fields, "table_name": table_name}
        print(f"  - {table_name}: table {table_id}, {len(fields)} fields")
    return resolved


def remap_query(node, resolved, field_entity_map, table_entity_map):
    """Walk a dataset_query, replacing every ['field', {...}, old_id] with
    this account's equivalent field id (via field_entity_map: old_id ->
    {entity, column}) and every {"source-table": old_id} with this
    account's equivalent table id (via table_entity_map: old_id -> entity).
    A card can reference more than one entity (e.g. a job/assignment join),
    so - unlike a single flat field map - each old id is resolved through
    its own entity. Returns the set of old ids we couldn't map."""
    missing = set()

    def walk(n):
        if isinstance(n, list):
            if len(n) == 3 and n[0] == "field" and isinstance(n[2], (int, float)):
                old_id = int(n[2])
                info = field_entity_map.get(str(old_id))
                entity = resolved.get(info["entity"]) if info else None
                new_id = entity["fields"].get(info["column"]) if entity else None
                if new_id is None:
                    missing.add(old_id)
                else:
                    n[2] = new_id
                return
            for x in n:
                walk(x)
        elif isinstance(n, dict):
            for k, v in n.items():
                if k == "source-table" and isinstance(v, (int, float)):
                    entity_name = table_entity_map.get(str(int(v)))
                    entity = resolved.get(entity_name) if entity_name else None
                    if entity is None:
                        missing.add(("table", int(v)))
                    else:
                        n[k] = entity["table_id"]
                else:
                    walk(v)

    walk(node)
    return missing


def find_equality_literals(node, field_entity_map, acc):
    """Scan a dataset_query for ['=', {...}, ['field', {...}, id], <literal>]
    triples so we can verify the literal category value actually occurs in
    this account's data before trusting a filter/count-where on it."""
    if isinstance(node, list):
        if (
            len(node) == 4
            and node[0] == "="
            and isinstance(node[2], list)
            and node[2][0] == "field"
            and isinstance(node[3], str)
        ):
            old_id = int(node[2][2])
            info = field_entity_map.get(str(old_id))
            if info:
                acc.append((info["entity"], info["column"], node[3]))
        for x in node:
            find_equality_literals(x, field_entity_map, acc)
    elif isinstance(node, dict):
        for v in node.values():
            find_equality_literals(v, field_entity_map, acc)


def distinct_values(profile, database_id, table_id, field_id):
    query = {
        "lib/type": "mbql/query",
        "database": database_id,
        "stages": [{"lib/type": "mbql.stage/mbql", "source-table": table_id, "breakout": [["field", {}, field_id]]}],
    }
    result = mb_body(profile, "query", body=query)
    return {row[0] for row in result.get("data", {}).get("rows", [])}


def build_card_query(profile, card, resolved, field_entity_map, table_entity_map):
    missing_entities = [e for e in card["entities"] if e not in resolved]
    if missing_entities:
        return None, f"entities {missing_entities} not available for this account"

    query = copy.deepcopy(card["dataset_query"])
    query["database"] = STARROCKS_DATABASE_ID

    missing = remap_query(query, resolved, field_entity_map, table_entity_map)
    if missing:
        return None, f"fields/tables {missing} not found for this account"

    for stage in query["stages"]:
        if "native" not in stage:
            continue
        # Native SQL cards embed the account-suffixed table name as a
        # literal substring in the query text (not a field/table
        # reference), so it needs its own substitution pass.
        for ref in card.get("native_table_refs", []):
            entity = resolved[ref["entity"]]
            stage["native"] = stage["native"].replace(ref["raw_table_name"], entity["table_name"])
        # `mb dashboard/card get --full` reads template-tags back as a
        # list, but authoring/dry-run requires the map-keyed-by-name shape
        # (see `mb skills get native-sql`) - convert if needed.
        if isinstance(stage.get("template-tags"), list):
            stage["template-tags"] = {tag["name"]: tag for tag in stage["template-tags"]}

    # Verify every literal category value (e.g. hiring_stage = "Placed") this
    # card depends on actually occurs in the account's real data - stage/
    # status label values are not guaranteed portable across accounts.
    literals = []
    find_equality_literals(card["dataset_query"], field_entity_map, literals)
    for entity_name, col_name, literal in literals:
        entity = resolved.get(entity_name)
        if entity is None:
            continue
        field_id = entity["fields"].get(col_name)
        if field_id is None:
            continue
        values = distinct_values(profile, STARROCKS_DATABASE_ID, entity["table_id"], field_id)
        if literal not in values:
            return None, f"value '{literal}' not found in {entity['table_name']}.{col_name} (has: {sorted(values)[:8]})"

    return query, None


def build_parameter_mapping(card, resolved):
    pm = card["param_mapping"]
    if pm["kind"] == "template_tag":
        return {"parameter_id": pm["parameter_slug"], "target": ["dimension", ["template-tag", pm["tag"]], {"stage-number": 0}]}
    entity = resolved.get(pm["entity"])
    if entity is None:
        return None
    new_field_id = entity["fields"].get(pm["column"])
    if new_field_id is None:
        return None
    return {
        "parameter_id": pm["parameter_slug"],
        "target": ["dimension", ["field", new_field_id, {"base-type": pm.get("base_type", "type/DateTimeWithLocalTZ")}], {"stage-number": 0}],
    }


def find_collection_node(node, target_id):
    """`mb collection tree` takes no id argument - it always returns the
    whole tree from the true root, regardless of what's passed - so finding
    a non-root collection's children means walking the tree ourselves."""
    if node["id"] == target_id:
        return node
    for child in node.get("children", []):
        found = find_collection_node(child, target_id)
        if found is not None:
            return found
    return None


def resolve_child_collection(profile, parent_id, name):
    """Find a child collection of `parent_id` by exact (trimmed) name, or
    create it if it doesn't exist yet. Returns (collection_id, created)."""
    tree = mb(profile, "collection", "tree")
    root = tree[0] if isinstance(tree, list) else tree
    parent_node = find_collection_node(root, parent_id)
    for child in (parent_node.get("children", []) if parent_node else []):
        if child["name"].strip() == name:
            return child["id"], False
    created = mb_body(
        profile, "collection", "create",
        body={"name": name, "parent_id": parent_id},
    )
    return created["id"], True


def resolve_account_collection(profile, account):
    return resolve_child_collection(profile, PARENT_COLLECTION_ID, account)


def resolve_charts_collection(profile, account_collection_id):
    """All cards this script creates live in an 'Important Metrics
    Dashboard Charts' sub-collection under the account's collection - only
    the dashboard itself sits directly in the account collection."""
    return resolve_child_collection(profile, account_collection_id, CHARTS_COLLECTION_NAME)


def check_existing_dashboard(profile, account_collection_id):
    results = mb(profile, "search", DASHBOARD_NAME, "--models", "dashboard", "--limit", "50")
    for item in results.get("data", []):
        if item.get("collection_id") == account_collection_id and item.get("name") == DASHBOARD_NAME:
            return item["id"]
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="mb CLI profile to use (confirm via mb auth list/status first)")
    parser.add_argument("--account", help="Recruit CRM account number. Prompted for if omitted.")
    args = parser.parse_args()

    profile = args.profile

    print(f"Verifying Metabase authentication for profile '{profile}'...")
    base_url = verify_auth(profile)
    print(f"  authenticated against {base_url}")

    account = args.account or input("Which Recruit CRM account would you like to build the important metrics dashboard for? Please provide the account number: ").strip()
    if not account:
        print("No account number provided.")
        sys.exit(1)

    template = json.loads(TEMPLATE_PATH.read_text())
    field_entity_map = template["field_entity_map"]
    table_entity_map = template["table_entity_map"]

    print(f"\nResolving account {account}'s tables...")
    resolved = resolve_entities(profile, account, template)
    if not resolved:
        reason = f"no tables found on Production Starrocks for account {account} (looked for e.g. 'jobs_{account}')"
        print(f"\nNo tables found for account {account} (looked for e.g. 'jobs_{account}'). "
              "Please verify the account number.")
        log_event("important_metrics_dashboard_failed", account=account, reason=reason, profile=profile)
        sys.exit(1)

    print(f"\nResolving destination collection under 'Data Team WIP' (id {PARENT_COLLECTION_ID})...")
    account_collection_id, created = resolve_account_collection(profile, account)
    print(f"  collection {account_collection_id} ({'created' if created else 'existing'})")

    charts_collection_id, charts_created = resolve_charts_collection(profile, account_collection_id)
    print(f"  '{CHARTS_COLLECTION_NAME}' collection {charts_collection_id} ({'created' if charts_created else 'existing'})")

    existing = check_existing_dashboard(profile, account_collection_id)
    if existing:
        print(f"\nA '{DASHBOARD_NAME}' (id {existing}) already exists in this account's collection. "
              "Stopping rather than creating a duplicate.")
        log_event("important_metrics_dashboard_skipped", account=account, dashboard_id=existing,
                  collection_id=account_collection_id, reason=f"{DASHBOARD_NAME} already exists", profile=profile)
        sys.exit(1)

    print(f"\nCreating cards ({len(template['cards'])} in template)...")
    created_cards = {}  # key -> {id, tab, layout, param_mapping}
    skipped = []
    for card in template["cards"]:
        query, err = build_card_query(profile, card, resolved, field_entity_map, table_entity_map)
        if err:
            skipped.append((card["name"], err))
            print(f"  SKIP  {card['name']}: {err}")
            continue

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(query, f)
            tmp_path = f.name
        validation = subprocess.run(
            ["mb", "query", "--file", tmp_path, "--dry-run", "--profile", profile, "--json"],
            capture_output=True, text=True,
        )
        Path(tmp_path).unlink(missing_ok=True)
        if validation.returncode != 0:
            skipped.append((card["name"], f"query failed validation: {validation.stdout or validation.stderr}"))
            print(f"  SKIP  {card['name']}: failed dry-run validation")
            continue

        body = {
            "name": card["name"],
            "display": card["display"],
            "dataset_query": query,
            "visualization_settings": card["visualization_settings"],
            "collection_id": charts_collection_id,
        }
        result = mb_body(profile, "card", "create", body=body)
        created_cards[card["key"]] = {
            "id": result["id"],
            "tab": card["tab"],
            "layout": card["layout"],
            "param_mapping": card["param_mapping"],
        }
        print(f"  OK    {card['name']} -> card {result['id']}")

    if not created_cards:
        print("\nNo cards could be created for this account. Nothing to assemble into a dashboard.")
        log_event("important_metrics_dashboard_failed", account=account,
                  reason="no cards could be created", cards_skipped=[{"name": n, "reason": r} for n, r in skipped],
                  profile=profile)
        sys.exit(1)

    print(f"\nCreated {len(created_cards)}/{len(template['cards'])} cards ({len(skipped)} skipped).")

    print("\nAssembling dashboard...")
    tabs_present = []
    for t in template["tabs"]:
        if any(c["tab"] == t for c in created_cards.values()):
            tabs_present.append(t)
    tab_ids = {name: -(i + 1) for i, name in enumerate(tabs_present)}

    dashcards = []
    dashcard_id = -1
    for c in created_cards.values():
        mapping = build_parameter_mapping({"param_mapping": c["param_mapping"]}, resolved)
        parameter_mappings = [mapping] if mapping else []
        dashcards.append({
            "id": dashcard_id,
            "card_id": c["id"],
            "dashboard_tab_id": tab_ids[c["tab"]],
            "row": c["layout"]["row"],
            "col": c["layout"]["col"],
            "size_x": c["layout"]["size_x"],
            "size_y": c["layout"]["size_y"],
            "parameter_mappings": parameter_mappings,
        })
        dashcard_id -= 1

    parameters = [
        {"id": p["slug"], "name": p["name"], "slug": p["slug"], "type": p["type"]}
        for p in template["dashboard_parameters"]
    ]

    dashboard_body = {
        "name": DASHBOARD_NAME,
        "collection_id": account_collection_id,
        "tabs": [{"id": tab_ids[name], "name": name, "position": i} for i, name in enumerate(tabs_present)],
        "dashcards": dashcards,
        "parameters": parameters,
    }
    dashboard = mb_body(profile, "dashboard", "create", body=dashboard_body)
    dashboard_id = dashboard["id"]

    print(f"  dashboard {dashboard_id} created")

    print("\nVerifying...")
    verify = mb(profile, "dashboard", "get", str(dashboard_id), "--fields", "id,name,collection_id")
    assert verify["id"] == dashboard_id

    print(f"\nDone. '{DASHBOARD_NAME}' (id {dashboard_id}) for account {account}:")
    print(f"  {len(created_cards)} cards created in '{CHARTS_COLLECTION_NAME}' (collection {charts_collection_id}), "
          f"{len(skipped)} skipped, dashboard in collection {account_collection_id}")
    if skipped:
        print("  Skipped:")
        for name, reason in skipped:
            print(f"    - {name}: {reason}")
    print(f"  {base_url}/dashboard/{dashboard_id}")

    log_event(
        "important_metrics_dashboard_created",
        account=account,
        dashboard_id=dashboard_id,
        collection_id=account_collection_id,
        charts_collection_id=charts_collection_id,
        cards_created=len(created_cards),
        cards_skipped=[{"name": n, "reason": r} for n, r in skipped],
        profile=profile,
    )


if __name__ == "__main__":
    main()
