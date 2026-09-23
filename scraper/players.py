# data = [
#           { "Name": "cap..",
#             "InsightsLink": "https://www.aoe2insights.com/user/4741867/",
#             "RelicID": "3756612",
#             "SteamID": "/steam/76561198098982166",
#             "Clan": "NooEl",
#             "LeagueID":"8582349206351200256",
#             "ToornamentProfile": "5246847275145707520"
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
import sys
import json
import re
import argparse
import logging
import requests
from requests import RequestException
from rich import print as rprint
from rich.prompt import Prompt

from logging_setup import setup_logging, print_name as _n
from logging_setup import select_menu
from config import TOORNAMENT_API, TOORNAMENT_ID, TOORNAMENT_NAME
from config import WORLDSEDGE_API
from config import STEAM_AVATARS, INSIGHTS_NOAVATAR

# Disable warning about f-strings in logging
# pylint: disable=W1203

PLAYERFILE = f"{TOORNAMENT_NAME}/players.json"


# ------------------------------------------------------------------------------
def check_name(ptpt: dict, names: list) -> bool:
    if not names:
        return True
    name = str(ptpt["Name"]).lower()
    for n in names:
        if n.lower() in name:
            return True
    return False


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def extract_insights_id(profile_string):
    """Extract the aoe2insights id from the profile strings"""
    if not profile_string:
        logging.warning("Empty profile string when extracting steam id")
        return ""
    pattern = r"Profil-Link:\s*(?:[h,H]ttps://www\.aoe2insights\.com/user/)?(\d+)"
    match = re.search(pattern, profile_string)
    if match:
        return match.group(1)
    logging.warning(f"Did not find ID in {profile_string}")
    return ""


# ------------------------------------------------------------------------------




