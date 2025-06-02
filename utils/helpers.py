import os

def ensure_results_dir():
    os.makedirs("results", exist_ok=True)
