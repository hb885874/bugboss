from utils.helpers import ensure_results_dir

def run(target):
    ensure_results_dir()
    output_file = "results/idor_results.txt"
    with open(output_file, "a") as f:
        for i in range(1, 4):
            url = f"{target}?id={i}"
            try:
                response = requests.get(url, timeout=5)
                if "user" in response.text.lower() or "account" in response.text.lower():  # crude check
                    f.write(f"[{target}] Possible IDOR at {url}\n")
                    print(f"[!] Potential IDOR vulnerability detected at {url}")
                else:
                    print(f"[-] No IDOR vulnerability detected at {url}")
            except Exception as e:
                print(f"[!] Error checking {url}: {str(e)}")