# ------------------------------------------------------------------------------
def scrape_insights_one(data: list, names: list) -> list:
    """
    Go through the participants on aoe2insights and get their 1v1 stats
    """
    logging.info("===================================")
    logging.info("Getting 1v1 stats from aoe2insights")
    logging.info("===================================")

    # path_to_civ_tab = '//*[@id="app"]/div[3]/div/div/div/div/div/div[2]/div/'\
    #     'div[5]/div/div[1]/div/div/div/table/tbody'
    # path_to_civ_tab2 = '//*[@id="app"]/div[3]/div/div/div/div/div/div[2]/div/'\
    #     'div[5]/div/div[2]/div/div/div/table/tbody'
    # path_to_map_tab = '//*[@id="app"]/div[3]/div/div/div/div/div/div[2]/div/'\
    #     'div[6]/div/div[1]/div/table/tbody'
    # path_to_map_tab2 = '//*[@id="app"]/div[3]/div/div/div/div/div/div[2]/div/'\
    #     'div[6]/div/div[2]/div/table/tbody'

    # with sync_playwright() as playwirght:
    #     browser = playwirght.chromium.launch(
    #         timeout=20000, headless=True, handle_sigint=False, handle_sigterm=False
    #     )
    #     page = browser.new_page()

    #     # ----------------------------------------------------------------------
    #     def extract_player_data(player: dict):
    #         logging.info(f"Checking Player {player['Name']}{player['InsightsLink']}")
    #         if len(player["InsightsLink"]) <= 0:
    #             logging.warning(f"Skipping {player['Name']}, no InsightsLink")
    #             return

    #         page.set_default_timeout(10000)
    #         try:
    #             response = page.goto(player["InsightsLink"] + "stats/3")
    #         except PlaywrightError:
    #             logging.error(f"Could not navigate to {player['InsightsLink']}stats/3")
    #             return

    #         if response.status != 200:
    #             logging.error(f"Could not navigate to {player['InsightsLink']}stats/3")
    #             return

    #         try:
    #             page.wait_for_selector(path_to_civ_tab)
    #         except PlaywrightTimeoutError:
    #             logging.error("Could not find the civ tab")
    #             return

    #         civtab = page.query_selector_all(f"{path_to_civ_tab}//tr")
    #         one_civs = []
    #         for row in civtab:
    #             tdname = row.query_selector("//td[1]/strong")
    #             name = tdname.inner_text() if tdname else "None"
    #             tdmatches = row.query_selector("//td[2]/div")
    #             matches = tdmatches.inner_text() if tdname else "0"
    #             tdwins = row.query_selector("//td[3]/div")
    #             wins = tdwins.inner_text() if tdname else "0"
    #             tdrate = row.query_selector("//td[4]/strong")
    #             rate = tdrate.inner_text() if tdname else "0.0%"
    #             rate = float(rate[:-1])
    #             one_civs.append(
    #                 {"Name": name, "Matches": matches, "Wins": wins, "Rate": rate}
    #             )

    #         player["Civs1v1"] = one_civs
    #         civtab = page.query_selector_all(f"{path_to_civ_tab2}//tr")
    #         one_civs = []
    #         for row in civtab:
    #             tdname = row.query_selector("//td[1]/strong")
    #             name = tdname.inner_text() if tdname else "None"
    #             tdmatches = row.query_selector("//td[2]/div")
    #             matches = tdmatches.inner_text() if tdname else "0"
    #             tdwins = row.query_selector("//td[3]/div")
    #             wins = tdwins.inner_text() if tdname else "0"
    #             tdrate = row.query_selector("//td[4]/strong")
    #             rate = tdrate.inner_text() if tdname else "0.0%"
    #             rate = float(rate[:-1])
    #             one_civs.append(
    #                 {"Name": name, "Matches": matches, "Wins": wins, "Rate": rate}
    #             )

    #         player["CivsOp1v1"] = one_civs
    #         maptab = page.query_selector_all(f"{path_to_map_tab}//tr")
    #         one_maps = []
    #         for row in maptab:
    #             tdname = row.query_selector("//td[1]/strong")
    #             name = tdname.inner_text() if tdname else "None"
    #             tdmatches = row.query_selector("//td[2]/div")
    #             matches = tdmatches.inner_text() if tdname else "0"
    #             tdwins = row.query_selector("//td[3]/div")
    #             wins = tdwins.inner_text() if tdname else "0"
    #             tdrate = row.query_selector("//td[4]/strong")
    #             rate = tdrate.inner_text() if tdname else "0.0%"
    #             rate = float(rate[:-1])
    #             one_maps.append(
    #                 {"Name": name, "Matches": matches, "Wins": wins, "Rate": rate}
    #             )

    #         maptab = page.query_selector_all(f"{path_to_map_tab2}//tr")
    #         for row in maptab:
    #             tdname = row.query_selector("//td[1]/strong")
    #             name = tdname.inner_text() if tdname else "None"
    #             tdmatches = row.query_selector("//td[2]/div")
    #             matches = tdmatches.inner_text() if tdname else "0"
    #             tdwins = row.query_selector("//td[3]/div")
    #             wins = tdwins.inner_text() if tdname else "0"
    #             tdrate = row.query_selector("//td[4]/strong")
    #             rate = tdrate.inner_text() if tdname else "0.0%"
    #             rate = float(rate[:-1])
    #             one_maps.append(
    #                 {"Name": name, "Matches": matches, "Wins": wins, "Rate": rate}
    #             )

    #         player["Maps1v1"] = one_maps

    #     # ----------------------------------------------------------------------
    #     for participant in data:
    #         if not check_name(participant, names):
    #             continue

    #         if "Members" in participant:
    #             logging.info(f"Checking team {participant['Name']}")
    #             for member in participant["Members"]:
    #                 extract_player_data(member)
    #         else:
    #             extract_player_data(participant)

    #     page.close()
    #     print("")
    return data
# ------------------------------------------------------------------------------




