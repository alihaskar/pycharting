import sys
import os
from pathlib import Path

# Add project root to path so we can import charting
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import charting

# Setup path to data file
# This handles running from project root or examples directory
data_path = "data/sample.csv"
if not os.path.exists(data_path):
    data_path = "../data/sample.csv"

if not os.path.exists(data_path):
    print(f"❌ Error: Could not find {data_path}")
    exit(1)

print(f"📂 Loading data from {data_path}...")
df = pd.read_csv(data_path)

print("📊 Plotting data...")
# This will start the server and open the browser
charting.plot(df)

