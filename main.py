import os, time, argparse, re
from selenium.webdriver import Chrome, ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from zipfile import ZipFile

def parse_args():
    parser = argparse.ArgumentParser(description="Download full-res images from a Google Photos album using Selenium.")
    parser.add_argument("--album-urls", nargs="+", required=True, help="Google Photos album URL")
    parser.add_argument("--output-dir", required=True, help="Directory to save downloaded images")
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

def main():
    args = parse_args()
    driver = setup_driver(profile_dir=args.profile_dir, headless=args.headless)

    os.makedirs("gp_temp", exist_ok=True)

    if not os.path.exists(args.output_dir) or not os.path.isdir(args.output_dir):
        print("ERROR: Invalid output directory.")
        return

    for album_url in args.album_urls:
        if re.match(r'^https?://photos\.app\.goo\.gl/[A-Za-z0-9]+$', album_url) is None:
            print(f"Invalid album URL: {album_url}")
            continue

        print(f"Opening {album_url}")

        driver.get(album_url)

        print("Waiting for menu button...")
        try:
            menu_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@aria-label="More options"]')))
        except TimeoutException:
            print("ERROR: Could not find more options button in time.")
            print("Continuing with next album.")
            continue

        print("Clicking menu button...")
        menu_button.click()

        print("Waiting for download all button...")
        try:
            download_all_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@aria-label="Download all"]')))
        except TimeoutException:
            print("ERROR: Could not find download all button in time.")
            print("Continuing with next album.")
            continue

        print("Clicking the download all button...")
        download_all_button.click()

        print("Waiting for a zip file to land in gp_temp...")
        zip_file = None
        while not zip_file:
            zip_file = find_zip_file()
            time.sleep(0.1)

        print(f"Zip file downloaded, extracting to {args.output_dir}")

        with ZipFile(f"gp_temp/{zip_file}") as opened_file:
            opened_file.extractall(args.output_dir)

        print("Deleting zip file...")
        os.remove(f"gp_temp/{zip_file}")

        print(f"Succesfully extracted to {args.output_dir}")

    os.removedirs("gp_temp")

    driver.quit()

if __name__ == '__main__':
    main()