# ------------------------------------------------------------------------------
def lookup_player_elos(data: list, names: list) -> list:
    """
    Go through the participants and update their elos
    """
    logging.info("===================================")
    logging.info("Getting player elos from worldsedge")
    logging.info("===================================")

    # --------------------------------------------------------------------------
    def calculate_team_elo(team: dict):
        """
        The formula for calculating the team elo might change from toornay to toornay
        """
        elos = []
        for member in team["Members"]:
            tourney_elo = (member["Elo1v1"] + member["Ath1v1"]) / 2
            elos.append(tourney_elo)
        elos.sort(reverse=True)
        highest = elos[0]
        second = elos[1]
        team_elo = (highest + second) / 2 + ((highest - second) / 100) * 20
        team["TeamElo"] = team_elo

    # --------------------------------------------------------------------------




    # ----------------------------------------------------------------------
    def fetch_elos(participant: dict):
        if 'RelicID' not in participant:
            logging.warning(f"Skipping {participant['Name']} - no relic id")
            return

        logging.info(
            f"Getting elos for {_n(participant['Name'])} "
            f"{participant['RelicID']}"
        )

        url = (
            f"{WORLDSEDGE_API}getPersonalStat?title=age2&"
            f"profile_ids=[{participant['RelicID']}]"
        )

        response = requests.get(url, timeout=20000)
        status = response.status_code
        if not status == 200:
            logging.error(f"Got unexpected response code: {response.status_code}")
            print(response)
            return
        data = response.json()
        if 'statGroups' not in data and 'members' not in data['statGroups'][0]:
            logging.warning(f"Did not find any members for alias {participant['Name']}")
            print(data)
            return

        member = data['statGroups'][0]['members'][0]
        participant['SteamID'] = member['name']
        participant['Clan'] = member['clanlist_name']
        participant['Statgroup'] = member['personal_statgroup_id']

        stats1v1, statsTeam = {}, {}
        for s in data['leaderboardStats']:
            if s['leaderboard_id'] == 3:
                stats1v1 = s
            elif s['leaderboard_id'] == 4:
                statsTeam = s

        participant['Elo1v1'] = stats1v1['rating'] if stats1v1 else ""
        participant['Ath1v1'] = stats1v1['highestrating'] if stats1v1 else ""
        participant['EloTeam'] = statsTeam['rating'] if statsTeam else ""
        participant['AthTeam'] = statsTeam['highestrating'] if statsTeam else ""
        print_player(participant)
    # ----------------------------------------------------------------------

    for participant in data:
        if not check_name(participant, names):
            continue

        if "Members" in participant:
            logging.info(f"Checking team {participant['Name']}")
            for member in participant["Members"]:
                fetch_elos(member)
            calculate_team_elo(participant)
        else:
            fetch_elos(participant)
    print("")
    return data
# ------------------------------------------------------------------------------




# ------------------------------------------------------------------------------
def scrape_insights_icons(data: list, names: list) -> list:
    """
    Go through the participants on aoe2insights and get their icons
    """
    logging.info("======================================")
    logging.info("Getting player icons from aoe2insights")
    logging.info("======================================")

    with sync_playwright() as playwirght:
        browser = playwirght.chromium.launch(
            timeout=20000, headless=True, handle_sigint=False, handle_sigterm=False
        )
        page = browser.new_page()

        current_img = {"url": ""}

        # ----------------------------------------------------------------------
        def handle_route(route: Route):
            if current_img["url"]:
                route.abort()
                return

            if ( route.request.resource_type == "image" and
                ( STEAM_AVATARS in route.request.url or
                 INSIGHTS_NOAVATAR in route.request.url ) ):
                current_img["url"] = route.request.url
                route.abort()
            else:
                route.continue_()

        # ----------------------------------------------------------------------
        page.route("**/*", handle_route)
        page.set_default_timeout(7000)

        # ----------------------------------------------------------------------
        def fetch_icons(participant: dict):
            logging.info(
                f"Getting icon for {_n(participant['Name'])} "
                f"{participant['InsightsLink']}"
            )
            if len(participant["InsightsLink"]) <= 0:
                logging.warning(f"Skipping {participant['Name']}, no InsightsLink")
                return
            base_url = participant["InsightsLink"]
            try:
                current_img["url"] = ""
                page.goto(base_url, wait_until="networkidle")
            except PlaywrightError as e:
                logging.warning(
                    f"PlaywrightError for link {participant['InsightsLink']} "
                    f"({e.name})"
                )

            img_link = current_img["url"].replace("_full", "")
            participant["Image"] = img_link
        # ----------------------------------------------------------------------

        for participant in data:
            if not check_name(participant, names):
                continue

            if "Members" in participant:
                logging.info(f"Checking team {participant['Name']}")
                for member in participant["Members"]:
                    fetch_icons(member)
            else:
                fetch_icons(participant)
        page.close()
        print("")
    return data
# ------------------------------------------------------------------------------




# ------------------------------------------------------------------------------
def icons_from_steamids(data: list, names: list) -> list:
    """
    Go through the participants and create an image link from the steamid
    """
    logging.info("===================================")
    logging.info("Creating player icons from steamIDs")
    logging.info("===================================")

    # ----------------------------------------------------------------------
    def make_icon_link(participant: dict):
        if 'SteamID' not in participant:
            logging.warning(f"Skipping {participant['Name']} - no steam id")
            return

        logging.info(f"Creating icon link for {_n(participant['Name'])} ")

        steam_id = participant["SteamID"].split("/")[-1]
        participant["Image"] = f"https://unavatar.io/steam/profile:{steam_id}"
    # ----------------------------------------------------------------------

    for participant in data:
        if not check_name(participant, names):
            continue

        if "Members" in participant:
            logging.info(f"Checking team {participant['Name']}")
            for member in participant["Members"]:
                make_icon_link(member)
        else:
            make_icon_link(participant)

    print("")
    return data
