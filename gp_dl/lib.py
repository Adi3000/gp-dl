from selenium.webdriver import Chrome, ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from zipfile import ZipFile
import os, time, logging

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
        
def download_albums(
    album_urls: list[str],
    output_dir: str,
    driver_path: str | None = None,
    profile_dir: str | None = None,
    headless: bool = False,
) -> tuple[list[str], list[str], list[float]]:
    """
    1) Download full-resolution images from one or more Google Photos albums using Selenium.

    2) Return lists of successful and failed album names, as well as download durations.

    :type album_urls: list[str]
    :param album_urls: One or more Google Photos album URLs to download images from.

    :type output_dir: str
    :param output_dir: Directory path where the downloaded albums will be saved.

    :type driver_path: str | None
    :param driver_path: Path to a custom Chrome WebDriver binary. If None, Selenium will download it or choose the default system ChromeDriver.

    :type profile_dir: str | None
    :param profile_dir: Path to a Chrome user data directory. Use this to access private albums (non-shared links).

    :type headless: bool
    :param headless: Whether to run Chrome in headless mode. Defaults to False.

    :returns: A tuple containing the names of the successful albums, names of the albums that failed to download, and the durations it took to download each album.
    :rtype: tuple[list[str], list[str], list[float]]
    """

    driver = setup_driver(driver_path=driver_path, profile_dir=profile_dir, headless=headless)

    if not os.path.exists("gp_temp") or not os.path.isdir("gp_temp"):
        logging.info("Creating gp_temp directory to temporarily store the downloaded zip files.")
        os.makedirs("gp_temp", exist_ok=True)

    if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
        logging.fatal("Invalid output directory. Please supply a valid and existing directory.")
        return

    failed_albums = []
    successful_albums = []
    album_times = []

    for album_url in album_urls:
        album_start = time.perf_counter()

        driver.get(album_url)

        album_title = driver.title.split(" -")[0]

        logging.info(f"Now downloading {album_title} ({album_url})")

        logging.debug("Waiting for menu button...")
        try:
            menu_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@aria-label="More options"]')))
        except TimeoutException:
            logging.error("Could not find the 'more options' button in time.")
            logging.info("Continuing with next album URL.")
            failed_albums.append(album_title)
            continue

        logging.debug("Clicking menu button...")
        menu_button.click()

        logging.debug("Waiting for download all button...")
        try:
            download_all_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@aria-label="Download all"]')))
        except TimeoutException:
            logging.error("Could not find the 'download all' button in time.")
            logging.info("Continuing with next album.")
            failed_albums.append(album_title)
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

        logging.debug(f"Zip file downloaded, extracting to {output_dir}")

        with ZipFile(f"gp_temp/{zip_file}") as opened_file:
            opened_file.extractall(output_dir)

        logging.debug("Deleting zip file...")
        os.remove(f"gp_temp/{zip_file}")

        logging.info(f"Succesfully extracted zip file to {output_dir}")

        successful_albums.append(album_title)
        album_times.append(time.perf_counter() - album_start)
    
        logging.debug("Removing temporary gp_temp directory.")
        os.removedirs("gp_temp")

    driver.quit()

    return successful_albums, failed_albums, album_times