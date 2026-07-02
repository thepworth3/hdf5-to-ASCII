# HDF5/NeXus to ASCII Converter

A command-line tool for extracting data from NeXus/HDF5 (`.nxs`) files and exporting selected datasets to CSV files that can be opened in Excel, Origin, or Python. This is useful for quick inspection of ASCII values to see if your files are okay, or if you do not want to do analysis using available hdf5 python readers supported by the ILL, or elsewhere. 

Another use case would be simulations. PENTrack can write HDF5 files much faster than ASCII, and you could extract data afterward with this tool if you like.


---

## Installation

Install directly from GitHub using pip:

```bash
pip install git+https://github.com/thepworth3/hdf5-to-ASCII.git
```
or on SSH
```bash 
pip install git+ssh://git@github.com/thepworth3/hdf5-to-ASCII.git
```

This will install all dependencies automatically and make the command available system-wide. After installation, you can run it from any directory with:

```bash
hdf5_to_ascii
```

No `python` prefix or file path needed.

---

## Requirements

If you prefer to run the script directly rather than installing it, install the dependencies manually, and clone the repository to get the script to keep where you like:

```bash
pip install h5py numpy
```

---

## Usage

Run the script from a terminal:

```bash
python nxs_to_ascii.py
```

The script will guide you through a series of prompts. No configuration file or command-line arguments are needed.

---

## Step-by-step Prompts

### 1. File location and run range

```
Data folder path          : your/path/here
File extension (e.g. .nxs): .nxs (or .hdf5, etc.)
First run number          : 123456
Last run number           : 123460
Step (default 1)          : 2
```

- **Data folder path** — the folder containing your `.nxs` files. Files must be named `<run_number><suffix>`, e.g. `126952.nxs`.
- **File extension** — usually `.nxs`. The dot is optional.
- **Step** — use `2` to process every other run, `3` for every third, etc. Press Enter or 1 for step 1.

### 2. Dataset listing

The script opens the first file and prints every dataset it contains, with its shape, data type, and units:

```
  #    Path                                                    Shape                Dtype        Units
  ---------------------------------------------------------------------------------------------------------
  0    entry0/SUPERSUN/Detector1/data                          (1024, 16, 3562)     uint32
  1    entry0/SUPERSUN/Detector1/detrate                       (1,)                 float32
  ...
  47   entry0/log/Environment_PUCNInstr/average                (1,)                 float64
  49   entry0/log/Environment_PUCNInstr/values                 (712,)               float64
  52   entry0/log/ReactorPower_Rpower/values                   (712,)               float64
  63   entry0/user/name                                        (1,)                 |S8
```

If you have files which have a different format, you need to process them separately.

### 3. Dataset selection

Enter a comma-separated list of dataset numbers. **You can repeat a number** to extract multiple quantities from the same dataset (e.g. different detector channels stored in a higher dimensional data structure):

```
Enter dataset numbers to export (comma-separated, e.g. 0,0,3,5): 0,0,0,49,52,63
```

### 4. Per-dataset configuration

For each selected dataset the script asks how to handle it.

#### 1D datasets (e.g. time series)

```
Dataset: entry0/log/Environment_PUCNInstr/values  shape=(712,)
  Slice range? (e.g. 1:600, or press Enter for all): specify range
  Column label (default: last part of path): provide header string
```

- **Slice range** — optionally restrict to a sub-range of indices, e.g. `1:600`. Press Enter to take all values.
- **Column label** — the header name in the output CSV.

#### String datasets (e.g. user name)

```
Dataset: entry0/user/name  shape=(1,)
  Slice range? (e.g. 1:600, or press Enter for all):
  Column label (default: last part of path): name
```

String handled automatically — datatype conversion should not be an issue.

#### Higher-dimensional datasets

For datasets with 2 or more dimensions, the script asks what to do with each axis. It is presently designed under the assumption that higher dimensional datasets are representing detectors:

| Operation | Description |
|-----------|-------------|
| `sum`     | Sum all values along this axis |
| `mean`    | Average all values along this axis |
| `index N` | Select a single slice at position N (0-indexed) |
| `keep`    | Use this axis as the rows of the output column |

Exactly one axis should be marked `keep` — this becomes the output column length. All other axes must be reduced to a single value via `sum`, `mean`, or `index N`. To save the full 3D space to ASCII further changes are required. However any summations you would like to make across the 3D space can be handled in this pre-processing step.

### 5. Output folder

