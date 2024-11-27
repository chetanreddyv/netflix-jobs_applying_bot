from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
import time
import random
import logging
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def random_delay(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)
    return driver

def wait_for_element(driver, by, value, timeout=10, clickable=False):
    try:
        condition = EC.element_to_be_clickable((by, value)) if clickable else EC.presence_of_element_located((by, value))
        return WebDriverWait(driver, timeout).until(condition)
    except TimeoutException:
        logger.error(f"Element not found: {value}")
        return None

def click_with_retry(element, retries=3):
    for i in range(retries):
        try:
            element.click()
            return True
        except (ElementClickInterceptedException, ElementNotInteractableException):
            logger.warning(f"Click failed, attempt {i+1} of {retries}")
            random_delay()
    return False

def handle_dropdown(driver, dropdown_id, option_text):
    dropdown = wait_for_element(driver, By.ID, dropdown_id, clickable=True)
    if not dropdown or not click_with_retry(dropdown):
        return False
    random_delay()
    option_xpath = f"//button[@role='option' and contains(., '{option_text}')]"
    option = wait_for_element(driver, By.XPATH, option_xpath, clickable=True)
    return option and click_with_retry(option)

def handle_checkbox(driver, aria_label):
    checkbox = wait_for_element(driver, By.CSS_SELECTOR, f'input[aria-label="{aria_label}"]', clickable=True)
    if checkbox and checkbox.get_attribute("aria-checked") == "false":
        click_with_retry(checkbox)
        random_delay()

def click_acknowledge_button(driver):
    acknowledge_button = wait_for_element(driver, By.CSS_SELECTOR, 'button[data-test-id="confirm-upload-resume"]', clickable=True)
    return acknowledge_button and click_with_retry(acknowledge_button)

def upload_resume(driver, file_path):
    upload_button = wait_for_element(driver, By.ID, "resume-upload", clickable=True)
    if not upload_button or not click_with_retry(upload_button):
        logger.error("Failed to click upload button.")
        return False
    random_delay()
    select_file_button = wait_for_element(driver, By.CSS_SELECTOR, 'a[data-test-id="upload-resume-browse-button"]', clickable=True)
    if not select_file_button or not click_with_retry(select_file_button):
        logger.error("Failed to click select file button.")
        return False
    random_delay()
    file_input = wait_for_element(driver, By.CSS_SELECTOR, 'input[type="file"]', clickable=True)
    if file_input:
        logger.info(f"Uploading file: {file_path}")
        file_input.send_keys(file_path)
        random_delay()
        return click_acknowledge_button(driver)
    logger.error("File input element not found.")
    return False

def fill_form(driver, url):
    logger.info("Starting form fill...")
    driver.get(url)
    random_delay(5, 10)
    
    if not upload_resume(driver, os.getenv("Resume_Path")):
        logger.error("Failed to upload resume.")
        return False
    
    form_fields = {
        'input[aria-label="First Name"]': os.getenv("FIRST_NAME"),
        'input[aria-label="Last Name"]': os.getenv("LAST_NAME"),
        'input[aria-label="Phone Number"]': os.getenv("PHONE_NUMBER"),
        'input[data-testid="common-text-input-postion-apply-input-location"]': os.getenv("LOCATION"),
    }
    for selector, value in form_fields.items():
        element = wait_for_element(driver, By.CSS_SELECTOR, selector, clickable=True)
        if element:
            element.clear()
            element.send_keys(value)
            random_delay()
        else:
            logger.error(f"Failed to fill field: {selector}")
            return False
    
    dropdowns = {
        "1-1-additional-questions-dropdown": os.getenv("DROPDOWN_1_1"),
        "1-2-additional-questions-dropdown": os.getenv("DROPDOWN_1_2"),
        "2-0-additional-questions-dropdown": os.getenv("DROPDOWN_2_0"),
        "2-1-additional-questions-dropdown": os.getenv("DROPDOWN_2_1"),
        "2-2-additional-questions-dropdown": os.getenv("DROPDOWN_2_2")
    }
    for dropdown_id, option in dropdowns.items():
        dropdown = wait_for_element(driver, By.ID, dropdown_id, clickable=True)
        if dropdown:
            selected_option = dropdown.get_attribute('value')
            if selected_option != option:
                if not handle_dropdown(driver, dropdown_id, option):
                    logger.error(f"Failed to select option in dropdown: {dropdown_id}")
                    return False
            else:
                logger.info(f"Dropdown {dropdown_id} already has the desired option selected, skipping.")
        else:
            logger.error(f"Failed to find dropdown: {dropdown_id}")
            return False
    
    checkboxes = [
        os.getenv("CHECKBOX_1"),
        os.getenv("CHECKBOX_2"),
        os.getenv("CHECKBOX_3"),
        os.getenv("CHECKBOX_4")
    ]

    try:
        for aria_label in checkboxes:
            checkbox_element = driver.find_element(By.CSS_SELECTOR, f'i[aria-label="{aria_label}"]')
            if checkbox_element.get_attribute("aria-checked") == "false":
                driver.execute_script("arguments[0].click();", checkbox_element)

        logger.info("Checkboxes handled successfully.")
        random_delay()

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

    submit_button = wait_for_element(driver, By.XPATH, "//button[@data-test-id='position-apply-button']", clickable=True)
    if submit_button and click_with_retry(submit_button):
        logger.info("Form submitted successfully!")
        random_delay(5, 10)
        return True
    logger.error("Failed to click submit button.")
    return False

def main():
    driver = setup_driver()
    urls = [
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298013456&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298012330&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790299356302&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298013409&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298735290&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298553924&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298013511&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790299386198&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298012802&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298905761&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790299741083&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298013456&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298012330&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298013409&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298735290&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298553924&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298013497&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298735297&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298318863&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790299386198&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298905761&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790299741083&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298013456&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298553924&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298198373&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298014123&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790299379813&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298209736&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298318863&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790299807818&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298014663&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790298013522&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790299379813&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790299807818&domain=netflix.com&sort_by=relevance&utm_source=Netflix%20Careersite&show_multiple=false#apply",
        "https://explore.jobs.netflix.net/careers?query=data&pid=790299385411&domain=netflix.com&sort_by=relevance&triggerGoButton=false&utm_source=Netflix%20Careersite&show_multiple=false#apply"
    ]
    try:
        for url in urls:
            if not fill_form(driver, url):
                logger.error(f"Failed to fill form for URL: {url}")
            random_delay(5, 10)
    except Exception as e:
        logger.error(f"Main execution error: {str(e)}")
    finally:
        logger.info("Script completed. Browser will remain open for review.")
        time.sleep(100)

if __name__ == "__main__":
    main()



