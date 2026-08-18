#!/usr/bin/env python3
"""
Build the standard Advanced Analytics "Default Dashboard" for a Recruit CRM
account, replicating the reference dashboard (Metabase dashboard 12908) onto
that account's own data.

Every Metabase operation goes through the `mb` CLI via subprocess - this
script never calls the Metabase REST API directly and never touches a
database driver. It never fabricates data: every table/field/filter value it
uses is discovered live from the target account's own tables, and any entity
that doesn't exist for this account is skipped (not faked).

This script only ever adds new content - it never deletes, archives, or
modifies anything (per CLAUDE.md hard constraint 7). A card whose query
fails dry-run validation is simply never created (see build_card_query /
the dry-run check in main) - nothing gets created and then torn down. If a
"Default Dashboard" already exists for the account, the script stops rather
than touching it (see check_existing_dashboard).

Every card this script creates lives in a "Default Dashboard Charts"
sub-collection under the account's own collection (see
resolve_charts_collection) - the dashboard itself sits directly in the
account collection, one level up. This keeps default-dashboard charts
visually separate from anything the Chart Suggestions flow creates directly
in the account collection.

Usage:
    python3 scripts/create_default_dashboard.py --profile <mb-profile> [--account <number>]

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

TEMPLATE_PATH = Path(__file__).parent / "default_dashboard_template.json"
LOG_PATH = Path(__file__).parent.parent / "logs" / "history.jsonl"
PARENT_COLLECTION_ID = 199  # "Data Team WIP" - see CLAUDE.md
DEFAULT_DEAL_TARGET_GOAL = 1_000_000  # from the reference dashboard's "Deal Target Achieved" card


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
    """Find a table by its exact underlying name (e.g. 'candidates_662') on
    Production Starrocks specifically. Returns the table id, or None if not
    found there. Some accounts also have an older, unreachable copy of the
    same tables in the legacy Redshift database ("Recruit CRM", id
    13371338) - that copy must never be used, so the search is scoped to
    Starrocks and the result's database is double-checked defensively.
    The shared warehouse has far too many tables for a full metadata pull, so
    use `mb search` (per CLAUDE.md's "Locating the account's data") and
    confirm the exact raw name via `table get` - search results surface
    `display_name` under `name`, not the raw table name, so a substring
    search alone isn't a reliable exact match."""
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


def remap_field_ids(node, field_names, name_to_new_id):
    """Walk dataset_query, replacing every ['field', {...}, old_id] with the
    equivalent new field id, and return the set of old ids we couldn't map."""
    missing = set()

    def walk(n):
        if isinstance(n, list):
            if len(n) == 3 and n[0] == "field" and isinstance(n[2], (int, float)):
                old_id = int(n[2])
                col_name = field_names.get(str(old_id))
                new_id = name_to_new_id.get(col_name) if col_name else None
                if new_id is None:
                    missing.add(old_id)
                else:
                    n[2] = new_id
                return
            for x in n:
                walk(x)
        elif isinstance(n, dict):
            for v in n.values():
                walk(v)

    walk(node)
    return missing


def find_equality_literals(node, field_names, acc):
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
            col_name = field_names.get(str(old_id))
            if col_name:
                acc.append((col_name, node[3]))
        for x in node:
            find_equality_literals(x, field_names, acc)
    elif isinstance(node, dict):
        for v in node.values():
            find_equality_literals(v, field_names, acc)


def distinct_values(profile, database_id, table_id, field_id):
    query = {
        "lib/type": "mbql/query",
        "database": database_id,
        "stages": [{"lib/type": "mbql.stage/mbql", "source-table": table_id, "breakout": [["field", {}, field_id]]}],
    }
    result = mb_body(profile, "query", body=query)
    return {row[0] for row in result.get("data", {}).get("rows", [])}


def build_card_query(profile, card, resolved):
    entity = resolved.get(card["entity"])
    if entity is None:
        return None, f"entity '{card['entity']}' not available for this account"

    query = copy.deepcopy(card["dataset_query"])
    query["database"] = STARROCKS_DATABASE_ID
    query["stages"][0]["source-table"] = entity["table_id"]

    missing = remap_field_ids(query, card["field_names"], entity["fields"])
    if missing:
        return None, f"fields {missing} not found on {entity['table_name']}"

    # Verify every literal category value (e.g. hiring_stage = "Placed") this
    # card depends on actually occurs in the account's real data - stage/
    # status label values are not guaranteed portable across accounts.
    literals = []
    find_equality_literals(card["dataset_query"], card["field_names"], literals)
    for col_name, literal in literals:
        field_id = entity["fields"].get(col_name)
        if field_id is None:
            continue
        values = distinct_values(profile, STARROCKS_DATABASE_ID, entity["table_id"], field_id)
        if literal not in values:
            return None, f"value '{literal}' not found in {entity['table_name']}.{col_name} (has: {sorted(values)[:8]})"

    return query, None


def apply_deal_goal(card, visualization_settings, deal_goal):
    if card["key"] == "deal_target_achieved":
        visualization_settings = copy.deepcopy(visualization_settings)
        visualization_settings["progress.goal"] = deal_goal
    return visualization_settings


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
    """All cards this script creates live in a 'Default Dashboard Charts'
    sub-collection under the account's collection - only the dashboard
    itself sits directly in the account collection."""
    return resolve_child_collection(profile, account_collection_id, "Default Dashboard Charts")


def check_existing_dashboard(profile, account_collection_id):
    results = mb(profile, "search", "Default Dashboard", "--models", "dashboard", "--limit", "50")
    for item in results.get("data", []):
        if item.get("collection_id") == account_collection_id and item.get("name") == "Default Dashboard":
            return item["id"]
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="mb CLI profile to use (confirm via mb auth list/status first)")
    parser.add_argument("--account", help="Recruit CRM account number. Prompted for if omitted.")
    parser.add_argument("--deal-target-goal", type=float, default=DEFAULT_DEAL_TARGET_GOAL,
                         help=f"Goal value for the 'Deal Target Achieved' card (default: {DEFAULT_DEAL_TARGET_GOAL}, taken from the reference dashboard)")
    args = parser.parse_args()

    profile = args.profile

    print(f"Verifying Metabase authentication for profile '{profile}'...")
    base_url = verify_auth(profile)
    print(f"  authenticated against {base_url}")

    account = args.account or input("Which Recruit CRM account would you like to build the default dashboard for? Please provide the account number: ").strip()
    if not account:
        print("No account number provided.")
        sys.exit(1)

    template = json.loads(TEMPLATE_PATH.read_text())

    print(f"\nResolving account {account}'s tables...")
    resolved = resolve_entities(profile, account, template)
    if not resolved:
        reason = f"no tables found on Production Starrocks for account {account} (looked for e.g. 'candidates_{account}')"
        print(f"\nNo tables found for account {account} (looked for e.g. 'candidates_{account}'). "
              "Please verify the account number.")
        log_event("default_dashboard_failed", account=account, reason=reason, profile=profile)
        sys.exit(1)

    print(f"\nResolving destination collection under 'Data Team WIP' (id {PARENT_COLLECTION_ID})...")
    account_collection_id, created = resolve_account_collection(profile, account)
    print(f"  collection {account_collection_id} ({'created' if created else 'existing'})")

    charts_collection_id, charts_created = resolve_charts_collection(profile, account_collection_id)
    print(f"  'Default Dashboard Charts' collection {charts_collection_id} ({'created' if charts_created else 'existing'})")

    existing = check_existing_dashboard(profile, account_collection_id)
    if existing:
        print(f"\nA 'Default Dashboard' (id {existing}) already exists in this account's collection. "
              "Stopping rather than creating a duplicate.")
        log_event("default_dashboard_skipped", account=account, dashboard_id=existing,
                  collection_id=account_collection_id, reason="Default Dashboard already exists", profile=profile)
        sys.exit(1)

    print(f"\nCreating cards ({len(template['cards'])} in template)...")
    created_cards = {}  # key -> {id, tab, layout, param_mappings, entity}
    skipped = []
    for card in template["cards"]:
        query, err = build_card_query(profile, card, resolved)
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

        viz = apply_deal_goal(card, card["visualization_settings"], args.deal_target_goal)
        body = {
            "name": card["name"],
            "display": card["display"],
            "dataset_query": query,
            "visualization_settings": viz,
            "collection_id": charts_collection_id,
        }
        result = mb_body(profile, "card", "create", body=body)
        created_cards[card["key"]] = {
            "id": result["id"],
            "tab": card["tab"],
            "layout": card["layout"],
            "param_mappings": card["param_mappings"],
            "entity": card["entity"],
        }
        print(f"  OK    {card['name']} -> card {result['id']}")

    if not created_cards:
        print("\nNo cards could be created for this account. Nothing to assemble into a dashboard.")
        log_event("default_dashboard_failed", account=account,
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
        parameter_mappings = []
        for pm in c["param_mappings"]:
            new_field_id = resolved[c["entity"]]["fields"].get(pm["column_name"])
            if new_field_id is None:
                continue
            parameter_mappings.append({
                "parameter_id": pm["parameter_slug"],
                "target": ["dimension", ["field", new_field_id, None]],
            })
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

    parameters = []
    for p in template["dashboard_parameters"]:
        if p["slug"] == "recruiter" and "call_logs" not in resolved:
            continue  # only call-log cards use this filter
        parameters.append({
            "id": p["slug"],
            "name": p["name"],
            "slug": p["slug"],
            "type": p["type"],
            **({"default": p["default"]} if "default" in p else {}),
        })

    dashboard_body = {
        "name": "Default Dashboard",
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

    print(f"\nDone. 'Default Dashboard' (id {dashboard_id}) for account {account}:")
    print(f"  {len(created_cards)} cards created in 'Default Dashboard Charts' (collection {charts_collection_id}), "
          f"{len(skipped)} skipped, dashboard in collection {account_collection_id}")
    if skipped:
        print("  Skipped:")
        for name, reason in skipped:
            print(f"    - {name}: {reason}")
    print(f"  {base_url}/dashboard/{dashboard_id}")

    log_event(
        "default_dashboard_created",
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
