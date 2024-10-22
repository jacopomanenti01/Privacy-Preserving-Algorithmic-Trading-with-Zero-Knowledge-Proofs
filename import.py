import json
import subprocess
import sys

# Load dependencies from the JSON file
def load_dependencies(json_file):
    with open(json_file, "r") as file:
        return json.load(file)

# Install the package if it's not installed
def install_and_import(package, version):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", f"{package}=={version}"])
        __import__(package)

# Install required dependencies
def install_dependencies(dependencies):
    for package, version in dependencies.items():
        if version != "builtin":  # Skip built-in modules
            install_and_import(package, version)

# Main script to install and import all libraries
if __name__ == "__main__":
    dependencies = load_dependencies("requirements.json")
    install_dependencies(dependencies)

    # Importing the libraries
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib as mtl
    import math
    import yfinance as yf

    # Now you can use the libraries as usual
    print("All dependencies are installed and imported successfully!")
