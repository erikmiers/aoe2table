"""
Calendar
"""
import json
import signal
import argparse
import logging
from datetime import date
from playwright.sync_api import sync_playwright

from logging_setup import setup_logging, print_name as _n
from config import TOORNAMENT_API, TOORNAMENT_ID, TOORNAMENT_NAME
from config import STEAM_AVATARS, INSIGHTS_NOAVATAR, INSIGHTS_ELO1V1, INSIGHTS_ELOTEAM

# Disable warning about f-strings in logging
# pylint: disable=W1203

DATAFILE = f"{TOORNAMENT_NAME}/calendar.json"

AOE2GCALENDAR = "https://aoe2germany.de/kalender"


# ------------------------------------------------------------------------------
def scrape_calendar(data: list) -> list:
    """
    Go through the aoe2g calendar and get the entries
    """
    logging.info("=============================")
    logging.info(" Getting calendar from aoe2g")
    logging.info("=============================")

    with sync_playwright() as playwirght:
        browser = playwirght.chromium.launch(
            timeout=20000,
            headless=True,
            handle_sigint=False,
            handle_sigterm=False)
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(AOE2GCALENDAR)

        entries = []
        current_date = date.today().isoformat()

        table_rows = page.locator("tbody tr")
        for i in range(table_rows.count()):
            cells = table_rows.nth(i).locator("td")
            if cells.count() == 1:
                date_text = cells.first.inner_text().split(" - ")[1]
                [day, month, year] = date_text.split('.')
                current_date = f"{year}-{month}-{day}"
                logging.info(f"Found new day: {current_date}")
                continue
            if cells.count() < 1:
                logging.warning(f"No cells found in row {i}")
                continue
            time = cells.nth(0).inner_text()
            stage = cells.nth(1).inner_text()
            stage_n = 0
            host =  cells.nth(2).inner_text()
            guest =  cells.nth(4).inner_text()
            logging.info(f"[{time}] {stage} {host} - {guest}")
            entries.append({"stage":stage,"number":stage_n,"date":current_date,
                            "time":time,"home":host,"away":guest})
        page.close()
        print("")
    return entries
# ------------------------------------------------------------------------------




# ------------------------------------------------------------------------------
def write_data(out_data):
    """ Write the data to fie """
    with open(DATAFILE, "w+", encoding="utf-8") as outfile:
        json.dump(out_data, outfile, indent=4)
# ------------------------------------------------------------------------------




# ------------------------------------------------------------------------------
def print_list(data: list):
    """ Print a list of available data """
    print("")


# ------------------------------------------------------------------------------
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description='Commandline program to get the calendar data from aoe2g',
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
    args = arg_parser.parse_args()

    if args.debug:
        args.log_level = "DEBUG"
    setup_logging(args.log_level)

    try:
        with open(DATAFILE, "r", encoding="utf-8") as json_file:
            cal_data = json.load(json_file)
    except FileNotFoundError:
        cal_data = []

    cal_data = scrape_calendar(cal_data)
    write_data(cal_data)
