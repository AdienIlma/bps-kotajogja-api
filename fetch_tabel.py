import json
import subprocess
import sys

subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)

from playwright.sync_api import sync_playwright

BASE_URL = "https://jogjakota.bps.go.id"

def scrape_all_tables():
    all_tables = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        
        # Pakai user agent browser biasa supaya tidak diblokir
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        page_num = 1
        while True:
            url = f"{BASE_URL}/id/statistics-table?page={page_num}"
            print(f"Scraping halaman {page_num}: {url}")
            
            try:
                # Ganti networkidle ke domcontentloaded, lebih cepat
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                # Tunggu konten JS selesai render
                page.wait_for_timeout(5000)
            except Exception as e:
                print(f"  Gagal load halaman: {e}")
                break
            
            # Debug: print title halaman
            print(f"  Title: {page.title()}")
            
            # Coba berbagai selector yang mungkin dipakai BPS
            links = (
                page.query_selector_all("a[href*='/statistics-table/1/']") +
                page.query_selector_all("a[href*='/statistics-table/2/']") +
                page.query_selector_all("a[href*='/statistics-table/3/']")
            )
            
            print(f"  Link tabel ditemukan: {len(links)}")
            
            if not links:
                # Debug: print semua link yang ada di halaman
                all_links = page.query_selector_all("a[href]")
                print(f"  Total link di halaman: {len(all_links)}")
                for l in all_links[:10]:
                    print(f"    - {l.get_attribute('href')}")
                break
            
            existing_urls = {t["url"] for t in all_tables}
            new_count = 0
            
            for link in links:
                href = link.get_attribute("href") or ""
                title = link.inner_text().strip()
                
                if title and len(title) > 5:
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
            
            print(f"  {new_count} tabel baru (total: {len(all_tables)})")
            
            next_btn = page.query_selector("a[rel='next'], li.next:not(.disabled) a")
            if not next_btn:
                print("  Tidak ada halaman berikutnya.")
                break
            
            page_num += 1
            if page_num > 50:
                break
        
        browser.close()
    
    return all_tables

tables = scrape_all_tables()

with open("tabel_statistik.json", "w", encoding="utf-8") as f:
    json.dump(tables, f, ensure_ascii=False, indent=2)

print(f"\nSelesai! Total {len(tables)} tabel disimpan.")
