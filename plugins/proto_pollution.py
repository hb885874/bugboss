# plugins/proto_pollution.py

import requests
import json

def scan(target):
    print(f"[*] Scanning {target} for prototype pollution vulnerabilities...")
    payload = {
        "__proto__": {
            "polluted": "yes"
        }
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(target, data=json.dumps(payload), headers=headers, timeout=10)
        if "polluted" in response.text:
            print(f"[!] Potential prototype pollution vulnerability detected at {target}")
        else:
            print(f"[-] No prototype pollution vulnerability detected at {target}")
    except requests.exceptions.RequestException as e:
        print(f"[!] Error scanning {target}: {e}")
