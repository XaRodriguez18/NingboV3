def run_scraper():
    print("[SCRAPER.0 INFO] Running Daily scraper")
    try:
        main()
        print("[SCRAPER.0 INFO] Scraper completed")
    except Exception as e:
        print(f"[SCRAPER.0 INFO] Scraper failed {e}")

def main():
    import time as pytime
    from datetime import datetime
    from scraper.config import ALLOWED_ELEMENT_TYPES, ICON_COLOR_MAP
    from scraper.utils import reformat_scraped_data
    import os
    import pytz

    # STEP I - Initialize Chromedriver
    print("[SCRAPER.1 INFO] Initializing undetected-chromedriver...")
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

        # Set Chrome binary location for Railway or Linux environments
        import sys
        if sys.platform.startswith("linux"):
            chrome_paths = ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"]
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    options.binary_location = chrome_path
                    break
            else:
                print("[SCRAPER.1 ERROR] Chrome/Chromium not found in common locations. Please install Chrome or set the correct path.")
                return
        driver = uc.Chrome(options=options)
        print("[SCRAPER.1 INFO] Chrome driver started successfully.")
    except Exception as e:
        print(f"[SCRAPER.1 ERROR] Could not start undetected-chromedriver: {e}")
        return

    # STEP II - NAVIGATE TO FOREX FACTORY
    print("[SCRAPER.2 INFO] Navigating to Forex Factory homepage...")
    driver.get("https://www.forexfactory.com/")

    # Set Forex Factory timezone via UI
    timezone_display = os.getenv("FF_TIMEZONE_DISPLAY", "Mountain Time")  # e.g., 'Mountain Time', 'GMT-7', etc.
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as ec
        print("[SCRAPER.2 INFO] Waiting for timezone link...")
        tz_link = WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="timezone"]'))
        )
        tz_link.click()
        print("[SCRAPER.2 INFO] Timezone link clicked.")

        # Wait for the timezone selection page to load
        pytime.sleep(2)

        # Find the timezone option by visible text and click it
        tz_options = driver.find_elements(By.XPATH, f"//*[contains(text(), '{timezone_display}')]")
        found = False
        for option in tz_options:
            try:
                option.click()
                found = True
                print(f"[SCRAPER.2 INFO] Selected timezone: {option.text}")
                break
            except Exception:
                continue
        if not found:
            print(f"[SCRAPER.2 WARN] Could not find timezone '{timezone_display}' in options. Using default.")

        # Look for a save or confirm button and click it if present
        try:
            save_btn = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Save Settings']")
            save_btn.click()
            print("[SCRAPER.2 INFO] Clicked 'Save Settings' for timezone.")
        except Exception:
            print("[SCRAPER.2 INFO] No explicit 'Save Settings' button found, continuing.")

        # Wait for the calendar to reload
        pytime.sleep(2)
    except Exception as e:
        print(f"[SCRAPER.2 WARN] Could not set timezone automatically: {e}")

    # Get local timezone from environment variable or default
    env_tz = os.getenv("LOCAL_TZ", "Europe/London")
    local_tz = pytz.timezone(env_tz)
    now_local = datetime.now(local_tz)
    today = now_local.strftime("%b %d")  # e.g., 'Sep 10'

    # STEP III - SCRAPE CALENDAR
    # Find calendar
    print("[SCRAPER.3 INFO] Waiting for calendar table to load...")
    try:
        table = driver.find_element(By.CLASS_NAME, "calendar__table")
        print("[SCRAPER.3 INFO] Calendar table found!")
    except Exception as e:
        print(f"[SCRAPER.3 ERROR] Could not find calendar table: {e}")
        driver.quit()
        return

    # Scroll to end of page
    data = []
    print("[SCRAPER.3 INFO] Scrolling to the end of the page...")
    while True:
        before_scroll = driver.execute_script("return window.pageYOffset;")
        driver.execute_script("window.scrollTo(0, window.pageYOffset + 500);")
        pytime.sleep(2)
        after_scroll = driver.execute_script("return window.pageYOffset;")
        if before_scroll == after_scroll:
            print("[SCRAPER.3 INFO] Reached end of page.")
            break

    # Scrape table
    print("[SCRAPER.3 INFO] Collecting today's news from table...")
    from scraper.config import ALLOWED_CURRENCY_CODES, ALLOWED_IMPACT_COLORS
    stored_date = None
    last_time_val = None
    for row in table.find_elements(By.TAG_NAME, "tr"):
        date_cells = row.find_elements(By.CLASS_NAME, "calendar__date")
        if date_cells:
            for date_cell in date_cells:
                if date_cell.text:
                    stored_date = date_cell.text
                    print(f"[SCRAPER.3 DEBUG] Found date: {stored_date}")
                    break
        row_data = []
        currency = None
        impact_color = None
        time_val = None
        event_val = None
        for element in row.find_elements(By.TAG_NAME, "td"):
            class_name = element.get_attribute('class')
            if class_name in ALLOWED_ELEMENT_TYPES:
                if "calendar__time" in class_name:
                    if element.text:
                        time_val = element.text
                        last_time_val = time_val
                    else:
                        time_val = last_time_val
                elif "calendar__currency" in class_name and element.text:
                    currency = element.text
                elif "calendar__impact" in class_name:
                    impact_elements = element.find_elements(By.TAG_NAME, "span")
                    for impact in impact_elements:
                        impact_class = impact.get_attribute("class")
                        color = ICON_COLOR_MAP.get(impact_class)
                        if color:
                            impact_color = color
                elif "calendar__event" in class_name and element.text:
                    event_val = element.text
        # Only append if currency and impact_color are allowed
        if currency in ALLOWED_CURRENCY_CODES and impact_color in ALLOWED_IMPACT_COLORS:
            # Use stored_date for all rows
            row_data = [stored_date, time_val, currency, impact_color, event_val]
            print(f"[SCRAPER.3 DEBUG] Row accepted: {row_data}")
            data.append(row_data)
        else:
            print(f"[SCRAPER.3 DEBUG] Row rejected: currency={currency}, impact={impact_color}")
    print(f"[SCRAPER.3 INFO] Scraped {len(data)} rows for today from the calendar table.")

    # STEP IV - REFORMAT AND SAVE DATA
    print("[SCRAPER.4 INFO] Reformatting and saving scraped data...")
    # Use today's date for the CSV filename (in local time)
    today_str = now_local.strftime("%Y-%m-%d")
    reformat_scraped_data(data, today_str)
    print("[SCRAPER.4 INFO] Scraping process completed.")
    driver.quit()