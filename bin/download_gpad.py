"""
Download the GPAD suppliers data
"""

import argparse
import csv
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
import zipfile

from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
import requests

from gpad_helpers import (
    get_data_file_paths,
    get_main_system_from_value,
    get_month_and_year_from_iso_month,
)

BASE_GPAD_URL = "https://digital.nhs.uk/data-and-information/publications/statistical/appointments-in-general-practice"
EPRACCUR_URL = "https://www.odsdatasearchandexport.nhs.uk/api/getReport?report=epraccur"
OUTPUT_FILE = "data/gp_suppliers.csv"
EPRACCUR_TMP_FILE_PATH = "tmp/epraccur.csv"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main(month: str, zip_file: str = None):
    try:
        download_gpad_zip_file(month, zip_file)
    except Exception as e:
        logger.error(f"Error downloading zip file: {e}")
        raise e

    try:
        unzip_dir = unzip_gpad_zip_file(month)
    except Exception as e:
        logger.error(f"Error unzipping zip file: {e}")
        raise e

    input_file_paths = get_data_file_paths(unzip_dir, month)
    logger.info(f"Found {len(input_file_paths)} data files")

    try:
        data, gp_code_to_name = process_gpad_files(input_file_paths)
    except Exception as e:
        logger.error(f"Error processing data file: {e}")
        raise e

    try:
        download_epraccur_data()
    except Exception as e:
        logger.error(f"Error downloading EPRACCUR CSV: {e}")
        raise e

    try:
        gp_code_to_location = process_epraccur_data(EPRACCUR_TMP_FILE_PATH)
    except Exception as e:
        logger.error(f"Error processing EPRACCUR data: {e}")
        raise e

    try:
        write_output_file(data, gp_code_to_name, gp_code_to_location)
    except Exception as e:
        logger.error(f"Error writing output file: {e}")
        raise e

    try:
        remove_tmp_files(month)
    except Exception as e:
        logger.error(f"Error removing temporary files: {e}")
        raise e

    logger.info(f"Completed processing data for {month}")


def download_gpad_zip_file(iso_month: str, zip_file_path: str = None):
    """
    Download the GPAD suppliers zip data for a given month
    from the NHS Digital website
    """
    month, year = get_month_and_year_from_iso_month(iso_month)
    url = f"{BASE_GPAD_URL}/{month}-{year}"

    if zip_file_path is None:
        logger.info(f"Finding download link for {iso_month} from {url}")
        response = requests.get(url)
        response.raise_for_status()

        try:
            download_link = get_gpad_download_link_from_response(response)
        except Exception as e:
            raise Exception(f"Error getting download link: {e}")
    else:
        logger.info(
            f"Skipping finding download link and using provided zip file path: {zip_file_path}"
        )
        download_link = zip_file_path

    logger.info(f"Downloading zip file from {download_link}")
    response = requests.get(download_link)
    response.raise_for_status()

    with open(f"tmp/{iso_month}.zip", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
        f.write(response.content)

    logger.info(f"Downloaded zip file to tmp/{iso_month}.zip")


def get_gpad_download_link_from_response(response: requests.Response):
    soup = BeautifulSoup(response.content, "html.parser")
    downloads = soup.select("div.nhsd-m-download-card")

    for download in downloads:
        download_title = download.find("p").text
        if "Annex 1" in download_title and "CSV" in download_title:
            return download.find("a").get("href")

    if len(downloads) == 0:
        raise Exception("No downloads found.")
    else:
        raise Exception(
            f"Found {len(downloads)} downloads. No Annex 1 CSV downloads found."
        )


def unzip_gpad_zip_file(month: str):
    unzip_dir = f"tmp/{month}"
    if not os.path.exists(unzip_dir):
        os.makedirs(unzip_dir)
    with zipfile.ZipFile(f"tmp/{month}.zip", "r") as zip_ref:
        zip_ref.extractall(unzip_dir)

    logger.info(f"Unzipped zip file to {unzip_dir}")

    return unzip_dir


def process_gpad_files(input_file_paths: list[str]):
    data = {}
    gp_code_to_name = {}

    for input_file_path in input_file_paths:
        logger.info(f"Processing data file: {input_file_path}")
        with open(input_file_path, "r") as file:
            reader = csv.reader(file)
            for index, row in enumerate(reader):
                if index == 0:
                    continue

                gp_code = row[1]
                gp_name = row[2]

                appointments_systems = row[3]
                main_system = get_main_system_from_value(appointments_systems)

                if gp_code not in data:
                    data[gp_code] = (appointments_systems, main_system)

                if gp_code not in gp_code_to_name:
                    gp_code_to_name[gp_code] = gp_name

    # Sort the data alphabetically by GP code
    # to ensure the output file can be compared more easily over time
    data = dict(sorted(data.items()))

    return data, gp_code_to_name


def download_epraccur_data():
    response = requests.get(EPRACCUR_URL)
    response.raise_for_status()

    with open(EPRACCUR_TMP_FILE_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
        f.write(response.content)

    logger.info(f"Downloaded EPRACCUR data to {EPRACCUR_TMP_FILE_PATH}")


def process_epraccur_data(input_file_path: str):
    gp_code_to_location = {}

    with open(input_file_path, "r") as file:
        reader = csv.reader(file)
        # The file doesn't have a header row, so we don't need to skip the first row
        for row in reader:
            role_ids = row[25].split("|")
            if "RO76" not in role_ids:
                continue

            # Ignore practices with a close date
            if row[11].strip() != "":
                continue

            gp_code_to_location[row[0]] = {
                "postcode": row[9].strip(),
            }

    return gp_code_to_location


def write_output_file(data: dict, gp_code_to_name: dict, gp_code_to_location: dict):
    """
    Write the output file

    Args:
        data: A dictionary of GP codes to their appointment systems and main system
        gp_code_to_name: A dictionary of GP codes to their names
        gp_code_to_location: A dictionary of GP codes to their location data
    """
    with open(OUTPUT_FILE, "w") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["GP_ODS_CODE", "GP_NAME", "GP_POSTCODE", "GP_GPAD_SYSTEMS", "GP_SYSTEM"]
        )
        for gp_code, (appointment_systems, main_system) in data.items():
            try:
                postcode = gp_code_to_location[gp_code]["postcode"]
            except KeyError:
                postcode = None
                logger.warning(f"Postcode not found for GP code: {gp_code}")

            writer.writerow(
                [
                    gp_code,
                    gp_code_to_name[gp_code],
                    postcode,
                    appointment_systems,
                    main_system,
                ]
            )
    logger.info(f"Written output file: {OUTPUT_FILE}")


def remove_tmp_files(month: str):
    """
    Remove the temporary files for a given month for GPAD
    and the EPRACCUR CSV file
    """
    zip_file_path = f"tmp/{month}.zip"
    Path(zip_file_path).unlink()

    unzip_dir = f"tmp/{month}"
    shutil.rmtree(unzip_dir)

    Path(EPRACCUR_TMP_FILE_PATH).unlink()
    logger.info(f"Removed temporary files for {month} for GPAD and EPRACCUR")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download the Appointments in General Practice data"
    )

    parser.add_argument(
        "--month",
        type=str,
        help="The month to download the data for (e.g. 2025-01)",
    )

    parser.add_argument(
        "--zip-file",
        type=str,
        help="The path to the zip file to download",
        default=None,
        required=False,
    )

    args = parser.parse_args()

    # If no month is provided, use the previous month
    if args.month is None:
        args.month = (datetime.now() - relativedelta(months=1)).strftime("%Y-%m")

    main(args.month, args.zip_file)
