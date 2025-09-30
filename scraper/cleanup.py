import os
from datetime import datetime

def delete_today_csv(news_dir="news"):
    """Delete today's news CSV file after use."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    file_string = today_str + '_news.csv'
    news_path = os.path.abspath(os.path.join(news_dir, file_string))
    if os.path.exists(news_path):
        try:
            os.remove(news_path)
            print(f"[CLEANUP] Deleted CSV: {news_path}")
        except Exception as e:
            print(f"[CLEANUP] Failed to delete CSV: {news_path} - {e}")
    else:
        print(f"[CLEANUP] No CSV found to delete: {news_path}")
