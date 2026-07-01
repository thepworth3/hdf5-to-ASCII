# =============================================================================
# nxs_to_ascii.py
#
# Description : Extracts datasets from NeXus/HDF5 (.nxs) files and exports
#               them as CSV files for plotting and analysis.
#
# Author      : Thomas Hepworth
# Institution : Heidelberg University / Institut Laue-Langevin (ILL)
# Experiment  : SuperSUN UCN experiment
# Contact     : <thepworth@physi.uni-heidelberg.de>
#
# Created     : July 2026
# Version     : 1.0
#
# License     : MIT License
#               Copyright (c) 2026 Thomas Hepworth
#               Permission is hereby granted, free of charge, to any person
#               obtaining a copy of this software to use, copy, modify, and
#               distribute it, subject to the condition that this copyright
#               notice is retained in all copies.
#
# Dependencies: h5py, numpy
#
# Usage       : python nxs_to_ascii.py
#               See README.md for full documentation and worked examples.
# =============================================================================


import h5py
import numpy as np
import os
import csv


def find_filepath(folder, run_number, suffix):
    path = os.path.join(folder, f'{run_number}{suffix}')
    if not os.path.exists(path):
        raise FileNotFoundError(f'No file found for run {run_number} in {folder}')
    return path


def collect_datasets(hdf_file):
    datasets = {}
    def visitor(name, obj):
        if isinstance(obj, h5py.Dataset):
            datasets[name] = {
                'shape': obj.shape,
                'dtype': obj.dtype,
                'attrs': dict(obj.attrs)
            }
    hdf_file.visititems(visitor)
    return datasets


def print_datasets(datasets):
    print('\n  Available datasets:')
    print(f'  {"#":<4} {"Path":<55} {"Shape":<20} {"Dtype":<12} {"Units"}')
    print('  ' + '-'*105)
    for i, (path, info) in enumerate(datasets.items()):
        units = info['attrs'].get('units', info['attrs'].get('unit', ''))
        if isinstance(units, bytes):
            units = units.decode()
        print(f'  {i:<4} {path:<55} {str(info["shape"]):<20} {str(info["dtype"]):<12} {units}')
    print()


def prompt_slice(prompt_text):
    """Keep asking until the user enters a valid N:M slice or presses Enter for all."""
    while True:
        raw = input(prompt_text).strip()
        if raw == '':
            return None
        parts = raw.split(':')
        if len(parts) == 2:
            try:
                s, e = int(parts[0]), int(parts[1])
                return s, e
            except ValueError:
                pass
        print('    ⚠ Please enter a range like 1:600, or press Enter for all.')


def prompt_run_range():
    print('\n=== NeXus to ASCII Converter ===\n')
    folder = input('  Data folder path          : ').strip()
    suffix = input('  File extension (e.g. .nxs): ').strip()
    if not suffix.startswith('.'):
        suffix = '.' + suffix

    start = int(input('  First run number          : '))
    end   = int(input('  Last run number           : '))
    step  = input('  Step (default 1)          : ').strip()
    step  = int(step) if step else 1
    runs  = list(range(start, end + 1, step))
    print(f'\n  → {len(runs)} runs selected: {runs[0]} ... {runs[-1]} (step {step})')
    return folder, suffix, runs


def prompt_nd_reduction(path, shape):
    """
    For an N-dimensional dataset, ask the user what to do with each axis.
    Options per axis:
      sum     - sum over this axis
      mean    - average over this axis
      index N - select a single index along this axis
      keep    - keep this axis as the output rows (only one axis can be 'keep')
    Returns a list of axis operations and a slicing tuple for any initial index selection.
    """
    print(f'\n  Dataset has {len(shape)} dimensions: {shape}')
    print('  For each axis, choose an operation:')
    print('    sum      - sum all values along this axis')
    print('    mean     - average all values along this axis')
    print('    index N  - select a single slice (e.g. index 0)')
    print('    keep     - use this axis as rows in the output\n')

    ops = []
    keep_count = 0
    for ax, size in enumerate(shape):
        while True:
            raw = input(f'    Axis {ax} (size {size}): ').strip().lower()
            if raw == 'sum':
                ops.append(('sum', ax))
                break
            elif raw == 'mean':
                ops.append(('mean', ax))
                break
            elif raw.startswith('index'):
                parts = raw.split()
                if len(parts) == 2:
                    try:
                        idx = int(parts[1])
                        if 0 <= idx < size:
                            ops.append(('index', idx))
                            break
                        else:
                            print(f'      ⚠ Index must be between 0 and {size - 1}.')
                    except ValueError:
                        pass
                print('      ⚠ Please enter e.g. "index 0".')
            elif raw == 'keep':
                if keep_count > 0:
                    print('      ⚠ Only one axis can be "keep".')
                else:
                    ops.append(('keep', ax))
                    keep_count += 1
                    break
            else:
                print('      ⚠ Please enter: sum, mean, index N, or keep.')

    if keep_count == 0:
        print('\n  ⚠ No axis marked as "keep" — result will be a single scalar per file.')

    return ops


