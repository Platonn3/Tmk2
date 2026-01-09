import os
import time
import re
import requests
from urllib.parse import urlparse
from fake_useragent import UserAgent

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class Downloader:
    def __init__(self, save_dir="../data_sources"):
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        self.ua = UserAgent()

    def _sanitize_filename(self, title):
        return re.sub(r'[\\/*?:"<>|]', "", title)[:150] + ".pdf"

    def _download_stream(self, url, filename, cookies=None, referer=None):
        headers = {'User-Agent': self.ua.random}
        if referer:
            headers['Referer'] = referer

        print(f"Начало загрузки: {url}")
        try:
            with requests.get(url, stream=True, headers=headers, cookies=cookies, timeout=30) as r:
                r.raise_for_status()
                content_type = r.headers.get('content-type', '').lower()
                if 'pdf' not in content_type and 'octet-stream' not in content_type:
                    print(f"Внимание: Тип содержимого '{content_type}', возможно это не PDF.")

                filepath = os.path.join(self.save_dir, filename)
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Файл успешно сохранен: {filepath}")
            return True
        except Exception as e:
            print(f"Ошибка при скачивании файла: {e}")
            return False

    def try_selenium(self, url):
        print("\n[Шаг 3] Запуск Selenium (Имитация браузера)...")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={self.ua.random}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        driver = None
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(url)

            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)

            pdf_link = None

            try:
                meta_pdf = driver.find_element(By.CSS_SELECTOR, "meta[name='citation_pdf_url']")
                if meta_pdf:
                    pdf_link = meta_pdf.get_attribute("content")
                    print("Найден мета-тег citation_pdf_url.")
            except:
                pass

            if not pdf_link:
                anchors = driver.find_elements(By.TAG_NAME, "a")
                for a in anchors:
                    href = a.get_attribute("href")
                    text = a.text.upper()
                    if href and ("_pdf" in href or ".pdf" in href or "PDF" in text):
                        if "citation" not in href.lower():
                            pdf_link = href
                            print(f"Найдена ссылка на странице: {href}")
                            break

            if pdf_link:
                selenium_cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
                return self._download_stream(pdf_link, "scraped_article.pdf", cookies=selenium_cookies, referer=url)
            else:
                print("Не удалось найти PDF на странице через Selenium.")
                return False

        except Exception as e:
            print(f"Ошибка Selenium: {e}")
            return False
        finally:
            if driver:
                driver.quit()

    def process(self, url):
        print(f"\n{'=' * 60}\nОбработка: {url}\n{'=' * 60}")

        return self.try_selenium(url)


if __name__ == "__main__":
    downloader = Downloader()
    target_link = "https://arxiv.org/html/2601.05236v1"
    downloader.process(target_link)