
import os
from datetime import datetime

def log_summary(summary_lines):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    results_dir = f'results/{timestamp}'
    os.makedirs(results_dir, exist_ok=True)
    with open(f'{results_dir}/summary.txt', 'w') as f:
        for line in summary_lines:
            f.write(line + '\n')
