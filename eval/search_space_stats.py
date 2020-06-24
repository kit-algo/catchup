#!/usr/bin/env python3

import numpy as np
import pandas as pd

import json
import glob
import os
import sys
import re

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "/query_stats_all_graphs/*.json")
data = [json.load(open(path)) for path in paths]

query_running_times = pd.DataFrame.from_records([{
    'graph': run['args'][1],
    'A*': True,
    **algo }
    for run in data for algo in run["algo_runs"] if algo['algo'] == "Floating TDCCH Query"])

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "/query_stats_no_astar_all_graphs/*.json")
data = [json.load(open(path)) for path in paths]

query_running_times = query_running_times.append(pd.DataFrame.from_records([{
    'graph': run['args'][1],
    'A*': False,
    **algo }
    for run in data for algo in run["algo_runs"] if algo['algo'] == "Floating TDCCH Query"]))

table = query_running_times \
    .groupby(['graph', 'A*']) \
    [['num_nodes_in_elimination_tree_search_space', 'num_relaxed_elimination_tree_arcs', 'num_settled_nodes', 'num_relaxed_shortcut_arcs', 'running_time_ms']] \
    .mean() \
    .unstack()

table['num_nodes_in_elimination_tree_search_space_joined', '---'] = table['num_nodes_in_elimination_tree_search_space'][False].round().astype(int)
table['num_relaxed_elimination_tree_arcs_joined', '---'] = table['num_relaxed_elimination_tree_arcs'][False].round().astype(int)

table['num_settled_nodes'] = table['num_settled_nodes'].round().astype(int)
table['num_relaxed_shortcut_arcs'] = table['num_relaxed_shortcut_arcs'].round().astype(int)

output = table[['num_nodes_in_elimination_tree_search_space_joined', 'num_relaxed_elimination_tree_arcs_joined', 'num_settled_nodes', 'num_relaxed_shortcut_arcs', 'running_time_ms']] \
    .loc[[os.environ['TDCCH_GRAPH_DIR'] + graph for graph in ['/de/day/dido/', '/ptv17-de-car/day/di/', '/ptv17-eur-car/day/di/']]] \
    .rename(index={ os.environ['TDCCH_GRAPH_DIR'] + old: new for (old, new) in [('/de/day/dido/', 'Ger06'), ('/ptv17-de-car/day/di/', 'Ger17'), ('/ptv17-eur-car/day/di/', 'Eur17')] }) \
    .rename(columns={'num_nodes_in_elimination_tree_search_space_joined': 'Nodes in CCH search space',
                     'num_relaxed_elimination_tree_arcs_joined': 'Relaxed shortcuts',
                     'num_settled_nodes': 'Queue pops',
                     'num_relaxed_shortcut_arcs': 'Relaxed arcs',
                     'running_time_ms': 'Running time [ms]',}) \
    .to_latex(float_format='{:0.2f}'.format, column_format='lrrrrrrrr', index_names=False) \
    .replace('False', 'no A*') \
    .replace('True', 'A*') \
    .replace('---', '')

output = re.sub(re.compile('([0-9]{3}(?=[0-9]))'), '\\g<0>,\\\\', output[::-1])[::-1]
lines = output.split("\n")
lines = lines[:2] + [
  R"{} & \multicolumn{2}{c}{Elimination tree interval query} & \multicolumn{4}{c}{Lazy corridor Dijkstra} & \\ \cmidrule(lr){2-3} \cmidrule(lr){4-7}",
  R"{} & \multirow{2}{*}{\makecell{Nodes in \\ search space}} & \multirow{2}{*}{\makecell{Relaxed \\ shortcuts}} & \multicolumn{2}{c}{Queue pops} & \multicolumn{2}{c}{Relaxed arcs} & \multicolumn{2}{c}{Time [ms]} \\ \cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(lr){8-9}"
] + lines[3:]
output = "\n".join(lines) + "\n"

with open("paper/table/search_space_stats.tex", 'w') as f:
  f.write(output)
