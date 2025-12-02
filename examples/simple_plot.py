import pandas as pd
import charting
import os
import sys

# Setup path to data file
# This handles running from project root or examples directory
data_path = "data/sample.csv"
if not os.path.exists(data_path):
    # Try looking one level up if we are in examples dir
    data_path = "../data/sample.csv"
    if not os.path.exists(data_path):
         # Try looking in project root if script run from examples but cwd is root
         if os.path.exists("data/sample.csv"):
             data_path = "data/sample.csv"

if not os.path.exists(data_path):
    # Try to find it relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "sample.csv")
    
    if not os.path.exists(data_path):
        print(f"❌ Error: Could not find sample.csv")
        print(f"   Searched in: {data_path}")
        print("   Please run from project root.")
        sys.exit(1)

print(f"📂 Loading data from {data_path}...")
df = pd.read_csv(data_path)

print("📊 Plotting data...")
# This will start the server, open the browser, and block until Ctrl+C
charting.plot(df)
