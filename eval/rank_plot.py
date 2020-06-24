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

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "/rank_queries_all_graphs/*.json")
data = [json.load(open(path)) for path in paths]

running_times = pd.DataFrame.from_records([{
  'algo_running_time_ms': algo['running_time_ms'],
  'algox': 'CATCHUp Query',
  **algo }
  for run in data if os.environ['TDCCH_MAIN_GRAPH'] in run['args'][1] for algo in run["algo_runs"] if algo['algo'] == "Floating TDCCH Query"])

running_times = running_times.append(pd.DataFrame.from_records([{
  'algo_running_time_ms': algo['unpacking_running_time_ms'],
  'algox': 'Unpacking',
  **algo }
  for run in data if os.environ['TDCCH_MAIN_GRAPH'] in run['args'][1] for algo in run["algo_runs"] if algo['algo'] == "Floating TDCCH Query" and 'unpacking_running_time_ms' in algo]))

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "/rank_query_stats_no_astar_all_graphs/*.json")
data = [json.load(open(path)) for path in paths]

running_times = running_times.append(pd.DataFrame.from_records([{
  'algo_running_time_ms': algo['running_time_ms'],
  'algox': 'CATCHUp Query w/o A*',
  **algo }
  for run in data if os.environ['TDCCH_MAIN_GRAPH'] in run['args'][1] for algo in run["algo_runs"] if algo['algo'] == "Floating TDCCH Query"]), sort=True)

running_times = running_times.sort_values(by=['algox']).loc[lambda x: x['rank'] > 6]

plt.figure(figsize=(11,4))
g = sns.boxplot(data=running_times, x='rank', y='algo_running_time_ms', hue='algox', linewidth=0.8)
g.set_yscale('log')
g.legend().set_title('')
g.set_ylabel('Running Time [ms]')
g.set_xlabel('Dijkstra Rank')
plt.tight_layout()

g.get_figure().savefig('paper/fig/ranks.pdf')