```
Output folder (default: ascii_output): my_output
```

The folder is created if it does not exist. Each run is written as `<run_number>.csv`.

---

## Worked Example — Detector Data + Slow Controls

This example extracts three quantities from the 3D detector array `(1024, 16, 3562)` — where the axes are **(ADC bins, detector channel, time)** — plus average pressure, reactor power, and user name. Keep in mind the dataset numbers correspond to SuperSUN on June 30, 2026 and certainly do not translate elsewhere.

**Selection input:**
```
Enter dataset numbers to export: 0,0,0,49,52,63
```

**Dataset 0 — first pass: ADC spectrum of channel 0**

Sum over the time axis to get total counts per ADC bin on channel 0.

```
Dataset: entry0/SUPERSUN/Detector1/data  shape=(1024, 16, 3562)

  Axis 0 (size 1024): keep       ← ADC bins become the rows
  Axis 1 (size 16):   index 0    ← select channel 0
  Axis 2 (size 3562): sum        ← sum over all time bins
  Column label: monitor adc
```

Output: 1024 rows, one per ADC bin.

**Dataset 0 — second pass: count rate vs time on channel 0 (monitor)**

Sum over ADC bins to get total counts per time step on channel 0.

```
Dataset: entry0/SUPERSUN/Detector1/data  shape=(1024, 16, 3562)

  Axis 0 (size 1024): sum        ← sum over all ADC bins
  Axis 1 (size 16):   index 0    ← select channel 0
  Axis 2 (size 3562): keep       ← time becomes the rows
  Column label: monitor rate
```

Output: 3562 rows, one per time bin.

**Dataset 0 — third pass: count rate vs time on channel 8 (Dunya detector)**

```
Dataset: entry0/SUPERSUN/Detector1/data  shape=(1024, 16, 3562)

  Axis 0 (size 1024): sum        ← sum over all ADC bins
  Axis 1 (size 16):   index 8    ← select channel 8
  Axis 2 (size 3562): keep       ← time becomes the rows
  Column label: dunya rate
```

Output: 3562 rows, one per time bin.

**Dataset 49 — average pressure (slow control, 712 points)**

```
Dataset: entry0/log/Environment_PUCNInstr/values  shape=(712,)
  Slice range? : 
  Column label : avg pressure
```

**Dataset 52 — reactor power (slow control, 712 points)**

```
Dataset: entry0/log/ReactorPower_Rpower/values  shape=(712,)
  Slice range? : 
  Column label : rPower
```

**Dataset 63 — user name (string)**

```
Dataset: entry0/user/name  shape=(1,)
  Slice range? : 
  Column label : name
```

**Output folder:**
```
Output folder: my_output
```

**Result:**

```
Processing 3 files...

  ⚠ run126952: "monitor adc" has 1024 values, padding to 3562.
  ⚠ run126952: "avg pressure" has 712 values, padding to 3562.
  ⚠ run126952: "rPower" has 712 values, padding to 3562.
  ⚠ run126952: "name" has 1 values, padding to 3562.
✓ run126952  →  my_output\126952.csv  (3562 rows, 6 columns)
```

The output CSV has this structure:

```
monitor adc, monitor rate, dunya rate, avg pressure, rPower, name
0.0,         124.0,        88.0,       1.47e-04,     56.2,   hepworth
1.0,         131.0,        91.0,       1.47e-04,     56.2,
...
711.0,       119.0,        77.0,       ,             ,
...
1023.0,      108.0,        95.0,       ,             ,
```

Columns of different lengths are padded with empty cells (strings) or `NaN` (numbers) to match the longest column. Depending on how you load a file, this could cause mismatching datatype issues. Please keep this in mind.

The error report at the end of the file should indicate any issues with processing that are foreseen. With any bugs or issues with the code, please contact Thomas Hepworth.

---

## Notes

- **Column length mismatch** — if datasets have different lengths (e.g. 3562 time bins vs 712 slow-control points), shorter columns are padded with `NaN` or empty strings. This is expected and normal.
- **String columns** — datasets with byte-string dtype (shown as `|S*` in the listing) are decoded and written as text. They are not convertible to float and will be padded with empty cells.
- **Scalars** — datasets with `shape=(1,)` are treated as a single-row column and padded to match the longest column.
- **Step > 1** — the script skips missing files gracefully and reports which runs were not found.
- **Re-running** — the script always re-reads the file structure from the first available file, so it adapts automatically if file layouts differ between run ranges.
