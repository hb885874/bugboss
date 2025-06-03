# plugins/proto_pollution.py

import os
import re
import json
import time
import difflib
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Try importing selenium and handle gracefully if unavailable
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ModuleNotFoundError:
    print("[!] Selenium not available. DOM-based tests will be skipped.")
    SELENIUM_AVAILABLE = False

# Payloads for prototype pollution
def get_payloads():
    return [
        {"__proto__": {"isHacked": True}},
        {"constructor": {"prototype": {"polluted": 1}}},
        {"__proto__": {"admin": True}}
    ]

# Set up headless browser for DOM behavior testing
def setup_browser():
    if not SELENIUM_AVAILABLE:
        return None
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=chrome_options)

# Inject payload into URL query string
def inject_payload(base_url, payload):
    for key, val in payload.items():
        full_url = f"{base_url}?{key}={json.dumps(val)}"
        yield full_url

# Basic reflection check
def is_reflected(response_text, payload):
    for key in payload.keys():
        if key in response_text:
            return True, key
    return False, None

# Check DOM via headless browser
def check_dom_effect(driver, url):
    if not driver:
        return False, None
    try:
        driver.get(url)
        time.sleep(2)
        dom = driver.execute_script("return document.body.innerHTML")
        if "isHacked" in dom or "polluted" in dom or "admin" in dom:
            return True, dom
    except Exception:
        return False, None
    return False, None

# Analyze JS sinks
def extract_js_sinks(session, base_url):
    try:
        res = session.get(base_url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        scripts = soup.find_all("script")
        sink_hits = []
        pattern = re.compile(r'(Object\\.assign|\\.extend|_.merge)\\s*\\(')

        for script in scripts:
            if script.get("src"):
                js_url = urljoin(base_url, script["src"])
                try:
                    js_code = session.get(js_url, timeout=5).text
                    for match in pattern.finditer(js_code):
                        sink_hits.append((js_url, match.group()))
                except:
                    continue
            else:
                if script.string:
                    for match in pattern.finditer(script.string):
                        sink_hits.append((base_url, match.group()))
        return sink_hits
    except Exception:
        return []

# Save report as markdown
def save_markdown_report(report_lines, output_file):
    with open(output_file, "w") as f:
        f.write("\n".join(report_lines))

# Main scanner logic
def scan(target, results_dir):
    session = requests.Session()
    driver = setup_browser()
    payloads = get_payloads()
    report = [f"# Prototype Pollution Scan Report for {target}\n"]
    hit_count = 0

    for payload in payloads:
        for test_url in inject_payload(target, payload):
            try:
                print(f"[+] Testing: {test_url}")
                r = session.get(test_url, timeout=10)
                reflected, key = is_reflected(r.text, payload)
                dom_effect, dom_snapshot = check_dom_effect(driver, test_url)
                sinks = extract_js_sinks(session, target)

                if reflected or dom_effect or sinks:
                    hit_count += 1
                    report.append(f"## Finding {hit_count}")
                    report.append(f"**Tested URL**: `{test_url}`")
                    report.append(f"**Reflected**: `{reflected}` ({key})")
                    report.append(f"**DOM Mutation**: `{dom_effect}`")
                    if dom_snapshot:
                        dom_file = os.path.join(results_dir, f"dom_snapshot_{hit_count}.html")
                        with open(dom_file, "w") as f:
                            f.write(dom_snapshot)
                        report.append(f"**DOM Snapshot Saved**: `{dom_file}`")
                    if sinks:
                        report.append("**Sink Matches in JS**:")
                        for js_url, match in sinks:
                            report.append(f"- `{match}` in `{js_url}`")
                    report.append("\n")
            except Exception as e:
                print(f"[-] Error: {e}")
                continue

    if driver:
        driver.quit()
    if hit_count == 0:
        print("[-] No vulnerabilities detected.")
    else:
        out_file = os.path.join(results_dir, "proto_pollution_report.md")
        save_markdown_report(report, out_file)
        print(f"[+] Report saved to: {out_file}")
