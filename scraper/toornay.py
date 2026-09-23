"""
This is the central file for managing toornays.



Steps going forward:
    - make the data.json the players.json, where all the player data is stored and updated
    - move the player data aquisition to a players.py

    - add a toornay.json where all the tourney info is stored
    - move the toornay data aquisition to a toornay.py

Table calculation outline:
    - tables are based on stages
    - go through all groups (only 1), rounds (up to 7) and matches
      and gather data for each opponent:
      Games FOR and AGAINST: fill this table:
        For each match:
            - find opponent one in table or create new
            - add match to rounds using current round data
            - find opponent two in table or create new
            - add match to rounds using current round data
    - go through table and calculate buchholz:
        For each player in table:
            - for each round in player:
                - add up points of these players

table = { 
    "949playerID1234": {
        wins: 5,
        losses: 2,
        diff: +3,
        pts: 0
        rounds: [ {
            id: "",
            number: 1,
            opponentID: "2344...2343",
            result: [1,1],
            match: "matchID",

Add resulting table array to the current stage!



# Games metadata: https://www.npoint.io/docs/ff1016d44df25eed664e
# toornay.json schema: https://www.npoint.io/docs/fae26317d796ff6c6302

toornay = { id: "8544694639084077056",
            stages: [ { ...
                id:
                name:
                groups: [ { ...
                    rounds: [ { ...
                        matches: [ { ...
                table: [{ ... }]



# players = [
#           { "Name": "cap.."
#             "ID": "3423423"
#             "Image": "http://..."
#             "Elo1v1": "",
#             "EloTeam": "",
#             "Ath1v1": "",
#             "AthTeam": "",
#             "Civs1v1": [
#                 { "Name": "Franks",
#                   "Matches": "23"
#                   "Wins": "1"
#                   "Rate": .5 },
#             ],
#             "CivsOp1v1": [],
#             "Maps1v1": []
#           },
#     ]
"""

import os
import sys
import json
import copy
import argparse
import logging
from datetime import datetime, date, timedelta
from difflib import SequenceMatcher

import requests
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from logging_setup import setup_logging
from config import TOORNAMENT_API, TOORNAMENT_ID, TOORNAMENT_NAME, A2GDRAFTS_API

# Disable warning about f-strings in logging
# pylint: disable=W1203

DATAFILE = f"{TOORNAMENT_NAME}/toornay.json"
PLAYERFILE = f"{TOORNAMENT_NAME}/players.json"

STAGE_ELEMENTS = ["id", "number", "name", "type", "status", "closed", "groups", "table"]
GROUP_ELEMENTS = ["id", "number", "name", "status", "closed"]
ROUND_ELEMENTS = ["id", "number", "name", "status", "closed", "matches"]
MATCH_ELEMENTS = ["id", "number", "opponents", "status", "playedAt", "meta"]
OPPONENT_ELMTS = ["id", "number", "position", "rank", "result", "forfeit", "score"]


# ------------------------------------------------------------------------------
def filter_dict(dictionary: dict, keep_keys: list) -> dict:
    return {key: dictionary[key] for key in dictionary if key in keep_keys}


# ------------------------------------------------------------------------------
def fetch_list_from_toornament(endpoint: str, params: str, initial_range: int) -> list:
    """
    Get a list from the toornament api
    """

    endpoint_url = f"{TOORNAMENT_API}{endpoint}{params}"
    list_data = []
    list_offset = 0
    # initial range will be ignored now
    # list_to = initial_range
    while True:
        headers = {
            "content-type": "application/json",
        }
        url = f"{endpoint_url}&offset={list_offset}&limit={50}"
        response = requests.get(url, headers=headers, timeout=5000)
        status = response.status_code
        if not status == 206 and not status == 200:
            logging.error(
                f"Got unexpected response code: {response.status_code} "
                f"{url} {headers}"
            )
            print()
            return []
        new_data = response.json()
        data_range = new_data['range']
        offset = data_range['offset']
        count = data_range['length']
        total = data_range['total']
        new_list = new_data['items']
        list_data.extend(new_list)
        logging.info(
            f"Requested {endpoint} from {offset} to {count} - got "
            f"{len(new_list)} from a total of {total} entries"
        )
        if offset + count < int(total):
            list_offset = offset + count
        else:
            break
    return list_data


