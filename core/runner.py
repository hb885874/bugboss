
import importlib
from core.logger import log_summary

def run_modules(modules):
    summary = []
    for module in modules:
        try:
            plugin = importlib.import_module(f'plugins.{module}')
            result = plugin.run()
            summary.append(f"{module}: {result}")
        except Exception as e:
            summary.append(f"{module}: Failed with error {e}")
    log_summary(summary)