# ------------------------------------------------------------------------------




# ------------------------------------------------------------------------------
def lookup_player_ids(data: list, names: list) -> list:
    """
    Try to get the RelicIDs from the worldsedge api
    """
    logging.info("========================================")
    logging.info("Trying to get player ids from worldsedge")
    logging.info("========================================")

    worldsedge_url = (
        f"{WORLDSEDGE_API}getPersonalStat?title=age2&aliases"
    )

    def ask_custom_id(player: dict):
        player_id = Prompt.ask(f"Enter Relic-ID for {player['Name']}")
        if not player_id:
            return
        player['RelicID'] = player_id


    def lookup_player_id(player: dict):
        if 'RelicID' in player and player['RelicID']:
            logging.info(f"Player {player['Name']} already has an ID: {player['RelicID']} ...Skipping")
            return
        
        encoded_name = json.dumps([player["Name"]])
        url = f"{worldsedge_url}={encoded_name}"
        logging.info(f"Checking Player {player['Name']}")
        response = requests.get(url, timeout=20000)
        status = response.status_code
        if not status == 200:
            logging.error(f"Got unexpected response code: {response.status_code}")
            print(response)
            return
        data = response.json()
        member = {}
        if 'statGroups' in data and 'members' in data['statGroups'][0]:
            if len(data['statGroups']) > 1:
                logging.warning(f"Found multiple members for alias {player['Name']}"
                                f"\n{player['InsightsLink']}")
                entries = {"Skip":"skip", "Custom":"custom"}
                for group in data['statGroups']:
                    member = group['members'][0]
                    entry = f"{member['alias']} >> {member['profile_id']} [{member['country']}]"
                    entries[entry] = member
                    # print(f"{member['alias']} >> {member['profile_id']} [{member['country']}]")
                
                # ---------- Usage ----------
                choice = select_menu(entries, title=player['Name'])
                if choice == "skip":
                    return
                if choice == "custom":
                    ask_custom_id(player)
                    return
                member = choice
            else:
                member = data['statGroups'][0]['members'][0]
        else:
            logging.warning(f"Did not find any members for alias {player['Name']}"
                            f"\n{player['InsightsLink']}")
            logging.debug(data)
            ask_custom_id(player)
            return

        logging.info(f"Updating {player['Name']} / {member['alias']}")
        player['RelicID'] = member['profile_id']
        player['SteamID'] = member['name']
        player['Clan'] = member['clanlist_name']
        player['Statgroup'] = member['personal_statgroup_id']

        stats1v1, statsTeam = {}, {}
        for s in data['leaderboardStats']:
            if s['statgroup_id'] == player['Statgroup']:
                if s['leaderboard_id'] == 3:
                    stats1v1 = s
                elif s['leaderboard_id'] == 4:
                    statsTeam = s

        player['Elo1v1'] = stats1v1['rating'] if stats1v1 else ""
        player['Ath1v1'] = stats1v1['highestrating'] if stats1v1 else ""
        player['EloTeam'] = statsTeam['rating'] if statsTeam else ""
        player['AthTeam'] = statsTeam['highestrating'] if statsTeam else ""
        print_player(player)


    for participant in data:
        if not check_name(participant, names):
            continue

        if "Members" in participant:
            logging.info(f"Checking team {participant['Name']}")
            for member in participant["Members"]:
                lookup_player_id(member)
        else:
            lookup_player_id(participant)

    print()
    return data

