import requests

def scan(target, results_dir):
    print(f"[*] Scanning {target} for IDOR vulnerabilities...")
    idor_paths = [
        f"{target}?id=1",
        f"{target}?id=2",
        f"{target}?id=3",
        f"{target}/user/1",
        f"{target}/user/2",
        f"{target}/profile/1"
    ]

    for url in idor_paths:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and len(r.text) > 50:
                print(f"[!] Potential IDOR vulnerability detected at {url}")
                with open(f"{results_dir}/idor_hits.txt", "a") as f:
                    f.write(f"[IDOR] {url} -> Status: {r.status_code}\n")
            else:
                print(f"[-] No IDOR vulnerability detected at {url}")
        except Exception as e:
            print(f"[ERROR] {url} -> {str(e)}")
