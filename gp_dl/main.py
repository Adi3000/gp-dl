import os, time, argparse, re, sys, logging
from selenium.webdriver import Chrome, ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from zipfile import ZipFile

BANNER = """
██████   ██████         ██████  ██
██       ██   ██        ██   ██ ██
██   ███ ██████   █████ ██   ██ ██
██    ██ ██             ██   ██ ██
██████   ██             ██████  ███████

gp-dl — Google Photos Downloader
Download full-res albums using Selenium

Author: csd4ni3l  |  GitHub: https://github.com/csd4ni3l
"""

def parse_args():
    parser = argparse.ArgumentParser(description="Download full-res images from a Google Photos album using Selenium.")
    parser.add_argument("--album-urls", nargs="+", required=True, help="Google Photos album URL(s)")
    parser.add_argument("--output-dir", required=True, help="Directory to save downloaded albums")
    parser.add_argument("--driver-path", default=None, help="Custom Chrome driver path")
    parser.add_argument("--profile-dir", default=None, help="Chrome user data directory for session reuse")
    parser.add_argument("--headless", action="store_true", help="Run Chrome headlessly")
    return parser.parse_args()

def setup_driver(driver_path=None, profile_dir=None, headless=True):
    chrome_options = Options()
    if profile_dir:
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    if headless:
        chrome_options.add_argument("--headless")

    prefs = {
        "download.prompt_for_download": False,
        "download.default_directory": os.path.join(os.getcwd(), "gp_temp"),
        "profile.default_content_setting_values.automatic_downloads": 1
    }

    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    if driver_path:
        service = ChromeService(executable_path=driver_path)
        return Chrome(options=chrome_options, service=service)
    else:
        return Chrome(options=chrome_options)

def find_zip_file():
    for file in os.listdir("gp_temp"):
        if file.endswith(".zip"):
            return file

def find_crdownload_file():
    for file in os.listdir("gp_temp"):
        if file.endswith(".crdownload"):
            return file

def configure_logging():
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
    for logger_to_disable in ["selenium", "urllib3"]:
        logging.getLogger(logger_to_disable).propagate = False
        logging.getLogger(logger_to_disable).disabled = True

def main():
    args = parse_args()
    driver = setup_driver(profile_dir=args.profile_dir, headless=args.headless)

    if not os.path.exists("gp_temp") or not os.path.isdir("gp_temp"):
        logging.info("Creating gp_temp directory to temporarily store the downloaded zip files.")
        os.makedirs("gp_temp", exist_ok=True)

    if not os.path.exists(args.output_dir) or not os.path.isdir(args.output_dir):
        logging.fatal("Invalid output directory. Please supply a valid and existing directory.")
        return

    failed_album_count = 0
    successful_album_count = 0
    total_albums = len(args.album_urls)
    all_start = time.perf_counter()
    album_times = []

    for album_url in args.album_urls:
        album_start = time.perf_counter()

        if re.match(r'^https?://photos\.app\.goo\.gl/[A-Za-z0-9]+$', album_url) is None:
            logging.error(f"Invalid album URL: {album_url}")
            logging.info("Continuing with next album URL.")
            failed_album_count += 1
            continue

        logging.info(f"Now downloading {album_url}")

        driver.get(album_url)

        logging.debug("Waiting for menu button...")
        try:
            menu_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@aria-label="More options"]')))
        except TimeoutException:
            logging.error("Could not find more options button in time.")
            logging.info("Continuing with next album URL.")
            failed_album_count += 1
            continue

        logging.debug("Clicking menu button...")
        menu_button.click()

        logging.debug("Waiting for download all button...")
        try:
            download_all_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@aria-label="Download all"]')))
        except TimeoutException:
            logging.error("Could not find download all button in time.")
            logging.info("Continuing with next album.")
            failed_album_count += 1
            continue

        logging.debug("Clicking the download all button...")
        download_all_button.click()

        logging.info("Waiting for Google to prepare the file...")
        crdownload_file = None
        while not crdownload_file:
            crdownload_file = find_crdownload_file()
            time.sleep(0.1)

        logging.info("Waiting for the download to finish...")
        zip_file = None
        while not zip_file:
            zip_file = find_zip_file()
            time.sleep(0.1)

        logging.debug(f"Zip file downloaded, extracting to {args.output_dir}")

        with ZipFile(f"gp_temp/{zip_file}") as opened_file:
            opened_file.extractall(args.output_dir)

        logging.debug("Deleting zip file...")
        os.remove(f"gp_temp/{zip_file}")

        logging.info(f"Succesfully extracted zip file to {args.output_dir}")

        successful_album_count += 1
        album_times.append(time.perf_counter() - album_start)

    logging.debug("Removing temporary gp_temp directory.")
    os.removedirs("gp_temp")

    print("\n===== DOWNLOAD STATISTICS =====")
    print(f"Total albums given: {total_albums}")
    print(f"Successfully downloaded: {successful_album_count}")
    print(f"Failed downloads: {failed_album_count}")
    print(f"Average time taken per album: {sum(album_times) / len(album_times):.2f} seconds")
    print(f"Total time taken: {time.perf_counter() - all_start:.2f} seconds")
    print("================================")

    driver.quit()

def run_cli():
    print(BANNER)
    configure_logging()
    main()