# ------------------------------------------------------------------------------
def scrape_toornament() -> dict:
    """
    Go through the toornament page and get all the infos
    """
    logging.info("=============================")
    logging.info("Getting infos from toornament")
    logging.info("=============================")

    stages = fetch_list_from_toornament("stages", f"?tournament_ids={TOORNAMENT_ID}", 29)

    # meta_data = requests.get(LINK_TO_METADATA, timeout=5000).json()

    trny_data = {"id": TOORNAMENT_ID, "stages": []}
    for stage in stages:
        stage = filter_dict(stage, STAGE_ELEMENTS)
        logging.info(
            f"Checking stage [{stage['number']}] {stage['name']} with id {stage['id']}"
        )
        groups = fetch_list_from_toornament("groups", f"?stage_ids={stage['id']}", 49)
        stage["groups"] = []
        for group in groups:
            group = filter_dict(group, GROUP_ELEMENTS)
            logging.info(
                f"Checking group [{group['number']}] {group['name']} with id {group['id']}"
            )
            rounds = fetch_list_from_toornament(
                "rounds", f"?group_ids={group['id']}", 49
            )
            group["rounds"] = []

            table = {}
            table_entry = {"wins": 0, "losses": 0, "diff": 0, "pts": 0, "rounds": {}}
            for this_round in rounds:
                this_round = filter_dict(this_round, ROUND_ELEMENTS)
                logging.info(
                    f"Checking round [{this_round['number']}] "
                    f"{this_round['name']} with id {this_round['id']}"
                )
                matches = fetch_list_from_toornament(
                    "matches", f"?round_ids={this_round['id']}", 23
                )
                stripped_matches = []
                for match in matches:
                    match = filter_dict(match, MATCH_ELEMENTS)

                    opponent_one = match["opponents"][0]
                    if not opponent_one or not opponent_one["participant"]:
                        logging.warning(f"Opponent one missing in match number {match['number']}")
                        continue
                    opponent_one_id = opponent_one["participant"]["id"]
                    opponent_one_name = opponent_one["participant"]["name"]
                    opponent_one = filter_dict(opponent_one, OPPONENT_ELMTS)
                    opponent_one["id"] = opponent_one_id

                    opponent_two = match["opponents"][1]
                    if not opponent_two or not opponent_two["participant"]:
                        logging.warning(f"Opponent two missing in match number {match['number']}")
                        continue
                    opponent_two_id = opponent_two["participant"]["id"]
                    opponent_two_name = opponent_two["participant"]["name"]
                    opponent_two = filter_dict(opponent_two, OPPONENT_ELMTS)
                    opponent_two["id"] = opponent_two_id

                    logging.debug(
                        f"Match: {opponent_one_name} - {opponent_two_name} "
                        f"[{opponent_one['score']}:{opponent_two['score']}]"
                    )

                    match["opponents"] = [opponent_one, opponent_two]
                    # match["meta"] = (
                    #     meta_data[match["id"]] if match["id"] in meta_data else {}
                    # )
                    stripped_matches.append(match)
                    # if match["status"] != "completed":
                    #     continue
                    # Build table
                    # - find opponent one in table or create new
                    # - add match to rounds using current round data
                    # - find opponent two in table or create new
                    # - add match to rounds using current round data
                    opponent_one_score = (
                        opponent_one["score"] if opponent_one["score"] else 0
                    )
                    opponent_two_score = (
                        opponent_two["score"] if opponent_two["score"] else 0
                    )
                    table_entry_one = (
                        table[opponent_one_id]
                        if opponent_one_id in table
                        else copy.deepcopy(table_entry)
                    )
                    table_entry_one["wins"] = (
                        table_entry_one["wins"] + opponent_one_score
                    )
                    table_entry_one["losses"] = (
                        table_entry_one["losses"] + opponent_two_score
                    )
                    table_entry_one["rounds"][this_round["id"]] = {
                        "number": this_round["number"],
                        "opponent": opponent_two_id,
                        "result": [opponent_one_score, opponent_two_score],
                        "match": match["id"],
                    }
                    table[opponent_one_id] = table_entry_one
                    logging.debug(
                        f"Table Entry One: {opponent_one_name}:"
                        f"[{table_entry_one['wins']}:{table_entry_one['losses']}] "
                    )

                    table_entry_two = (
                        table[opponent_two_id]
                        if opponent_two_id in table
                        else copy.deepcopy(table_entry)
                    )
                    table_entry_two["wins"] = (
                        table_entry_two["wins"] + opponent_two_score
                    )
                    table_entry_two["losses"] = (
                        table_entry_two["losses"] + opponent_one_score
                    )
                    table_entry_two["rounds"][this_round["id"]] = {
                        "number": this_round["number"],
                        "opponent": opponent_one_id,
                        "result": [opponent_two_score, opponent_one_score],
                        "match": match["id"],
                    }
                    table[opponent_two_id] = table_entry_two
                    logging.debug(
                        f"Table Entry Two: {opponent_two_name}:"
                        f"[{table_entry_two['wins']}:{table_entry_two['losses']}] "
                    )

                this_round["matches"] = stripped_matches
                group["rounds"].append(this_round)

            # Buchholz
            for pid, player in table.items():
                pts = 0
                for this_round in player["rounds"].values():
                    if this_round["result"] == [0, 0]:
                        continue
                    pts += table[this_round["opponent"]]["wins"]
                player["pts"] = pts
                player["diff"] = player["wins"] - player["losses"]
                table[pid] = player
            sorted_table = sorted(
                table.items(), key=lambda x: (-x[1]["wins"], -x[1]["pts"])
            )
            stage["table"] = dict(sorted_table)
            stage["groups"].append(group)
            break
        trny_data["stages"].append(stage)

    print()
    return trny_data


