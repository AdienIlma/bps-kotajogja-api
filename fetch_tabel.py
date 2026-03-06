import json
import subprocess
import sys

# Install playwright
subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)

from playwright.sync_api import sync_playwright

BASE_URL = "https://jogjakota.bps.go.id"

def scrape_all_tables():
    all_tables = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page_num = 1
        while True:
            url = f"{BASE_URL}/id/statistics-table?page={page_num}"
            print(f"Scraping halaman {page_num}: {url}")
            
            try:
                page.goto(url, timeout=30000, wait_until="networkidle")
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  Gagal load halaman: {e}")
                break
            
            # Ambil semua link tabel
            links = page.query_selector_all("a[href*='/statistics-table/']")
            
            if not links:
                print(f"  Tidak ada tabel di halaman {page_num}, selesai.")
                break
            
            new_count = 0
            existing_urls = {t["url"] for t in all_tables}
            
            for link in links:
                href = link.get_attribute("href") or ""
                title = link.inner_text().strip()
                
                # Filter hanya link tabel yang valid (bukan menu navigasi)
                if (
                    "/statistics-table/1/" in href or
                    "/statistics-table/2/" in href or
                    "/statistics-table/3/" in href
                ) and title and len(title) > 5:
                    full_url = href if href.startswith("http") else BASE_URL + href
                    
                    if full_url not in existing_urls:
                        existing_urls.add(full_url)
                        all_tables.append({
                            "table_id": len(all_tables) + 1,
                            "title": title,
                            "subj": "",
                            "updt_date": "",
                            "url": full_url
                        })
                        new_count += 1
            
            print(f"  Dapat {new_count} tabel baru (total: {len(all_tables)})")
            
            # Cek apakah ada tombol next page
            next_btn = page.query_selector("a[rel='next'], .pagination .next:not(.disabled) a, li.next:not(.disabled) a")
            if not next_btn:
                print("  Tidak ada halaman berikutnya, selesai.")
                break
            
            page_num += 1
            
            # Safety limit
            if page_num > 50:
                break
        
        browser.close()
    
    return all_tables

tables = scrape_all_tables()

with open("tabel_statistik.json", "w", encoding="utf-8") as f:
    json.dump(tables, f, ensure_ascii=False, indent=2)

print(f"\nSelesai! Total {len(tables)} tabel disimpan.")
