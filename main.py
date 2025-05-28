
import argparse
import os
import importlib
from core.runner import run_modules

def parse_args():
    parser = argparse.ArgumentParser(description="Pluggable Bug Hunting Tool")
    parser.add_argument('--modules', type=str, help='Comma-separated module names to run (e.g., proto_pollution,idor)', required=True)
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    selected_modules = [m.strip() for m in args.modules.split(',')]
    run_modules(selected_modules)