# ------------------------------------------------------------------------------
def scrape_toornament(data: list) -> list:
    """
    Go through the participants on the toornament page and scrape their info
    """
    logging.info("====================================")
    logging.info("Getting player infos from toornament")
    logging.info("====================================")

    # ---------------------------------------------------------------------------
    def extract_player_data(player: dict) -> dict:
        logging.info(f"Checking player {_n(player['name'])}")
        playername = player["name"]
        if "id" in player.keys() and player["id"] is not None:
            leagueid = player["id"]
        else:
            logging.debug(f"{_n(player['name'])} has no league id")
            leagueid = ""
        if "playerUser" in player.keys() and player["playerUser"] is not None:
            toornamentprofile = player["playerUser"]["id"]
        else:
            logging.warning(f"{_n(player['name'])} has no toornament profile")
            toornamentprofile = ""
        if "customFieldValues" in player.keys():
            insightslink = player["customFieldValues"]["aoe2insights_profil_link"]
            if insightslink is None:
                logging.warning(f"{_n(player['name'])} has no aoeinsights profile link")
                insightslink = ""
            elif not insightslink.endswith("/"):
                insightslink += "/"
            if not insightslink.startswith("http"):
                insightslink = "https://" + insightslink
            if "aoe2insights" not in insightslink:
                try:
                    response = requests.head(insightslink, allow_redirects=True, timeout=5)
                    insightslink = response.url
                except RequestException as e:
                    logging.error(f"Error resolving URL {insightslink}: {e}")
        else:
            logging.warning(f"{_n(player['name'])} has no custom field values")
            insightslink = ""
        return {
            "Name": playername,
            "InsightsLink": insightslink,
            "LeagueID": leagueid,
            "ToornamentProfile": toornamentprofile,
        }

    # ---------------------------------------------------------------------------

    # ---------------------------------------------------------------------------
    def update_player_data(player: dict, data: list):
        player_item = next(
            (item for item in data if item["Name"] == player["Name"]), None
        )
        if not player_item:
            logging.info(
                f"Found new player {_n(player['Name'])} with Link "
                f"{player['InsightsLink']}"
            )
            data.append(player)
        else:
            logging.info(
                f"Found known player {_n(player['Name'])} with Link "
                f"{player['InsightsLink']} ... updating"
            )
            player_item["InsightsLink"] = player["InsightsLink"]
            player_item["LeagueID"] = player["LeagueID"]
            player_item["ToornamentProfile"] = player["ToornamentProfile"]

    # ---------------------------------------------------------------------------

    # ---------------------------------------------------------------------------
    def check_participants(participants_found: list, data: list):
        missing = [
            ptcpnt for ptcpnt in data if ptcpnt["Name"] not in participants_found
        ]
        for participant in missing:
            logging.info(f"Removing participant {_n(participant['Name'])}")
        data = [ptcpnt for ptcpnt in data if ptcpnt["Name"] in participants_found]

    # ---------------------------------------------------------------------------

    toornament_url = (
        f"{TOORNAMENT_API}participants?tournament_ids={TOORNAMENT_ID}&sort=alphabetic"
    )
    participants = []
    players_offset = 0
    while True:
        headers = {
            "content-type": "application/json",
        }
        url = f"{toornament_url}&offset={players_offset}&limit={50}"
        response = requests.get(url, headers=headers, timeout=20000)
        status = response.status_code
        if not status == 206 and not status == 200:
            logging.error(f"Got unexpected response code: {response.status_code}")
            print()
            return data
        new_data = response.json()
        data_range = new_data['range']
        offset = data_range['offset']
        count = data_range['length']
        total = data_range['total']
        new_participants = new_data['items']
        participants.extend(new_participants)
        logging.info(
            f"Requested players from {players_offset} to {offset + count} - got "
            f"{len(new_participants)} from a total of {total} players"
        )
        if offset + count < int(total):
            players_offset = offset + count
        else:
            break

    participants_found = []
    for participant in participants:

        # Teams
        if participant["type"] == "team":
            logging.info(f"Checking team {_n(participant['name'])}")
            team = next(
                (item for item in data if item["Name"] == participant["name"]), None
            )
            if not team:
                logging.info(f"Found new team {_n(participant['name'])}")
                team = {
                    "Name": participant["name"],
                    "LeagueID": participant["id"],
                    "Members": [],
                }
                data.append(team)
            else:
                logging.info(f"Found known team {_n(team['Name'])} updating ...")

            team_info = participant["team"]
            if team_info is not None:
                team["ToornamentProfile"] = team_info["id"]
            found_members = []
            for teammember in participant["lineup"]:
                player = extract_player_data(teammember)
                update_player_data(player, team["Members"])
                found_members.append(player["Name"])

            # Check for removed teammembers
            check_participants(found_members, team["Members"])
            participants_found.append(team["Name"])

        # Single players
        else:
            player = extract_player_data(participant)
            update_player_data(player, data)
            participants_found.append(player["Name"])

    # Check for missing participants
    check_participants(participants_found, data)

    print()
    return data


