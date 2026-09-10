# data = [
#           { "Name": "cap..",
#             "InsightsLink": "https://www.aoe2insights.com/user/4741867/",
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
import signal
import requests
import argparse
import logging
from colorama import init as colorama_init, Fore, Style
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import Error as PlaywrightError

DATAFILE = "players.json"
TOORNAMEN_ID = "8544694639084077056"
TOORNAMENT_API = "https://play.toornament.com/api/"


colorama_init(autoreset=True)

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class LevelColoredFormatter(logging.Formatter):
    """Simple formatter that only colors the level name"""

    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.WHITE,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
    }

    def format(self, record):
        # Color the levelname according to its level
        record.colored_levelname = f"{self.COLORS.get(record.levelname, '')}"\
        f"{record.levelname}{Style.RESET_ALL}"

        # Use the parent class's format method with our custom format string
        return super().format(record)


# ------------------------------------------------------------------------------
def setup_logging(log_level):
    """
    Set up logging with the specified log level.
    
    Args:
        log_level (str): Desired logging level ('DEBUG', 'INFO', 'WARN')
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    # Configure logging
    formatter = LevelColoredFormatter(
        fmt = f'{Fore.GREEN}%(asctime)s{Style.RESET_ALL} [%(colored_levelname)s] %(message)s',
        datefmt = '%H:%M:%S'
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    logger.handlers.clear()
    logger.addHandler(console_handler)
    # logging.basicConfig(
    #     level=numeric_level,
    #     format=f'{Fore.GREEN}%(asctime)s{Style.RESET_ALL} [%(colored_levelname)s] %(message)s',
    #     datefmt='%H:%M:%S'
    # )

    # Set a higher logging level for urllib3
    logger = logging.getLogger('urllib3')
    logger.setLevel(logging.WARNING)



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
def scrape_insights_one(data: list, names: list) -> list:
    """
    Go through the participants on aoe2insights and get their 1v1 stats
    """
    logging.info("===================================")
    logging.info("Getting 1v1 stats from aoe2insights")
    logging.info("===================================")

    path_to_civ_tab = ('//*[@id="app"]/div[4]/div/div/div/div/div/div[2]/div/div[5]/div/div[1]/div/div/div/table/tbody')
    path_to_civ_tab2 = ('//*[@id="app"]/div[4]/div/div/div/div/div/div[2]/div/div[5]/div/div[2]/div/div/div/table/tbody')
    path_to_map_tab = ('//*[@id="app"]/div[4]/div/div/div/div/div/div[2]/div/div[6]/div/div[1]/div/table/tbody')
    path_to_map_tab2 = ('//*[@id="app"]/div[4]/div/div/div/div/div/div[2]/div/div[6]/div/div[2]/div/table/tbody')

    with sync_playwright() as playwirght:
        browser = playwirght.chromium.launch(
            timeout=20000,
            headless=True,
            handle_sigint=False,
            handle_sigterm=False)
        page = browser.new_page()
        for player in data:
            logging.info(f"Checking Player {player['Name']}({player['InsightsLink']})")
            if len(player['InsightsLink']) <= 0:
                logging.warning(f"Skipping {player['Name']}, no InsightsLink")
                continue
            page.set_default_timeout(10000)
            try:
                response = page.goto(player['InsightsLink'] + "stats/3")
            except PlaywrightError:
                logging.error(f"Could not navigate to {player['InsightsLink']}stats/3")
                continue
            if response.status != 200:
                logging.error(f"Could not navigate to {player['InsightsLink']}stats/3")
                continue

            try:
                page.wait_for_selector(path_to_civ_tab)
            except PlaywrightTimeoutError:
                logging.error("Could not find the civ tab")
                continue
            civtab = page.query_selector_all(f'{path_to_civ_tab}//tr')
            one_civs = []
            for row in civtab:
                tdname = row.query_selector('//td[1]/strong')
                name = tdname.inner_text() if tdname else "None"
                tdmatches = row.query_selector('//td[2]/div')
                matches = tdmatches.inner_text() if tdname else "0"
                tdwins = row.query_selector('//td[3]/div')
                wins = tdwins.inner_text() if tdname else "0"
                tdrate = row.query_selector('//td[4]/strong')
                rate = tdrate.inner_text() if tdname else "0.0%"
                rate = float(rate[:-1])
                one_civs.append({"Name":name, "Matches":matches, "Wins":wins, "Rate":rate})
            player["Civs1v1"] = one_civs
            civtab = page.query_selector_all(f'{path_to_civ_tab2}//tr')
            one_civs = []
            for row in civtab:
                tdname = row.query_selector('//td[1]/strong')
                name = tdname.inner_text() if tdname else "None"
                tdmatches = row.query_selector('//td[2]/div')
                matches = tdmatches.inner_text() if tdname else "0"
                tdwins = row.query_selector('//td[3]/div')
                wins = tdwins.inner_text() if tdname else "0"
                tdrate = row.query_selector('//td[4]/strong')
                rate = tdrate.inner_text() if tdname else "0.0%"
                rate = float(rate[:-1])
                one_civs.append({"Name":name, "Matches":matches, "Wins":wins, "Rate":rate})
            player["CivsOp1v1"] = one_civs
            maptab = page.query_selector_all(f'{path_to_map_tab}//tr')
            one_maps = []
            for row in maptab:
                tdname = row.query_selector('//td[1]/strong')
                name = tdname.inner_text() if tdname else "None"
                tdmatches = row.query_selector('//td[2]/div')
                matches = tdmatches.inner_text() if tdname else "0"
                tdwins = row.query_selector('//td[3]/div')
                wins = tdwins.inner_text() if tdname else "0"
                tdrate = row.query_selector('//td[4]/strong')
                rate = tdrate.inner_text() if tdname else "0.0%"
                rate = float(rate[:-1])
                one_maps.append({"Name":name, "Matches":matches, "Wins":wins, "Rate":rate})
            maptab = page.query_selector_all(f'{path_to_map_tab2}//tr')
            for row in maptab:
                tdname = row.query_selector('//td[1]/strong')
                name = tdname.inner_text() if tdname else "None"
                tdmatches = row.query_selector('//td[2]/div')
                matches = tdmatches.inner_text() if tdname else "0"
                tdwins = row.query_selector('//td[3]/div')
                wins = tdwins.inner_text() if tdname else "0"
                tdrate = row.query_selector('//td[4]/strong')
                rate = tdrate.inner_text() if tdname else "0.0%"
                rate = float(rate[:-1])
                one_maps.append({"Name":name, "Matches":matches, "Wins":wins, "Rate":rate})
            player["Maps1v1"] = one_maps
        page.close()
        print("")
    return data


# ------------------------------------------------------------------------------
def scrape_insights(data: list, names: list) -> list:
    """
    Go through the participants on aoe2insights and get their stats
    """
    logging.info("======================================")
    logging.info("Getting player infos from aoe2insights")
    logging.info("======================================")

    path_to_elo1v1 = ('/*[@id="app"]/div[4]/div/div/div/div/div/div[2]/div[1]/'
                      'div[2]/div[1]/div/div/div/div[2]/small')
    path_to_ath1v1 = ('/*[@id="app"]/div[4]/div/div/div/div/div/div[2]/div[1]/'
                      'div[2]/div[1]/div/div/div/div[3]/small/i')
    path_to_eloteam = ('/*[@id="app"]/div[4]/div/div/div/div/div/div[2]/div[1]/'
                       'div[2]/div[2]/div/div/div/div[2]/small')
    path_to_athteam = ('/*[@id="app"]/div[4]/div/div/div/div/div/div[2]/div[1]/'
                       'div[2]/div[2]/div/div/div/div[3]/small/i')
    path_to_image = ('//*[@id="app"]/div[4]/div/div/div/div/div/div[1]/div/'
                     'div[1]/div[1]/img')
    network_responses = {
        'team_elos' : {},
        'onev_elos' : {}
    }

    #---------------------------------------------------------------------------
    def handle_response(response):
        if "elo-history/4" in response.url:
            try:
                network_responses['team_elos'] = json.loads(response.body())
            except json.decoder.JSONDecodeError:
                logging.warning("Could not parse the team_ elos")
        if "elo-history/3" in response.url:
            try:
                network_responses['onev_elos'] = json.loads(response.body())
            except json.decoder.JSONDecodeError:
                logging.warning("Could not parse the onev_ elos")

    #---------------------------------------------------------------------------
    def get_elos(elos):
        """ Unpack the elo list """
        current = 0
        high = 0
        for elo in elos.values():
            current = int(elo)
            high = max(high, current)
        return (current, high)

    #---------------------------------------------------------------------------
    with sync_playwright() as playwirght:
        browser = playwirght.chromium.launch(
            timeout=20000,
            headless=True,
            handle_sigint=False,
            handle_sigterm=False)
        page = browser.new_page()
        for player in data:
            logging.info(f"Checking Player {player['Name']}({player['InsightsLink']})")
            if len(player['InsightsLink']) <= 0:
                logging.warning(f"Skipping {player['Name']}, no InsightsLink")
                continue
            page.set_default_timeout(10000)
            page.on("response", handle_response)
            try:
                response = page.goto(player['InsightsLink'])
            except PlaywrightError:
                logging.error(f"Could not navigate to {player['InsightsLink']}")
                continue
            if response.status != 200:
                logging.error(f"Could not navigate to {player['InsightsLink']}")
                continue
            page.wait_for_selector(path_to_image)
            page.set_default_timeout(1000)
            try:
                elo1v1 = page.locator('xpath=/' + path_to_elo1v1).inner_text()
                elo1v1 = elo1v1.split(' ')[1]
            except PlaywrightTimeoutError:
                elo1v1 = 0
            try:
                ath1v1 = page.locator('xpath=/' + path_to_ath1v1).inner_text()
                ath1v1 = ath1v1.split(": ")[1]
            except PlaywrightTimeoutError:
                ath1v1 = 0
            try:
                eloteam = page.locator('xpath=/' + path_to_eloteam).inner_text()
                eloteam = eloteam.split(" ")[1]
            except PlaywrightTimeoutError:
                eloteam = 0
            try:
                athteam = page.locator('xpath=/' + path_to_athteam).inner_text()
                athteam = athteam.split(': ')[1]
            except PlaywrightTimeoutError:
                athteam = 0
            img = page.query_selector(path_to_image)
            img_link = img.get_attribute('src') if img else ""
            img_link = img_link.replace("_full", "")
            (onev_elo, onev_ath) = get_elos(network_responses['onev_elos'])
            (team_elo, team_ath) = get_elos(network_responses['team_elos'])
            player["Image"] = img_link
            player["Elo1v1"] = onev_elo if elo1v1 == 0 else elo1v1
            player["Ath1v1"] = onev_ath if ath1v1 == 0 else ath1v1
            player["EloTeam"] = team_elo if eloteam == 0 else eloteam
            player["AthTeam"] = team_ath if athteam == 0 else athteam
        page.close()
        print("")
    return data


# ------------------------------------------------------------------------------
def scrape_toornament(data: list) -> list:
    """
    Go through the participants on the toornament page and scrape their info
    """
    logging.info("====================================")
    logging.info("Getting player infos from toornament")
    logging.info("====================================")

    toornament_url = f"{TOORNAMENT_API}participants?tournament_ids={TOORNAMEN_ID}&sort=alphabetic"
    participants = []
    players_from = 0
    players_to = 47
    while True:
        headers = { 
            'content-type':'application/json',
            'Range':f"participants={players_from}-{players_to}"
            }
        response = requests.get(toornament_url, headers=headers)
        status = response.status_code
        if not status == 206 or status == 200:
            logging.error(f"Got unexpected response code: {response.status_code}")
            print()
            return data
        _, count = response.headers["Content-Range"].split('/')
        new_participants = response.json()
        participants.extend(new_participants)
        logging.info(f"Requested players from {players_from} to {players_to} - got {len(new_participants)} from a total of {count} players")
        if len(participants) < int(count):
            players_from = players_to + 1
            players_to = players_to + 48
        else:
            break

    players_found = []
    for player in participants:
        logging.info(f"Checking {player['name']}")
        playername = player["name"]
        leagueid = player["id"]
        if "playerUser" in player.keys() and player["playerUser"] is not None:
            toornamentprofile = player["playerUser"]["id"]
        else:
            logging.warning(f"{player['name']} has no toornament profile")
            toornamentprofile = ""
        if "customFieldValues" in player.keys():
            insightslink = player["customFieldValues"]["aoe2insights_profil_link"]
            if insightslink is None:
                logging.warning(f"{player['name']} has no aoeinsights profile link")
                insightslink = ""
            elif not insightslink.endswith('/'):
                insightslink += "/"
        else:
            logging.warning(f"{player['name']} has no custom field values")
            insightslink = ""
        member = {
            "Name": playername,
            "InsightsLink": insightslink,
            "LeagueID":leagueid,
            "ToornamentProfile":toornamentprofile
            }
        player_item = next((item for item in data if item["Name"] == member["Name"]), None)
        if not player_item:
            logging.info(f"Found new player {playername} with Link {insightslink}")
            data.append(member)
        else:
            logging.info(f"Found known player {playername} with Link {insightslink} ... updating")
            player_item["InsightsLink"] = member["InsightsLink"]
            player_item["LeagueID"] = member["LeagueID"]
            player_item["ToornamentProfile"] = member["ToornamentProfile"]
        players_found.append(playername)
    # Check for missing players
    players_missing = [player for player in data if player["Name"] not in players_found]
    for player in players_missing:
        logging.info(f"Removing player {player['Name']}")
    data = [player for player in data if player["Name"] in players_found]

    print()
    return data


# ------------------------------------------------------------------------------
def write_data(out_data):
    """ Write the data to fie """
    with open(DATAFILE, "w", encoding="utf-8") as outfile:
        json.dump(out_data, outfile, indent=4)



# ------------------------------------------------------------------------------
def print_player(player: object):
    """ Print available data of a player"""
    # print(Fore.CYAN + "\n["+team["Name"]+"]", end=" ")
    # for member in team["Members"]:
    print(f"{Fore.LIGHTBLUE_EX}{player['Name']:<20}", end="")
    try:
        print(f"{Fore.WHITE}({player['Elo1v1']}/{Style.DIM}{player['Ath1v1']}{Style.NORMAL})", end=" ")
        print(f"{Fore.YELLOW}({player['EloTeam']}/{Style.DIM}{player['AthTeam']}{Style.NORMAL})", end=" ")
    except KeyError:
        print(Fore.RED+"Elo[X]", end=" ")
    if "Civs1v1" in player:
        print(Fore.GREEN + "1v1[✅]", end=" ")
    else:
        print(Fore.RED + "1v1[X]", end=" ")
    print("")



# ------------------------------------------------------------------------------
def print_list(data: list):
    """ Print a list of available data """
    print("\n\nCurrently registered players")
    print("============================")

    sorted_data = sorted(data, key=lambda p: int(p.get("Elo1v1", 0)), reverse=True)
    for player in sorted_data:
        print_player(player)
    print("")


# ------------------------------------------------------------------------------
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description='Commandline program to get player infos for a toornament tournament',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
        --------------------------------
        Author: erik.miers+aoe2@gmail.com
        --------------------------------
        """
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
        "--elos",
        action="store_true",
        help="Will scrape the aoe2insights page for elos",
    )
    arg_parser.add_argument(
        "--one",
        action="store_true",
        help="Will scrape the 1v1 stats on aoe2insights",
    )
    arg_parser.add_argument(
        "--all",
        action="store_true",
        help="Will run all the scrapers",
    )
    arg_parser.add_argument(
        "--names",
        nargs="+",
        help="Specify player names to update",
    )

    # Display a summary
    arg_parser.add_argument(
        "--list",
        action="store_true",
        help="List players",
    )
    args = arg_parser.parse_args()
    if not any([args.check, args.elos, args.one, args.all]):
        # args.all = True
        args.list = True

    if args.debug:
        args.log_level = "DEBUG"
    setup_logging(args.log_level)


    #---------------------------------------------------------------------------
    class Terminator:
        """ Helper to terminate long running tasks """
        interruption_requested = False

        def __init__(self):
            signal.signal(signal.SIGINT, self.terminate)  # CTRL-C
            signal.signal(signal.SIGTERM, self.terminate)  # kill

        def terminate(self, *_):
            """ The terminat gunction """
            self.interruption_requested = True


    try:
        with open(DATAFILE, "r", encoding="utf-8") as json_file:
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

    if args.elos or args.all:
        player_data = scrape_insights(player_data, args.names)
        write_data(player_data)

    if args.one or args.all:
        player_data = scrape_insights_one(player_data, args.names)
        write_data(player_data)

    # data = scrapeGG(data)
