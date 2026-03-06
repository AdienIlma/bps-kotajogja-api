import json
import urllib.request
from html.parser import HTMLParser

BASE_URL = "https://jogjakota.bps.go.id"

class TableListParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.in_table_link = False
        self.current_title = ""
        self.current_url = ""

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if "/statistics-table/" in href:
                self.in_table_link = True
                self.current_url = href if href.startswith("http") else BASE_URL + href
                self.current_title = ""

    def handle_data(self, data):
        if self.in_table_link:
            self.current_title += data.strip()

    def handle_endtag(self, tag):
        if tag == "a" and self.in_table_link:
            self.in_table_link = False
            title = self.current_title.strip()
            if title and self.current_url:
                self.tables.append({
                    "title": title,
                    "url": self.current_url
                })

def fetch_page(url):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; BPS-Scraper/1.0)"
        })
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

all_tables = []
page = 1

while True:
    url = f"{BASE_URL}/id/statistics-table?page={page}"
    print(f"Scraping halaman {page}...")
    html = fetch_page(url)
    
    if not html:
        break

    parser = TableListParser()
    parser.feed(html)
    
    if not parser.tables:
        print("Tidak ada tabel lagi, selesai.")
        break

    # Hindari duplikat
    existing_urls = {t["url"] for t in all_tables}
    new_tables = [t for t in parser.tables if t["url"] not in existing_urls]
    
    if not new_tables:
        break

    for i, t in enumerate(new_tables, start=len(all_tables) + 1):
        all_tables.append({
            "table_id": i,
            "title": t["title"],
            "subj": "",
            "updt_date": "",
            "url": t["url"]
        })
    
    print(f"  Dapat {len(new_tables)} tabel baru (total: {len(all_tables)})")
    page += 1

with open("tabel_statistik.json", "w", encoding="utf-8") as f:
    json.dump(all_tables, f, ensure_ascii=False, indent=2)

print(f"\nSelesai! Total {len(all_tables)} tabel disimpan ke tabel_statistik.json")
