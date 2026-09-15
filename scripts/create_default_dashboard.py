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

This flow always saves into the account's own collection (see CLAUDE.md
"Where created charts live" - Convention B), never "Data Team WIP" - a
genuine top-level collection (never nested under collection 199), named
"Shared Collection <account>" by default, though some accounts already
have one under a different, custom name (see resolve_account_own_collection).
This script never creates or touches that parent collection itself - if no
matching top-level collection exists for the account, it stops rather than
creating one or falling back to "Data Team WIP". Once found, that
collection mandatorily gets three sub-collections - Cards, Models,
Drill-downs (see ensure_structural_subcollections) - created if missing,
without touching anything already sitting directly in the account's
collection. Every card this script creates lives in a "Default Dashboard
Cards" sub-collection under Cards (see resolve_dashboard_cards_collection);
the dashboard itself is created directly in the account's own collection
and pinned there (`collection_position`). If a "Default Dashboard" already
exists for this account under the old "Data Team WIP" convention (from
before this flow switched to the account's own collection), the script
stops rather than creating a second copy elsewhere (see
check_legacy_dashboard).

Every monetary card (Total Cost of Calls, Deal Target Achieved, Total Deal
Value per Company, Deal Value Closed Over Time) is formatted in the currency
confirmed for this run (see --currency) rather than a hardcoded symbol - a
client could be billed in USD, EUR, GBP, or anything else, and this is never
assumed (see CLAUDE.md "Value formatting").

Usage:
    python3 scripts/create_default_dashboard.py --profile <mb-profile> [--account <number>] [--currency <ISO code>]

If --account or --currency is omitted, the script prompts for it interactively.
"""
import argparse
import copy
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TEMPLATE_PATH = Path(__file__).parent / "default_dashboard_template.json"
LOG_PATH = Path(__file__).parent.parent / "logs" / "history.jsonl"
LEGACY_PARENT_COLLECTION_ID = 199  # "Data Team WIP" - see CLAUDE.md; only
# consulted here to check for a pre-existing dashboard from before this flow
# switched to the account's own collection (see check_legacy_dashboard).
DASHBOARD_NAME = "Default Dashboard"
CARDS_SUBCOLLECTION_NAME = f"{DASHBOARD_NAME} Cards"
STRUCTURAL_SUBCOLLECTIONS = ("Cards", "Models", "Drill-downs")  # mandatory
# under the account's own collection - see CLAUDE.md "Where created charts
# live" (Convention B).
DEFAULT_DEAL_TARGET_GOAL = 1_000_000  # from the reference dashboard's "Deal Target Achieved" card
IST = ZoneInfo("Asia/Kolkata")


def log_event(event_type, **fields):
    """Append one entry to logs/history.jsonl - see CLAUDE.md "History log"."""
    entry = {"timestamp": datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S+05:30"), "type": event_type, **fields}
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

# Every Recruit CRM account's data lives in "Production Starrocks" (this is
# the live, queryable copy). Some accounts also have an older, unreachable
# copy of the same tables in the legacy "Recruit CRM" Redshift database
# (id 13371338) - that one must never be used.
STARROCKS_DATABASE_ID = 13371569

# Cards whose value is a monetary sum - see CLAUDE.md "Value formatting".
# Their currency is never assumed (a client could be billed in USD, EUR,
# GBP, etc.) - it's confirmed with the user once per run (see --currency)
# and applied here instead of a hardcoded symbol.
MONETARY_CARD_KEYS = {"total_cost_of_calls", "deal_target_achieved", "total_deal_value_per_company", "deal_value_closed_over_time"}
CURRENCY_CODE_RE = re.compile(r"^[A-Za-z]{3}$")


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


def apply_currency_formatting(card, visualization_settings, currency_code):
    """Format this card's monetary total using the currency confirmed with
    the user (see CLAUDE.md "Value formatting") - never a hardcoded symbol,
    since a client could be billed in USD, EUR, GBP, or anything else."""
    if card["key"] not in MONETARY_CARD_KEYS:
        return visualization_settings
    visualization_settings = copy.deepcopy(visualization_settings)
    column_settings = visualization_settings.setdefault("column_settings", {})
    column_settings['["name","sum"]'] = {
        "number_style": "currency",
        "currency": currency_code,
        "currency_style": "symbol",
    }
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


def resolve_account_own_collection(profile, account):
    """Find this account's own client-facing collection - a genuine
    top-level collection (parent_id null, never nested under "Data Team
    WIP") named "Shared Collection <account>" by default, though some
    accounts already have one under a different, custom name (see
    CLAUDE.md "Where created charts live" - Convention B). `mb collection
    tree` returns a flat list of every top-level collection (each carrying
    its own nested `children`) - matched here by the account number
    appearing in one of *those* top-level names, never by descending into
    any collection's children (that would also catch "Data Team WIP"
    sub-collections sharing the same number, which are a different
    convention). This project never creates this parent collection itself -
    returns (None, None) if nothing matches, and the caller must stop."""
    tree = mb(profile, "collection", "tree")
    if not isinstance(tree, list):
        tree = [tree]
    matches = [c for c in tree if account in c["name"]]
    if not matches:
        return None, None
    if len(matches) > 1:
        print(f"  Multiple top-level collections match account {account}:")
        for c in matches:
            print(f"    {c['id']}: {c['name']!r}")
        chosen = input("  Which collection id is this account's own collection? ").strip()
        for c in matches:
            if str(c["id"]) == chosen:
                return c["id"], c["name"]
        print(f"  '{chosen}' doesn't match any of the listed collection ids.")
        sys.exit(1)
    return matches[0]["id"], matches[0]["name"]


def ensure_structural_subcollections(profile, parent_id):
    """Ensure the account's own collection has its three mandatory
    sub-collections - Cards, Models, Drill-downs (see CLAUDE.md "Where
    created charts live" - Convention B) - creating whichever are missing.
    Never touches anything else already sitting in the parent collection."""
    return {name: resolve_child_collection(profile, parent_id, name)[0] for name in STRUCTURAL_SUBCOLLECTIONS}


def resolve_dashboard_cards_collection(profile, cards_collection_id):
    """This run's cards live in a 'Default Dashboard Cards' sub-collection
    under the account's own collection's Cards folder."""
    return resolve_child_collection(profile, cards_collection_id, CARDS_SUBCOLLECTION_NAME)


def check_legacy_dashboard(profile, account):
    """Look for a 'Default Dashboard' already sitting in this account's old
    'Data Team WIP' sub-collection, from before this flow switched to the
    account's own collection (see CLAUDE.md "Where created charts live" -
    "Avoiding a duplicate across the two conventions"). Returns
    (dashboard_id, collection_id), or (None, None) if there isn't one."""
    tree = mb(profile, "collection", "tree")
    root = tree[0] if isinstance(tree, list) else tree
    wip_node = find_collection_node(root, LEGACY_PARENT_COLLECTION_ID)
    if wip_node is None:
        return None, None
    for child in wip_node.get("children", []):
        if child["name"].strip() == account:
            legacy_collection_id = child["id"]
            results = mb(profile, "search", DASHBOARD_NAME, "--models", "dashboard", "--limit", "50")
            for item in results.get("data", []):
                if item.get("collection_id") == legacy_collection_id and item.get("name") == DASHBOARD_NAME:
                    return item["id"], legacy_collection_id
    return None, None


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
    parser.add_argument("--deal-target-goal", type=float, default=DEFAULT_DEAL_TARGET_GOAL,
                         help=f"Goal value for the 'Deal Target Achieved' card (default: {DEFAULT_DEAL_TARGET_GOAL}, taken from the reference dashboard)")
    parser.add_argument("--currency", help="ISO 4217 code (e.g. USD, EUR, GBP, INR) for this account's monetary "
                         "charts (Total Cost of Calls, Deal Target Achieved, Total Deal Value per Company, Deal "
                         "Value Closed Over Time). Never assumed - prompted for if omitted (see CLAUDE.md "
                         "\"Value formatting\").")
    args = parser.parse_args()

    profile = args.profile

    currency_code = args.currency
    while not currency_code or not CURRENCY_CODE_RE.match(currency_code):
        if currency_code:
            print(f"'{currency_code}' doesn't look like a 3-letter ISO 4217 currency code - try again.")
        currency_code = input("Which currency should this account's monetary charts be formatted in "
                               "(ISO code, e.g. USD, EUR, GBP, INR)? ").strip()
    currency_code = currency_code.upper()

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

    print(f"\nResolving account {account}'s own collection...")
    account_collection_id, account_collection_name = resolve_account_own_collection(profile, account)
    if account_collection_id is None:
        print(f"\nNo existing top-level account collection found for account {account} (looked for the "
              f"account number in a genuine top-level collection's name, e.g. 'Shared Collection {account}', "
              "outside 'Data Team WIP'). This project never creates that parent collection itself - it needs "
              "to exist first. Please create it (or tell me its existing name/id) and re-run.")
        log_event("default_dashboard_failed", account=account, collection_mode="account_collection",
                  reason="no existing top-level account collection found", profile=profile)
        sys.exit(1)
    print(f"  collection {account_collection_id} ({account_collection_name!r})")

    legacy_dashboard_id, legacy_collection_id = check_legacy_dashboard(profile, account)
    if legacy_dashboard_id:
        print(f"\nA '{DASHBOARD_NAME}' (id {legacy_dashboard_id}) already exists in this account's old "
              f"'Data Team WIP' collection (id {legacy_collection_id}), from before this flow switched to "
              "the account's own collection. Stopping rather than creating a second copy elsewhere.")
        log_event("default_dashboard_skipped", account=account, collection_mode="account_collection",
                  dashboard_id=legacy_dashboard_id, collection_id=legacy_collection_id,
                  reason=f"{DASHBOARD_NAME} already exists in legacy Data Team WIP collection", profile=profile)
        sys.exit(1)

    structural = ensure_structural_subcollections(profile, account_collection_id)
    print(f"  Cards {structural['Cards']}, Models {structural['Models']}, Drill-downs {structural['Drill-downs']}")

    cards_collection_id, cards_created = resolve_dashboard_cards_collection(profile, structural["Cards"])
    print(f"  '{CARDS_SUBCOLLECTION_NAME}' collection {cards_collection_id} ({'created' if cards_created else 'existing'})")

    existing = check_existing_dashboard(profile, account_collection_id)
    if existing:
        print(f"\nA '{DASHBOARD_NAME}' (id {existing}) already exists in this account's collection. "
              "Stopping rather than creating a duplicate.")
        log_event("default_dashboard_skipped", account=account, collection_mode="account_collection",
                  dashboard_id=existing, collection_id=account_collection_id,
                  reason=f"{DASHBOARD_NAME} already exists", profile=profile)
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
        viz = apply_currency_formatting(card, viz, currency_code)
        body = {
            "name": card["name"],
            "display": card["display"],
            "dataset_query": query,
            "visualization_settings": viz,
            "collection_id": cards_collection_id,
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
        log_event("default_dashboard_failed", account=account, collection_mode="account_collection",
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
        "name": DASHBOARD_NAME,
        "collection_id": account_collection_id,
        "collection_position": 1,  # pinned - see CLAUDE.md "Where created charts live"
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
    print(f"  {len(created_cards)} cards created in '{CARDS_SUBCOLLECTION_NAME}' (collection {cards_collection_id}), "
          f"{len(skipped)} skipped, dashboard pinned in collection {account_collection_id} ({account_collection_name!r})")
    if skipped:
        print("  Skipped:")
        for name, reason in skipped:
            print(f"    - {name}: {reason}")
    print(f"  {base_url}/dashboard/{dashboard_id}")

    log_event(
        "default_dashboard_created",
        account=account,
        collection_mode="account_collection",
        dashboard_id=dashboard_id,
        collection_id=account_collection_id,
        cards_collection_id=structural["Cards"],
        models_collection_id=structural["Models"],
        drilldowns_collection_id=structural["Drill-downs"],
        charts_collection_id=cards_collection_id,
        cards_created=len(created_cards),
        cards_skipped=[{"name": n, "reason": r} for n, r in skipped],
        profile=profile,
        currency=currency_code,
    )


if __name__ == "__main__":
    main()