# ------------------------------------------------------------------------------
def write_data(out_data):
    """Write the data to fie"""
    with open(DATAFILE, "w+", encoding="utf-8") as outfile:
        json.dump(out_data, outfile, indent=4)


# ------------------------------------------------------------------------------
def print_player(player: dict):
    """Print available data of a player"""
    if not player["Name"]:
        rprint(f"[bright_blue]{'noname':<30}", end="")
    else:
        rprint(f"[bright_blue]{player['Name']:<30}", end="")
    try:
        rprint(
            f"[bright_white]({player['Elo1v1']}/[dim]{player['Ath1v1']})",
            end=" ",
        )
        rprint(
            f"[yellow]({player['EloTeam']}/[dim]{player['AthTeam']})",
            end=" ",
        )
    except KeyError:
        rprint("[red]Elos", end=" ")

    if "Civs1v1" in player:
        rprint("[green]1v1", end=" ")
    else:
        rprint("[red]1v1", end=" ")

    if "CivsTeam" in player:
        rprint("[green]team", end=" ")
    else:
        rprint("[red]team", end=" ")

    if "Image" in player and player["Image"]:
        rprint("[green]icon", end=" ")
    else:
        rprint("[red]icon", end=" ")
    print("")


# ------------------------------------------------------------------------------
def print_table(which: int):
    """Print a table for each stage"""

    try:
        with open(DATAFILE, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        logging.error(f"Could not open toornay data file {DATAFILE}")
        data = {}

    try:
        with open(PLAYERFILE, "r", encoding="utf-8") as player_file:
            player_data = json.load(player_file)
    except FileNotFoundError:
        logging.error(f"Could not open player data file {PLAYERFILE}")
        player_data = []

    def get_player_name(player_id: str) -> str:
        for player in player_data:
            if player["LeagueID"] == player_id:
                return player["Name"]
        return player_id

    def rnd(rndobj: dict) -> str:
        name = get_player_name(str(rndobj["opponent"]))
        result = str(rndobj["result"])
        color = "[bright_black]"
        if rndobj["result"][0] == 2:
            color = "[green]"
        if rndobj["result"][0] == 0:
            color = "[red]"
        if rndobj["result"][0] == 0 and rndobj["result"][1] == 0:
            color = "[bright_cyan]"
        return f"{color}{name}\n{color}{result}"

    headers = [
        "Player",
        "W",
        "L",
        "D",
        "P",
        "Round 1",
        "Round 2",
        "Round 3",
        "Round 4",
        "Round 5",
    ]

    for stage in data["stages"]:
        table = Table(title=f"The table for {stage['name']}")
        for header in headers:
            table.add_column(header)

        if which not in (-1, stage["number"]):
            continue
        tab = stage["table"]
        logging.info("=====================================")
        logging.info(f"The table for {stage['name']}")
        logging.info("=====================================")
        # table = []
        for pid, stats in tab.items():
            entry = [
                get_player_name(pid),
                str(stats["wins"]),
                str(stats["losses"]),
                str(stats["diff"]),
                str(stats["pts"]),
            ]
            for _, rd in stats["rounds"].items():
                entry.append(rnd(rd))
            table.add_row(*entry)
        console = Console()
        console.print(table)

    print("")
# ------------------------------------------------------------------------------




# ------------------------------------------------------------------------------
def get_drafts() -> dict:
    """Try and get the drafts from the AoE2Germany dashboard"""

    try:
        with open(DATAFILE, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        logging.error(f"Could not open toornay data file {DATAFILE}")
        data = {}

    try:
        with open(PLAYERFILE, "r", encoding="utf-8") as player_file:
            player_data = json.load(player_file)
    except FileNotFoundError:
        logging.error(f"Could not open player data file {PLAYERFILE}")
        player_data = []

    items = []
    for page in range(0,50):
        response = requests.get(f"{A2GDRAFTS_API}{page}", timeout=5000)
        status = response.status_code
        if not status == 200:
            logging.error(
                f"Got unexpected response code: {response.status_code} "
                f"{A2GDRAFTS_API}"
            )
            print()
            return data
        response_data = response.json()
        if len(response_data["items"]) == 0:
            break
        items.extend(response_data["items"])


    # --------------------------------------------------------------------------
    def get_player_name(player_id: str) -> str:
        for player in player_data:
            if player["LeagueID"] == player_id:
                return player["Name"]
        return player_id


    # --------------------------------------------------------------------------
    def similarity(a: str, b: str) -> float:
        """Simple similarity score between 0 and 1."""
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


    # --------------------------------------------------------------------------
    def find_draft_ids(
        hostname: str,
        guestname: str,
        played_at: date | str,          # date object or "YYYY-MM-DD"
    ) -> dict:
        """
        Find Civs and Maps draftIds for a given host/guest + date.
        
        Returns:
            {
                "Civs": "draftId" or None,
                "Maps": "draftId" or None,
            }
        """
        threshold: float = 0.68

        # Normalize played_at to a date
        if isinstance(played_at, str):
            played_at = datetime.fromisoformat(played_at.replace("Z", "+00:00")).date()
        elif isinstance(played_at, datetime):
            played_at = played_at.date()

        candidates = []
        refused = []

        logging.info(f"Looking for {hostname} vs. "
                        f"{guestname} - {played_at}"
                    )

        for item in items:
            # Parse created timestamp
            created_dt = datetime.fromisoformat(item["created"].replace("Z", "+00:00"))
            created_date = created_dt.date()

            # Date filter (primary hint)
            date_score = 1.0
            if created_date != played_at:
                for day in range(1, 6):
                    date_score -= 0.1
                    next_day = created_date + timedelta(days=day)
                    if next_day == played_at:
                        break

            # Fuzzy name scores
            host_score = max(
                similarity(hostname, item["host"]),
                similarity(hostname, item["guest"])   # sometimes roles are swapped
            )
            guest_score = max(
                similarity(guestname, item["host"]),
                similarity(guestname, item["guest"])
            )

            # Combined score / ignoring date score for now
            combined = (host_score + guest_score + date_score) / 3

            candidate = {
                "item": item,
                "host_score": host_score,
                "guest_score": guest_score,
                "combined": combined,
                "created_dt": created_dt
            }

            if combined > threshold:
                candidates.append(candidate)
            else:
                refused.append(candidate)

        if not candidates:
            refused.sort(key=lambda c: (-c["combined"], c["created_dt"]))
            best = refused[0]
            logging.debug(f"Best refused candidate (score {best['combined']}): {best['item']}")
            return {"Civs": None, "Maps": None}

        # Sort by best name match, then by closest time
        candidates.sort(key=lambda c: (-c["combined"], c["created_dt"]))

        # Take the best matching pair of players
        best = candidates[0]
        best_host = best["item"]["host"]
        best_guest = best["item"]["guest"]
        best_date = best["created_dt"].date()

        # Now collect all drafts (Civs + Maps) for this exact host/guest + date
        result = {
            "Civs": None,
            "Maps": None,
        }

        for c in candidates:
            item = c["item"]
            if (item["host"] == best_host and
                item["guest"] == best_guest and
                c["created_dt"].date() == best_date):

                draft_type = item["draftTypeName"]
                if draft_type in ("Civs", "Maps"):
                    result[draft_type] = item["draftId"]

        return result

    for stage in data["stages"]:
        for group in stage["groups"]:
            for groupround in group["rounds"]:
                for match in groupround["matches"]:
                    if not match:
                        continue
                    if not match["status"] == "completed":
                        continue
                    host_name = get_player_name(match["opponents"][0]["id"])
                    guest_name = get_player_name(match["opponents"][1]["id"])
                    if "civs" in match["meta"] or "maps" in match["meta"]:
                        logging.info(f"Skipping match {host_name} vs. "
                                     f"{guest_name} - already has drafts"
                                    )
                        continue

                    played_at = match["playedAt"]
                    result = find_draft_ids(host_name, guest_name, played_at)
                        
                    if result["Civs"]:
                        match["meta"]["civs"] = result["Civs"]
                    if result["Maps"]:
                        match["meta"]["maps"] = result["Maps"]

                    if not result["Civs"] or not result["Maps"]:
                        logging.info(
                            f"Could not find drafts for {host_name} (vs) {guest_name}"
                            f" (maps:{result['Maps']} civs:{result['Civs']})"
                        )
                    else:
                        logging.info(
                            f"Added drafts for {host_name} (vs) {guest_name}"
                            f" (maps:{result['Maps']} civs:{result['Civs']})"
                        )
    print("")
    return data


# ------------------------------------------------------------------------------
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Commandline program to get a toornament tournament info",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
        --------------------------------
        Author: erik.miers+aoe2@gmail.com
        --------------------------------
        """,
    )

    # Debugging and Logging output
    arg_parser.add_argument(
        "--debug",
        action="store_true",
        help="Set logging output to DEBUG level",
    )

    # Log level
    arg_parser.add_argument(
        "--log-level",
        choices=["INFO", "DEBUG", "WARN"],
        default="INFO",
        help="Set logging level\n\n",
    )

    # Display the tables
    arg_parser.add_argument(
        "--table",
        nargs="?",  # Selecta a table
        const="-1",  # Show all tables
        default="0",  # Dont show table
        help="Print a table [N] - which table", 
    )

    # Display the tables
    arg_parser.add_argument(
        "--drafts",
        action="store_true",
        help="Try to find a draft link for the games",
    )

    args = arg_parser.parse_args()

    if args.debug:
        args.log_level = "DEBUG"
    setup_logging(args.log_level)

    show_table = int(args.table)
    if show_table:
        print_table(show_table)
        sys.exit(0)


    if args.drafts:
        draft_data = get_drafts()
        write_data(draft_data)
        sys.exit(0)



    toornay_data = scrape_toornament()
    if not os.path.isdir(TOORNAMENT_NAME):
        logging.info(f"Did not find directory {TOORNAMENT_NAME} - creating")
        os.makedirs(TOORNAMENT_NAME)
    write_data(toornay_data)
