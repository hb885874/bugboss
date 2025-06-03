# plugins/proto_pollution.py

import requests
from urllib.parse import urlparse
import difflib
import os
import re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "bugboss-scanner/1.0"
}

PAYLOAD_KEY = "__proto__[isAdmin]"
PAYLOAD_VALUE = "true"

def get_payload():
    return {PAYLOAD_KEY: PAYLOAD_VALUE}

def send_request(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        return response.text
    except Exception as e:
        print(f"[!] Error requesting {url}: {e}")
        return None

def highlight_reflection(html, payload_key, payload_value):
    key_escaped = re.escape(payload_key)
    value_escaped = re.escape(payload_value)

    key_hit = re.search(key_escaped, html, re.IGNORECASE)
    value_hit = re.search(value_escaped, html, re.IGNORECASE)

    if key_hit or value_hit:
        return True
    return False

def generate_html_diff(base_html, polluted_html):
    differ = difflib.HtmlDiff(tabsize=2, wrapcolumn=100)
    diff_html = differ.make_file(
        base_html.splitlines(),
        polluted_html.splitlines(),
        fromdesc='Original',
        todesc='With Payload'
    )
    return diff_html

def scan(url, results_dir):
    payload = get_payload()
    subdir = os.path.join(results_dir, "proto_pollution")
    os.makedirs(subdir, exist_ok=True)

    print(f"[*] Scanning {url} for prototype pollution vulnerabilities...")

    base_html = send_request(url)
    polluted_html = send_request(url, payload)

    if not base_html or not polluted_html:
        print(f"[!] Skipping {url} due to request failure.")
        return

    domain = urlparse(url).netloc.replace(':', '_')

    reflected = highlight_reflection(polluted_html, PAYLOAD_KEY, PAYLOAD_VALUE)
    diffs = list(difflib.unified_diff(base_html.splitlines(), polluted_html.splitlines(), lineterm=""))

    if reflected or diffs:
        print(f"[!!] Potential prototype pollution behavior detected at {url}")

        with open(os.path.join(subdir, f"{domain}_base.html"), "w") as f:
            f.write(base_html)

        with open(os.path.join(subdir, f"{domain}_polluted.html"), "w") as f:
            f.write(polluted_html)

        with open(os.path.join(subdir, "proto_pollution_hits.txt"), "a") as f:
            f.write(f"[!!] {url}\n")
            if reflected:
                f.write("[*] Reflected payload detected!\n")
            if diffs:
                f.write("[*] Response content differs\n")
            f.write("\n")

        # Generate HTML diff
        diff_html = generate_html_diff(base_html, polluted_html)
        with open(os.path.join(subdir, f"{domain}_diff.html"), "w") as f:
            f.write(diff_html)
    else:
        print(f"[-] No prototype pollution signs at {url}")
