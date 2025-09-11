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
    from scraper.config import ALLOWED_ELEMENT_TYPES, ICON_COLOR_MAP
    from scraper.utils import reformat_scraped_data
    from webdriver_manager.chrome import ChromeDriverManager

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
        driver = uc.Chrome(options=options)
        print("[INFO] Chrome driver started successfully.")
    except Exception as e:
        print(f"[ERROR] Could not start undetected-chromedriver: {e}")
        return

    print("[INFO] Navigating to Forex Factory homepage...")
    driver.get("https://www.forexfactory.com/")
    print(f"[INFO] Current URL: {driver.current_url}")

    today = datetime.now().strftime("%b %d")  # e.g., 'Sep 10'

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
    # Use today's date for the CSV filename
    today_str = datetime.now().strftime("%Y-%m-%d")
    reformat_scraped_data(data, today_str)
    print("[INFO] Scraping process completed.")
    driver.quit()