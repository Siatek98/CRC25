import importlib
import subprocess
import sys

packages = {
    "yfinance": "yfinance",
    "riskfolio": "riskfolio-lib",
    "matplotlib": "matplotlib",
    "pandas": "pandas",
    "numpy": "numpy",
    "dateutil": "python-dateutil",
    "openpyxl": "openpyxl"
}

for module_name, package_name in packages.items():
    try:
        importlib.import_module(module_name)
        print(f"{module_name} is already installed.")
    except ImportError:
        print(f"{module_name} not found. Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