def apply_nd_reduction(data, ops):
    """
    Apply the axis operations to a numpy array.
    Operations are applied in reverse axis order so that axis indices
    remain valid after each reduction.
    """
    # First pass: apply index selections (these don't change ndim in the same way)
    # We process from last axis to first to keep indices stable
    result = data.copy()

    # Apply in reverse order to preserve axis numbering
    for i, (op, val) in reversed(list(enumerate(ops))):
        ax = len(ops) - 1 - i  # current axis after previous reductions
        # Recompute which axis in the current array this corresponds to
        # Track which original axes are still present
        pass

    # Simpler approach: build the reduction step by step
    # tracking current axis positions
    result = np.array(data, dtype=float)
    # We'll process axes from highest to lowest to keep indices stable
    indexed_axes = [(i, op, val) for i, (op, val) in enumerate(ops)]

    # Sort: process 'index' and reductions from last axis to first
    for orig_ax in range(len(ops) - 1, -1, -1):
        op, val = ops[orig_ax]
        # Current axis in result = number of axes before orig_ax that have already been reduced
        # Since we go from last to first, axes after orig_ax are already gone;
        # the current axis index equals orig_ax minus the number of axes < orig_ax already removed
        # Simpler: since we go last→first, current axis = orig_ax (nothing before it removed yet)
        cur_ax = orig_ax
        if op == 'sum':
            result = np.sum(result, axis=cur_ax)
        elif op == 'mean':
            result = np.mean(result, axis=cur_ax)
        elif op == 'index':
            result = np.take(result, val, axis=cur_ax)
        elif op == 'keep':
            pass  # leave this axis alone

    return np.atleast_1d(result)


def prompt_dataset_selection(datasets):
    keys = list(datasets.keys())
    print_datasets(datasets)

    raw = input('  Enter dataset numbers to export (comma-separated, e.g. 0,0,3,5): ')
    indices = [int(x.strip()) for x in raw.split(',')]
    
    # Use a list of (path, info) tuples instead of a dict, to allow duplicates
    selected = [(keys[i], datasets[keys[i]]) for i in indices]

    print()
    column_configs = []
    for path, info in selected:
        print(f'  Dataset: {path}  shape={info["shape"]}')
        shape = info['shape']

        if len(shape) == 0:
            print('    ⚠ Scalar dataset, skipping.')
            continue

        elif len(shape) == 1:
            result = prompt_slice('    Slice range? (e.g. 1:600, or press Enter for all): ')
            if result:
                s, e = result
                slicing = (slice(s - 1, e),)
            else:
                slicing = (slice(None),)
            label = input('    Column label (default: last part of path): ').strip()
            label = label if label else path.split('/')[-1]
            column_configs.append({
                'path': path, 'slicing': slicing, 'label': label,
                'ndim': 1, 'nd_ops': None
            })

        elif len(shape) == 2:
            row = input('    Which row? (0-indexed, e.g. 0 for first row): ').strip()
            row = int(row) if row else 0
            result = prompt_slice('    Column slice range? (e.g. 1:600, or press Enter for all): ')
            if result:
                s, e = result
                slicing = (row, slice(s - 1, e))
            else:
                slicing = (row, slice(None))
            label = input('    Column label (default: last part of path): ').strip()
            label = label if label else path.split('/')[-1]
            column_configs.append({
                'path': path, 'slicing': slicing, 'label': label,
                'ndim': 2, 'nd_ops': None
            })

        else:
            # Higher-dimensional: prompt for axis-by-axis reduction
            nd_ops = prompt_nd_reduction(path, shape)
            label = input('    Column label (default: last part of path): ').strip()
            label = label if label else path.split('/')[-1]
            column_configs.append({
                'path': path, 'slicing': None, 'label': label,
                'ndim': len(shape), 'nd_ops': nd_ops, 'shape': shape
            })

        print()

    return column_configs


