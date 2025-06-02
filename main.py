# main.py

import argparse
import importlib
import sys

def load_targets(file_path):
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[!] Targets file not found: {file_path}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="BugBoss Vulnerability Scanner")
    parser.add_argument('--modules', type=str, required=True, help="Comma-separated list of modules to run (e.g., proto_pollution,idor)")
    parser.add_argument('--targets', type=str, default='targets.txt', help="Path to the targets file")
    args = parser.parse_args()

    modules = args.modules.split(',')
    targets = load_targets(args.targets)
    os.makedirs("results", exist_ok=True)

    for module_name in modules:
        try:
            module = importlib.import_module(f"plugins.{module_name}")
            for target in targets:
                module.scan(target, "results")
        except ModuleNotFoundError:
            print(f"[!] Module not found: {module_name}")
        except AttributeError:
            print(f"[!] 'scan' function not found in module: {module_name}")

if __name__ == "__main__":
    main()
