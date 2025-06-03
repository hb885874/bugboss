# recon_engine

import os
import re
import sys
import json
import time
import argparse
import threading
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

output_dir = "recon_results"
os.makedirs(output_dir, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; ReconBot/1.0)"
}

# ---------------------- Basic Utilities ----------------------
def save_to_file(path, lines):
    with open(path, "w") as f:
        for line in sorted(set(lines)):
            f.write(line.strip() + "\n")

# ---------------------- Crawler ----------------------
def crawl_url(url, depth=1):
    found_links = set()
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup.find_all(["a", "script"]):
            src = tag.get("href") or tag.get("src")
            if src:
                full_url = urljoin(url, src)
                if urlparse(full_url).netloc == urlparse(url).netloc:
                    found_links.add(full_url)
    except Exception:
        pass
    return list(found_links)

# ---------------------- Wayback URLs ----------------------
def get_wayback_urls(domain):
    try:
        api = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=original&collapse=urlkey"
        res = requests.get(api, timeout=15)
        entries = res.json()[1:] if res.status_code == 200 else []
        return [e[0] for e in entries]
    except:
        return []

# ---------------------- Screenshot Capture ----------------------
def capture_screenshot(url, out_file):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(15)
        driver.get(url)
        time.sleep(2)
        driver.save_screenshot(out_file)
        driver.quit()
    except:
        pass

# ---------------------- Recon Core ----------------------
def process_target(url, mode="fast"):
    print(f"[*] Recon for {url}")
    all_links = set([url])
    crawl_depth = 2 if mode == "deep" else 1

    for _ in range(crawl_depth):
        new_links = set()
        for link in all_links.copy():
            found = crawl_url(link)
            new_links.update(found)
        all_links.update(new_links)

    js_links = [l for l in all_links if l.endswith(".js")]
    param_links = [l for l in all_links if "?" in l and "=" in l]

    # Wayback
    domain = urlparse(url).netloc
    wayback = get_wayback_urls(domain)

    # Screenshots
    ss_dir = os.path.join(output_dir, "screenshots")
    os.makedirs(ss_dir, exist_ok=True)
    for idx, link in enumerate(all_links):
        out_img = os.path.join(ss_dir, f"ss_{idx}.png")
        capture_screenshot(link, out_img)

    # Save outputs
    save_to_file(os.path.join(output_dir, f"{domain}_all_links.txt"), all_links)
    save_to_file(os.path.join(output_dir, f"{domain}_js_links.txt"), js_links)
    save_to_file(os.path.join(output_dir, f"{domain}_fuzzable.txt"), param_links)
    save_to_file(os.path.join(output_dir, f"{domain}_wayback.txt"), wayback)

    return param_links  # can be passed to plugins

# ---------------------- CLI + Main ----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="target.txt with one URL per line", required=True)
    parser.add_argument("--mode", help="fast or deep", choices=["fast", "deep"], default="fast")
    parser.add_argument("--plugins", help="comma-separated plugin names", default="")
    args = parser.parse_args()

    with open(args.input) as f:
        targets = [x.strip() for x in f if x.strip()]

    all_fuzzable = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_target, t, args.mode) for t in targets]
        for fut in futures:
            result = fut.result()
            all_fuzzable.extend(result)

    # Auto plugin integration (placeholder call logic)
    for plugin in args.plugins.split(","):
        plugin = plugin.strip()
        if plugin == "proto_pollution":
            print("[*] Running proto_pollution plugin...")
            from plugins import proto_pollution
            for u in all_fuzzable:
                try:
                    proto_pollution.scan(u, "recon_results")
                except Exception as e:
                    print(f"[-] Plugin error: {e}")
