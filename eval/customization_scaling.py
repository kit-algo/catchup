#!/usr/bin/env python3

import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
import seaborn as sns
sns.set()

import pandas as pd

import json
import glob
import os

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "customization_scaling/*.json")
data = [json.load(open(path)) for path in paths]

customization_running_times = pd.DataFrame.from_records([{
    'num_threads': run['num_threads'],
    'customization_running_time_s': algo['main']['running_time_ms'] / 1000 }
    for run in data if not 'TDCCH_DISABLE_PAR' in run['feature_flags'] for algo in run["algo_runs"] if algo['algo'] == "Floating TDCCH Customization"])
customization_running_times['work'] = customization_running_times['num_threads'] * customization_running_times['customization_running_time_s']

baseline = pd.DataFrame.from_records([{
    'customization_running_time_s': algo['main']['running_time_ms'] / 1000 }
    for run in data if 'TDCCH_DISABLE_PAR' in run['feature_flags'] for algo in run["algo_runs"] if algo['algo'] == "Floating TDCCH Customization"]) \
    ['customization_running_time_s'].mean()

customization_running_times['efficiency'] = baseline / customization_running_times['work']

fig = plt.figure(figsize=(7/1.1,3/1.1))
ax1 = fig.add_subplot(121)
ax2 = fig.add_subplot(122)

sns.catplot(x="num_threads", y="customization_running_time_s", kind="bar", data=customization_running_times, ax=ax1)
ax1.set(xlabel='Threads', ylabel='Running time [s]')
ax1.axhline(y=baseline, linestyle='dashed')

sns.catplot(x="num_threads", y="efficiency", kind="bar", data=customization_running_times, ax=ax2)
ax2.set(xlabel='Threads', ylabel='Efficiency')

fig.tight_layout()
fig.savefig('paper/fig/customization_scaling.pdf')
