#!/usr/bin/env python3

import numpy as np
import pandas as pd

import json
import glob
import os
import sys
import re

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "/customization_approx/*.json")
data = [json.load(open(path)) for path in paths]

customization_running_times = pd.DataFrame.from_records([{
    'approx': algo['approx'],
    'approx_threshold': algo['approx_threshold'],
    'customization_running_time_s': algo['main']['running_time_ms'] / 1000 }
    for run in data for algo in run["algo_runs"] if algo['algo'] == "Floating TDCCH Customization"])

events = pd.DataFrame.from_records([
    {
        'approx': algo['approx'],
        'approx_threshold': algo['approx_threshold'],
        **event
    }
    for run in data
    for algo in run["algo_runs"] if algo['algo'] == "Floating TDCCH Customization"
    for event in algo["main"]["events"]])

events['ipps_per_active_shortcut'] = events['num_ipps_stored'] / events['num_shortcuts_active']

output = customization_running_times \
  .pivot(index='approx', columns='approx_threshold', values='customization_running_time_s') \
  .round() \
  .to_latex(na_rep="OOM", float_format='{:0.0f}'.format, column_format='rrrrrr', index_names=False) \
  .replace('nan', 'OOM') \
  .replace('approx\\_threshold', '') \

output = re.sub(re.compile('([0-9]{3}(?=[0-9]))'), "\\g<0>,\\\\", output[::-1])[::-1]
output = re.sub(re.compile('\\.\\d'), '\\g<0>s', output)
lines = output.split("\n")
output = "\n".join(lines[:2] + [R"\multicolumn{1}{c}{\multirow[c]{2}{*}{$\epsilon$}} & \multicolumn{5}{c}{$\beta$} \\ \cmidrule(lr){2-6}"] + lines[2:]) + "\n"

with open("paper/table/approx_params_running_times.tex", 'w') as f:
  f.write(output)

output = events.groupby(['approx', 'approx_threshold'])['ipps_per_active_shortcut'].mean().unstack() \
  .round() \
  .to_latex(na_rep="OOM", float_format='{:0.0f}'.format, column_format='rrrrrr', index_names=False) \
  .replace('nan', 'OOM') \
  .replace('approx\\_threshold', '') \

output = re.sub(re.compile('([0-9]{3}(?=[0-9]))'), '\\g<0>,\\\\', output[::-1])[::-1]
output = re.sub(re.compile('\\.\\d'), '\\g<0>s', output)
lines = output.split("\n")
output = "\n".join(lines[:2] + [R"\multicolumn{1}{c}{\multirow[c]{2}{*}{$\epsilon$}} & \multicolumn{5}{c}{$\beta$} \\ \cmidrule(lr){2-6}"] + lines[2:]) + "\n"

with open("paper/table/approx_params_active_ipps_avg.tex", 'w') as f:
  f.write(output)