# ------------------------------------------------------------------------------
def write_data(out_data):
    """Write the data to fie"""
    with open(PLAYERFILE, "w+", encoding="utf-8") as outfile:
        json.dump(out_data, outfile, indent=4)


# ------------------------------------------------------------------------------
def print_player(player: object):
    """Print available data of a player"""
    if not player["Name"]:
        rprint(f"[bright_blue]{'noname':<30}", end="")
    else:
        rprint(f"[bright_blue]{player['Name']:<30}", end="")

    if 'RelicID' in player and player['RelicID']:
        rprint(f"🟢 [green]{player['RelicID']}", end=" ")
    else: 
        rprint("🔴 [red]ID", end=" ")

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


# ------------------------------------------------------------------------------
def print_participant(participant: object):
    """Print available data of a player"""

    if "Members" in participant:
        name = f"[{participant.get('Name', 'noname')}]"
        elo = participant.get("TeamElo", "noelo")
        rprint(f"\n[white] {name.ljust(40)} [bright_white]({elo})", end="\n")
        for member in participant["Members"]:
            print("\t", end="")
            print_player(member)
    else:
        print_player(participant)


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def print_list(data: list):
    """Print a list of available data"""
    rprint("\n\nCurrently registered participants")
    rprint("=====================================")

    if "Members" in data[0]:
        sorted_data = sorted(data, key=lambda p: int(p.get("TeamElo") or 0), reverse=True)
    else:
        sorted_data = sorted(data, key=lambda p: int(p.get("Elo1v1") or 0), reverse=True)
    for participant in sorted_data:
        print_participant(participant)
    print("")


# ------------------------------------------------------------------------------
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Commandline program to get player infos for a toornament tournament",
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

    arg_parser.add_argument(
        "--log-level",
        choices=["INFO", "DEBUG", "WARN"],
        default="INFO",
        help="Set logging level\n\n",
    )


    # Select individual scrapers
    arg_parser.add_argument(
        "--check",
        action="store_true",
        help="Update the player-list from toornament page",
    )

    arg_parser.add_argument(
        "--ids",
        action="store_true",
        help="Try and get the RelicId from the worldsedge API using the names",
    )

    arg_parser.add_argument(
        "--elos",
        action="store_true",
        help="Will use the relic API to update elos",
    )

    arg_parser.add_argument(
        "--icon",
        action="store_true",
        help="Will scrape the aoe2insights page for player icons",
    )

    arg_parser.add_argument(
        "--one",
        action="store_true",
        help="Will scrape the 1v1 stats on aoe2insights",
    )

    arg_parser.add_argument(
        "--team",
        action="store_true",
        help="Will scrape the teams stats on aoe2insights",
    )

    arg_parser.add_argument(
        "--all",
        action="store_true",
        help="Will run all the scrapers",
    )

    arg_parser.add_argument(
        "--names",
        nargs="+",
        help="Specify player/team names to update",
    )

    # Display a summary
    arg_parser.add_argument(
        "--list",
        action="store_true",
        help="List players",
    )

    args = arg_parser.parse_args()
    if not any([args.check, args.ids, args.elos, args.icon, args.team, args.one, args.all]):
        # args.all = True
        args.list = True

    if args.debug:
        args.log_level = "DEBUG"
    setup_logging(args.log_level)

    try:
        with open(PLAYERFILE, "r", encoding="utf-8") as json_file:
            player_data = json.load(json_file)
    except FileNotFoundError:
        player_data = []

    if args.list:
        print_list(player_data)
        sys.exit(0)

    # if args.new:
    #     new_data = scrapeToornament(team_data)
    #     teams_new = {team["Name"] for team in new_data}
    #     teams_old = {team["Name"] for team in team_data}
    #     new_teams = teams_new.symmetric_difference(teams_old)
    #     new_data = [team for team in new_data if team["Name"] in new_teams]
    if (args.check or args.all) and not args.names:
        player_data = scrape_toornament(player_data)
        write_data(player_data)


    if args.ids or args.all:
        player_data = lookup_player_ids(player_data, args.names)
        write_data(player_data)


    if args.elos or args.all:
        player_data = lookup_player_elos(player_data, args.names)
        write_data(player_data)

    if args.icon or args.all:
        player_data = icons_from_steamids(player_data, args.names)
        write_data(player_data)

    if args.one or args.all:
        player_data = scrape_insights_one(player_data, args.names)
        write_data(player_data)

    # if args.one or args.all:
    #     player_data = scrape_insights_team(player_data, args.names)
    #     write_data(player_data)
