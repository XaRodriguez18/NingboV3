def run_scraper():
    print("Running Daily scraper")
    try:
        main()
        print("Scraper completed")
    except Exception as e:
        print(f"Scraper failed {e}")

def main():
    import time
    import json
    import pandas as pd
    from datetime import datetime
    from config import ALLOWED_ELEMENT_TYPES, ICON_COLOR_MAP
    from utils import reformat_scraped_data
    from webdriver_manager.chrome import ChromeDriverManager
    import os
    import pytz

    print("[INFO] Initializing undetected-chromedriver...")
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        # Set a realistic user-agent
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        import sys
        import os
        print(f"[DEBUG] sys.platform: {sys.platform}")
        # Set Chrome binary location for Railway or Linux environments
        if sys.platform.startswith("linux"):
            # List all files in /usr/bin containing 'chrome' or 'chromium' for debugging
            try:
                bin_files = os.listdir("/usr/bin")
                print(f"[DEBUG] All files in /usr/bin: {bin_files}")
            except Exception as e:
                print(f"[DEBUG] Could not list /usr/bin: {e}")
            chrome_paths = ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"]
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    options.binary_location = chrome_path
                    print(f"[INFO] Using Chrome binary at: {chrome_path}")
                    break
            else:
                print("[ERROR] Chrome/Chromium not found in common locations. Please install Chrome or set the correct path.")
                return
        driver = uc.Chrome(options=options)
        print("[INFO] Chrome driver started successfully.")
    except Exception as e:
        print(f"[ERROR] Could not start undetected-chromedriver: {e}")
        return


    print("[INFO] Navigating to Forex Factory homepage...")
    driver.get("https://www.forexfactory.com/")
    print(f"[INFO] Current URL: {driver.current_url}")

    # --- Set Forex Factory timezone via UI ---
    import os
    import time as pytime
    TIMEZONE_DISPLAY = os.getenv("FF_TIMEZONE_DISPLAY", "Mountain Time")  # e.g., 'Mountain Time', 'GMT-7', etc.
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        print("[INFO] Waiting for timezone link...")
        tz_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="timezone"]'))
        )
        tz_link.click()
        print("[INFO] Timezone link clicked.")
        # Wait for the timezone selection page or modal to load
        pytime.sleep(2)
        # Find the timezone option by visible text and click it
        tz_options = driver.find_elements(By.XPATH, f"//*[contains(text(), '{TIMEZONE_DISPLAY}')]")
        found = False
        for option in tz_options:
            try:
                option.click()
                found = True
                print(f"[INFO] Selected timezone: {option.text}")
                break
            except Exception:
                continue
        if not found:
            print(f"[WARN] Could not find timezone '{TIMEZONE_DISPLAY}' in options. Using default.")
        # Look for a save or confirm button and click it if present
        try:
            save_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Save')] | //input[@type='submit' and @value='Save']")
            save_btn.click()
            print("[INFO] Clicked Save/Confirm for timezone.")
        except Exception:
            print("[INFO] No explicit Save button found, continuing.")
        # Wait for the calendar to reload
        pytime.sleep(2)
    except Exception as e:
        print(f"[WARN] Could not set timezone automatically: {e}")

    # Get local timezone from environment variable or default
    LOCAL_TZ = os.getenv("LOCAL_TZ", "Europe/London")
    local_tz = pytz.timezone(LOCAL_TZ)
    now_local = datetime.now(local_tz)
    today = now_local.strftime("%b %d")  # e.g., 'Sep 10'

    print("[INFO] Waiting for calendar table to load...")
    try:
        table = driver.find_element(By.CLASS_NAME, "calendar__table")
        print("[INFO] Calendar table found!")
    except Exception as e:
        print(f"[ERROR] Could not find calendar table: {e}")
        print("[DEBUG] Dumping page source snippet:")
        print(driver.page_source[:2000])
        driver.quit()
        return

    data = []
    previous_row_count = 0
    print("[INFO] Scrolling to the end of the page...")
    while True:
        before_scroll = driver.execute_script("return window.pageYOffset;")
        driver.execute_script("window.scrollTo(0, window.pageYOffset + 500);")
        time.sleep(2)
        after_scroll = driver.execute_script("return window.pageYOffset;")
        if before_scroll == after_scroll:
            print("[INFO] Reached end of page.")
            break

    print("[INFO] Collecting today's news from table...")
    for row in table.find_elements(By.TAG_NAME, "tr"):
        # Check if this row is for today
        date_cells = row.find_elements(By.CLASS_NAME, "calendar__date")
        is_today = False
        for date_cell in date_cells:
            if today in date_cell.text:
                is_today = True
                break
        if not is_today and date_cells:
            continue
        row_data = []
        for element in row.find_elements(By.TAG_NAME, "td"):
            class_name = element.get_attribute('class')
            if class_name in ALLOWED_ELEMENT_TYPES:
                if element.text:
                    row_data.append(element.text)
                elif "calendar__impact" in class_name:
                    impact_elements = element.find_elements(By.TAG_NAME, "span")
                    for impact in impact_elements:
                        impact_class = impact.get_attribute("class")
                        color = ICON_COLOR_MAP[impact_class]
                    if color:
                        row_data.append(color)
                    else:
                        row_data.append("impact")
        if len(row_data):
            data.append(row_data)
    print(f"[INFO] Scraped {len(data)} rows for today from the calendar table.")

    print("[INFO] Reformatting and saving scraped data...")
    # Use today's date for the CSV filename (in local time)
    today_str = now_local.strftime("%Y-%m-%d")
    reformat_scraped_data(data, today_str)
    print("[INFO] Scraping process completed.")
    driver.quit()

run_scraper()