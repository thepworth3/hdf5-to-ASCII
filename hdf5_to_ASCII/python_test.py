import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# ── Configure ──────────────────────────────────────────────────────────────
CSV_FILE = 'all_test/127041.csv'   # change to your output file
# ───────────────────────────────────────────────────────────────────────────

# Read the CSV
df = pd.read_csv(CSV_FILE)

# Basic info
print(f'Shape: {df.shape[0]} rows x {df.shape[1]} columns\n')
print('Columns:')
for i, col in enumerate(df.columns):
    non_nan = df[col].count()
    print(f'  {i:<4} {col:<40} {non_nan} non-NaN values')

# Show first few rows
print('\nFirst 5 rows:')
print(df.head())

# Show summary statistics for numeric columns
print('\nNumeric summary:')
print(df.describe())

monitor_adc = df["Detector1_adc_ch0"]

dunya_adc = df["Detector1_adc_ch8"]

plt.plot(monitor_adc)
plt.show()
plt.plot(dunya_adc)
plt.show()

