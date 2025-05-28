# plugins/idor.py

import requests

def scan(target):
    print(f"[*] Scanning {target} for IDOR vulnerabilities...")
    test_ids = ["1", "2", "3"]
    for test_id in test_ids:
        url = f"{target}?id={test_id}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and "user" in response.text.lower():
                print(f"[!] Potential IDOR vulnerability detected at {url}")
            else:
                print(f"[-] No IDOR vulnerability detected at {url}")
        except requests.exceptions.RequestException as e:
            print(f"[!] Error scanning {url}: {e}")