def read_column(f, col):
    """Read and reduce a dataset to a 1D array."""
    path  = col['path']
    dtype = f[path].dtype

    # String datasets
    if h5py.check_string_dtype(dtype):
        raw  = f[path][col['slicing']] if col['slicing'] else f[path][()]
        data = np.atleast_1d(np.array(raw))
        return np.array([v.decode() if isinstance(v, bytes) else v for v in data]), True

    # High-dimensional datasets
    if col['nd_ops'] is not None:
        raw  = np.array(f[path][()], dtype=float)
        data = apply_nd_reduction(raw, col['nd_ops'])
        return data, False

    # 1D / 2D datasets
    raw  = f[path][col['slicing']]
    data = np.atleast_1d(np.array(raw, dtype=float))
    return data, False


def export_run(run_number, folder, suffix, column_configs, output_folder):
    filepath = find_filepath(folder, run_number, suffix)

    with h5py.File(filepath, 'r') as f:
        columns    = []
        labels     = []
        is_string  = []
        max_length = 0

        for col in column_configs:
            try:
                data, string_col = read_column(f, col)
            except Exception as e:
                print(f'    ⚠ run{run_number}: could not read "{col["label"]}" — {e}')
                continue
            columns.append(data)
            labels.append(col['label'])
            is_string.append(string_col)
            if len(data) > max_length:
                max_length = len(data)

    if not columns:
        print(f'  ✗ run{run_number}: no valid columns, skipping.')
        return

    # Pad shorter columns
    padded = []
    for data, string_col, label in zip(columns, is_string, labels):
        if len(data) < max_length:
            print(f'    ⚠ run{run_number}: "{label}" has {len(data)} values, '
                  f'padding to {max_length}.')
            pad = np.array([''] * (max_length - len(data))) if string_col \
                  else np.full(max_length - len(data), np.nan)
            data = np.concatenate([data, pad])
        padded.append(data)

    out_path = os.path.join(output_folder, f'{run_number}.csv')
    with open(out_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(labels)
        for row_i in range(max_length):
            writer.writerow([col[row_i] for col in padded])

    print(f'  ✓ run{run_number}  →  {out_path}  ({max_length} rows, {len(padded)} columns)')


def main():
    folder, suffix, runs = prompt_run_range()

    print('\n  Reading header from first file...')
    first_file = None
    for run in runs:
        try:
            first_file = find_filepath(folder, run, suffix)
            print(f'  Using: {first_file}')
            break
        except FileNotFoundError:
            continue

    if first_file is None:
        print('  ✗ Could not find any files. Check folder path and file extension.')
        return

    with h5py.File(first_file, 'r') as f:
        print('\n  File attributes (header metadata):')
        for k, v in f.attrs.items():
            print(f'    {k}: {v}')
        datasets = collect_datasets(f)

    column_configs = prompt_dataset_selection(datasets)

    if not column_configs:
        print('  No columns selected, exiting.')
        return

    out_folder = input('  Output folder (default: ascii_output): ').strip()
    out_folder = out_folder if out_folder else 'ascii_output'
    os.makedirs(out_folder, exist_ok=True)

    print(f'\n  Processing {len(runs)} files...\n')
    for run in runs:
        try:
            export_run(run, folder, suffix, column_configs, out_folder)
        except FileNotFoundError:
            print(f'  ✗ run{run}: file not found, skipping.')
        except Exception as e:
            print(f'  ✗ run{run}: error — {e}')

    print(f'\n  Done. Files written to: {os.path.abspath(out_folder)}\n')


if __name__ == '__main__':
    main()
