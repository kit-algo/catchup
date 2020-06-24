#!/usr/bin/env python3

import numpy as np
import pandas as pd

import json
import glob
import os
import re

graph_pattern = re.compile(".*Reading TPGR file '(.+)/graph.tpgr'.*")
total_runtime_pattern = re.compile(".*Ordering took ([0-9\\.]+) sec in total\\..*")
io_runtime_pattern = re.compile(".*Writing hierarchy to file took ([0-9\\.]+) sec in total\\..*")
no_io_runtime_pattern = re.compile(".*Ordering took ([0-9\\.]+) sec without writing to file\\..*")
thread_count_pattern = re.compile(".*Preprocessing running with (\d+) threads.*")

def parse_katch_contraction_output(path):
  stats = {}
  with open(path, 'r') as f:
    for line in f:
      match = graph_pattern.match(line)
      if match:
        stats['graph'] = match[1]

      match = total_runtime_pattern.match(line)
      if match:
        stats['running_time_s'] = float(match[1])

      match = io_runtime_pattern.match(line)
      if match:
        stats['io_running_time_s'] = float(match[1])

      match = no_io_runtime_pattern.match(line)
      if match:
        stats['no_io_running_time_s'] = float(match[1])

      match = thread_count_pattern.match(line)
      if match:
        stats['num_threads'] = int(match[1])

  return stats

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "/katch/contraction/*.out")
katch_contraction_stats = pd.DataFrame.from_records([parse_katch_contraction_output(path) for path in paths])
katch_contraction_stats.set_index('graph', inplace=True)

graph_pattern = re.compile(".*Reading BTCH file '(.+)/katch/hierarchy.tch'.*")
avg_runtime_pattern = re.compile(".*avg\\. running time \\(including route extraction\\) = ([0-9\\.]+) msec.*")
avg_runtime_pattern_wo_path = re.compile(".*avg\\. running time \\(without route extraction\\)   = ([0-9\\.]+) msec.*")

def parse_katch_query_output(path):
  stats = {}
  with open(path, 'r') as f:
    for line in f:
      match = graph_pattern.match(line)
      if match:
        stats['graph'] = match[1]

      match = avg_runtime_pattern.match(line)
      if match:
        stats['running_time_ms'] = float(match[1])

      match = avg_runtime_pattern_wo_path.match(line)
      if match:
        stats['running_time_wo_path_ms'] = float(match[1])

  return stats

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "/katch/uniform_queries/*.out")
katch_query_stats = pd.DataFrame.from_records([parse_katch_query_output(path) for path in paths])
katch_query_stats.set_index('graph', inplace=True)

runtime_pattern = re.compile(".*Needed (\\d+)musec\\..*")

def parse_tds_contraction_output(path):
  stats = { 'running_time_s': 0.0, 'num_threads': 1 }

  with open(path, 'r') as f:
    for line in f:
      if not 'graph' in stats:
        stats['graph'] = line.strip()
      else:
        match = runtime_pattern.match(line)
        if match:
          stats['running_time_s'] += int(match[1]) / 1000000

  return stats

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "/tds/contraction/*.out")
tds_contraction_stats = pd.DataFrame.from_records([parse_tds_contraction_output(path) for path in paths])
tds_contraction_stats.set_index('graph', inplace=True)

source_node_pattern = re.compile(".*source node : (\\d+).*")
source_time_pattern = re.compile(".*source time \\[ms since midnight\\] : (\\d+).*")
target_node_pattern = re.compile(".*target node : (\\d+).*")
runtime_pattern = re.compile(".*TD-S query running time \\[musec\\] : (\\d+).*")
dijk_runtime_pattern = re.compile(".*Dijkstra running time \\[musec\\] : (\\d+).*")
ground_truth_pattern = re.compile(".*Exact target time \\[ms since midnight\\] : (\\d+).*")
ea_pattern = re.compile(".*TD-S target time \\[ms since midnight\\] : (\\d+).*")

def parse_tds_query_output(path):
  stats = []
  graph = None

  with open(path, 'r') as f:
    for line in f:
      if not graph:
        graph = line.strip()
      else:
        match = source_node_pattern.match(line)
        if match:
          stats.append({ 'graph': graph, 'from': int(match[1]) })

        match = source_time_pattern.match(line)
        if match:
          stats[-1]['departure_time'] = int(match[1]) / 1000

        match = target_node_pattern.match(line)
        if match:
          stats[-1]['to'] = int(match[1])

        match = runtime_pattern.match(line)
        if match:
          stats[-1]['running_time_ms'] = int(match[1]) / 1000

        match = dijk_runtime_pattern.match(line)
        if match:
          stats[-1]['dijkstra_running_time_ms'] = int(match[1]) / 1000

        match = ground_truth_pattern.match(line)
        if match:
          stats[-1]['ground_truth'] = int(match[1]) / 1000

        match = ea_pattern.match(line)
        if match:
          stats[-1]['earliest_arrival'] = int(match[1]) / 1000

  return stats

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "/tds/uniform_queries/*.out")
tds_queries = pd.DataFrame.from_records([run for path in paths for run in parse_tds_query_output(path)])

tds_queries['rel_error'] = (tds_queries['earliest_arrival'] - tds_queries['ground_truth']) / (tds_queries['ground_truth'] - tds_queries['departure_time']) * 100

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "query_stats_all_graphs/*.json")
data = [json.load(open(path)) for path in paths]

tdcch_queries = pd.DataFrame.from_records([{
    'graph': run['args'][1],
    **algo }
    for run in data for algo in run["algo_runs"] if algo['algo'] == "Floating TDCCH Query"])

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "customization_all_graphs/*.json")
data = [json.load(open(path)) for path in paths]

tdcch_customization_stats = pd.DataFrame.from_records([{
    'graph': run['args'][1],
    'num_threads': run['num_threads'],
    'customization_running_time_s': algo['main']['running_time_ms'] / 1000,
    **algo }
    for run in data for algo in run["algo_runs"] if algo['algo'] == "Floating TDCCH Customization"])

runtime_pattern = re.compile(".*running time : (\\d+)musec.*")

def parse_flowcutter_partition_output(path):
  stats = { 'running_time_s': 0.0 }

  with open(path, 'r') as f:
    for line in f:
      if not 'graph' in stats:
        stats['graph'] = line.strip()
      else:
        match = runtime_pattern.match(line)
        if match:
          stats['running_time_s'] += int(match[1]) / 1000000

  return stats

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "/partition/*.out")
tdcch_partition_stats = pd.DataFrame.from_records([parse_flowcutter_partition_output(path) for path in paths])

paths = glob.glob(os.environ['TDCCH_EXP_OUTPUT_DIR'] + "contraction/*.json")
data = [json.load(open(path)) for path in paths]

tdcch_contraction_stats = pd.DataFrame.from_records([{
    'graph': run['args'][1],
    'running_time_s': sum([algo['running_time_ms'] / 1000 for algo in run["algo_runs"] if algo['algo'] == "CCH Contraction"]) }
    for run in data])

def dir_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

katch_prepro_space = pd.Series({ graph[:len(os.environ['TDCCH_GRAPH_DIR'])] + '/' + graph[len(os.environ['TDCCH_GRAPH_DIR']):]: dir_size(graph + 'katch') for graph in glob.glob(os.environ['TDCCH_GRAPH_DIR'] + "/*/day/*/") }) / 1000000000
tds_prepro_space = pd.Series({ graph[:len(os.environ['TDCCH_GRAPH_DIR'])] + '/' + graph[len(os.environ['TDCCH_GRAPH_DIR']):]: dir_size(graph + 'tds') for graph in glob.glob(os.environ['TDCCH_GRAPH_DIR'] + "/*/day/*/") }) / 1000000000
tdcch_prepro_space = pd.Series({ graph[:len(os.environ['TDCCH_GRAPH_DIR'])] + '/' + graph[len(os.environ['TDCCH_GRAPH_DIR']):]: dir_size(graph + 'cch') + dir_size(graph + 'customized') for graph in glob.glob(os.environ['TDCCH_GRAPH_DIR'] + "/*/day/*/") }) / 1000000000

query_time = 'Avg. query time [ms]'
unpack_time = 'Avg. path unpacking time [ms]'
prepro_time = 'Preprocessing time [s (cores)]'
space = 'Index size [GB]'
error = 'Avg. rel. error [\\%]'
max_error = 'Max. rel. error [\\%]'
customization_time = 'Customization time [s (cores)]'
cores = 'Cores'

the_table = pd.DataFrame.from_records([])
the_table['KaTCH', prepro_time] = katch_contraction_stats['running_time_s']
the_table['KaTCH', cores] = katch_contraction_stats['num_threads']
the_table['KaTCH', space] = katch_prepro_space
# the_table['KaTCH', query_time] = katch_query_stats['running_time_ms'].fillna("OOM")
the_table['KaTCH', query_time] = katch_query_stats['running_time_wo_path_ms'].fillna("OOM")
the_table['KaTCH', unpack_time] = (katch_query_stats['running_time_ms'] - katch_query_stats['running_time_wo_path_ms']).fillna("")
the_table['TD-S+9', prepro_time] = tds_contraction_stats['running_time_s']
the_table['TD-S+9', cores] = tds_contraction_stats['num_threads']
the_table['TD-S+9', space] = tds_prepro_space
the_table['TD-S+9', query_time] = tds_queries.groupby('graph')['running_time_ms'].mean()
the_table['TD-S+9', error] = tds_queries.groupby('graph')['rel_error'].mean()
the_table['TD-S+9', max_error] = tds_queries.groupby('graph')['rel_error'].max()
the_table['TD-Dijkstra', query_time] = tds_queries.groupby('graph')['dijkstra_running_time_ms'].mean()
the_table['TD-CCH', prepro_time] = tdcch_partition_stats.groupby('graph')['running_time_s'].mean() + tdcch_contraction_stats.groupby('graph')['running_time_s'].mean() + tdcch_customization_stats.groupby('graph')['customization_running_time_s'].mean()
the_table['TD-CCH', space] = tdcch_prepro_space
the_table['TD-CCH', query_time] = tdcch_queries.groupby('graph')['running_time_ms'].mean()
the_table['TD-CCH', unpack_time] = tdcch_queries.groupby('graph')['unpacking_running_time_ms'].mean()
the_table['TD-CCH', customization_time] = tdcch_customization_stats.groupby('graph')['customization_running_time_s'].mean()
the_table['TD-CCH', cores] = tdcch_customization_stats.groupby('graph')['num_threads'].max()
the_table.columns = pd.MultiIndex.from_tuples(the_table.columns)

rel_work_graph = os.environ['TDCCH_GRAPH_DIR'] + '/de/day/dido/'
tdcalt = 'TDCALT \\cite{dn-crdtd-12}'
the_table.loc[rel_work_graph, (tdcalt, prepro_time)] = 540
the_table.loc[rel_work_graph, (tdcalt, space)] = 0.2344
the_table.loc[rel_work_graph, (tdcalt, query_time)] = 5.36
the_table.loc[rel_work_graph, (tdcalt, cores)] = 1

tdcaltap = 'TDCALT-K1.15 \\cite{dn-crdtd-12}'
the_table.loc[rel_work_graph, (tdcaltap, prepro_time)] = 540
the_table.loc[rel_work_graph, (tdcaltap, space)] = 0.2344
the_table.loc[rel_work_graph, (tdcaltap, query_time)] = 1.87
the_table.loc[rel_work_graph, (tdcaltap, error)] = 0.05
the_table.loc[rel_work_graph, (tdcaltap, max_error)] = 13.84
the_table.loc[rel_work_graph, (tdcaltap, cores)] = 1

lsharc = 'eco L-SHARC \\cite{d-tdsr-11}'
the_table.loc[rel_work_graph, (lsharc, prepro_time)] = 4680
the_table.loc[rel_work_graph, (lsharc, space)] = 1.026672
the_table.loc[rel_work_graph, (lsharc, query_time)] = 6.31
the_table.loc[rel_work_graph, (lsharc, cores)] = 1

heusharc = 'heu SHARC \\cite{d-tdsr-11}'
the_table.loc[rel_work_graph, (heusharc, prepro_time)] = 12360
the_table.loc[rel_work_graph, (heusharc, space)] = 0.642256
the_table.loc[rel_work_graph, (heusharc, query_time)] = 0.69
the_table.loc[rel_work_graph, (heusharc, error)] = 'n/r'
the_table.loc[rel_work_graph, (heusharc, max_error)] = 0.61
the_table.loc[rel_work_graph, (heusharc, cores)] = 1

tch = 'TCH \\cite{bgsv-mtdtt-13}'
the_table.loc[rel_work_graph, (tch, prepro_time)] = 378
the_table.loc[rel_work_graph, (tch, space)] = 4.66456
the_table.loc[rel_work_graph, (tch, query_time)] = 0.75
the_table.loc[rel_work_graph, (tch, cores)] = 8
the_table.loc[rel_work_graph, (tch, customization_time)] = 74

atch = 'ATCH (1.0) \\cite{bgsv-mtdtt-13}'
the_table.loc[rel_work_graph, (atch, prepro_time)] = 378
the_table.loc[rel_work_graph, (atch, space)] = 1.120432
the_table.loc[rel_work_graph, (atch, query_time)] = 1.24
the_table.loc[rel_work_graph, (atch, cores)] = 8
the_table.loc[rel_work_graph, (atch, customization_time)] = 74

atchi = 'ATCH ($\\infty$) \\cite{bgsv-mtdtt-13}'
the_table.loc[rel_work_graph, (atchi, prepro_time)] = 378
the_table.loc[rel_work_graph, (atchi, space)] = 0.553
the_table.loc[rel_work_graph, (atchi, query_time)] = 1.66
the_table.loc[rel_work_graph, (atchi, cores)] = 8
the_table.loc[rel_work_graph, (atchi, customization_time)] = 74

itch01 = 'inex. TCH (0.1) \\cite{bgsv-mtdtt-13}'
the_table.loc[rel_work_graph, (itch01, prepro_time)] = 378
the_table.loc[rel_work_graph, (itch01, space)] = 1.340768
the_table.loc[rel_work_graph, (itch01, query_time)] = 0.7
the_table.loc[rel_work_graph, (itch01, error)] = 0.02
the_table.loc[rel_work_graph, (itch01, max_error)] = 1.0
the_table.loc[rel_work_graph, (itch01, max_error)] = 0.1
the_table.loc[rel_work_graph, (itch01, cores)] = 8
the_table.loc[rel_work_graph, (itch01, customization_time)] = 74

itch10 = 'inex. TCH (1.0) \\cite{bgsv-mtdtt-13}'
the_table.loc[rel_work_graph, (itch10, prepro_time)] = 378
the_table.loc[rel_work_graph, (itch10, space)] = 1.003232
the_table.loc[rel_work_graph, (itch10, query_time)] = 0.69
the_table.loc[rel_work_graph, (itch10, error)] = 0.27
the_table.loc[rel_work_graph, (itch10, max_error)] = 1.01
the_table.loc[rel_work_graph, (itch10, cores)] = 8
the_table.loc[rel_work_graph, (itch10, customization_time)] = 74

tdcrp01 = 'TD-CRP (0.1) \\cite{bdpw-dtdrp-16}'
the_table.loc[rel_work_graph, (tdcrp01, prepro_time)] = 273 + 16
the_table.loc[rel_work_graph, (tdcrp01, customization_time)] = 16
the_table.loc[rel_work_graph, (tdcrp01, space)] = 0.778208
the_table.loc[rel_work_graph, (tdcrp01, query_time)] = 1.92
# the_table.loc[rel_work_graph, (tdcrp01, unpack_time)] = 'n/i'
the_table.loc[rel_work_graph, (tdcrp01, error)] = 0.05
the_table.loc[rel_work_graph, (tdcrp01, max_error)] = 0.25
the_table.loc[rel_work_graph, (tdcrp01, cores)] = 16

tdcrp10 = 'TD-CRP (1.0) \\cite{bdpw-dtdrp-16}'
the_table.loc[rel_work_graph, (tdcrp10, prepro_time)] = 273 + 8
the_table.loc[rel_work_graph, (tdcrp10, customization_time)] = 8
the_table.loc[rel_work_graph, (tdcrp10, space)] = 0.360976
the_table.loc[rel_work_graph, (tdcrp10, query_time)] = 1.66
# the_table.loc[rel_work_graph, (tdcrp10, unpack_time)] = 'n/i'
the_table.loc[rel_work_graph, (tdcrp10, error)] = 0.68
the_table.loc[rel_work_graph, (tdcrp10, max_error)] = 2.85
the_table.loc[rel_work_graph, (tdcrp10, cores)] = 16

flat = 'FLAT \\cite{kppwz-iotdr-17a}'
the_table.loc[rel_work_graph, (flat, prepro_time)] = 158760
the_table.loc[rel_work_graph, (flat, space)] = 54.625875
the_table.loc[rel_work_graph, (flat, query_time)] = 1.269
# the_table.loc[rel_work_graph, (flat, unpack_time)] = 'n/i'
the_table.loc[rel_work_graph, (flat, error)] = 0.01534
the_table.loc[rel_work_graph, (flat, max_error)] = 'n/r'
the_table.loc[rel_work_graph, (flat, cores)] = 6

cflat = 'CFLAT \\cite{kppwz-iotdr-17a}'
the_table.loc[rel_work_graph, (cflat, prepro_time)] = 104220
the_table.loc[rel_work_graph, (cflat, space)] = 34.630256
the_table.loc[rel_work_graph, (cflat, query_time)] = 0.585
# the_table.loc[rel_work_graph, (cflat, unpack_time)] = 'n/r'
the_table.loc[rel_work_graph, (cflat, error)] = 0.0079
the_table.loc[rel_work_graph, (cflat, max_error)] = 0.918
the_table.loc[rel_work_graph, (cflat, cores)] = 6

relevant = ['Ger06', 'Ger17', 'Eur17']

the_table = the_table.stack(0) \
    .loc[[os.environ['TDCCH_GRAPH_DIR'] + graph for graph in ['/de/day/dido/', '/ptv17-de-car/day/di/', '/ptv17-eur-car/day/di/']]] \
    .rename(index={ os.environ['TDCCH_GRAPH_DIR'] + old: new for (old, new) in [('/de/day/dido/', 'Ger06'), ('/ptv17-de-car/day/di/', 'Ger17'), ('/ptv17-eur-car/day/di/', 'Eur17')] }) \
    .reindex(['TD-Dijkstra', tdcalt, tdcaltap, lsharc, heusharc, 'KaTCH', tch, atch, atchi, itch01, itch10, tdcrp01, tdcrp10, flat, cflat, 'TD-S+9', 'TD-CCH'], level=1) \
    .reindex(relevant, level=0)[[cores, prepro_time, space, query_time, unpack_time, error, max_error]]

the_table[query_time] = the_table[query_time] + the_table[unpack_time].fillna(0)

def highlight_max(s):
    '''
    highlight the maximum in a Series yellow.
    '''
    is_max = s == s.max()
    return ['background-color: yellow' if v else '' for v in is_max]

the_table.style.apply(highlight_max)

the_table[cores] = the_table[cores].dropna().astype(int)
the_table[prepro_time] = the_table[prepro_time].dropna().round().astype(int).map('{:.0f}'.format)
the_table[space] = the_table[space].dropna().round(2).map('{:.2f}'.format)
query_column = pd.to_numeric(the_table[query_time], errors='coerce').dropna().round(2).map('{:.2f}'.format)
the_table.loc[query_column.index, query_time] = query_column
# unpack_column = pd.to_numeric(the_table[unpack_time], errors='coerce').dropna().round(2).map('{:.2f}'.format)
# the_table.loc[unpack_column.index, unpack_time] = unpack_column
error_column = (pd.to_numeric(the_table[error], errors='coerce')).dropna().round(3).map('{:.3f}'.format)
the_table.loc[error_column.index, error] = error_column
max_error_column = (pd.to_numeric(the_table[max_error], errors='coerce')).dropna().round(3).map('{:.3f}'.format)
the_table.loc[max_error_column.index, max_error] = max_error_column

prepros = the_table[prepro_time].dropna().index
the_table[space].fillna('-', inplace=True)
the_table[prepro_time].fillna('-', inplace=True)
the_table[cores].fillna('-', inplace=True)
the_table[error].fillna('-', inplace=True)
the_table[max_error].fillna('-', inplace=True)
# the_table[unpack_time].fillna('n/r', inplace=True)

def gen_mapper(col):
    def bold_min(val):
        if pd.to_numeric(val, errors='coerce') == pd.to_numeric(col, errors='coerce').dropna().min():
           return "\\textbf{{{}}}".format(val)
        else:
           return "{}".format(val)
    return bold_min

for graph in relevant:
  for col in [prepro_time, space, query_time]:
    the_table.loc[[graph], col] = the_table.loc[[graph], col].map(gen_mapper(the_table.loc[[graph], col]))

# the_table.loc[prepros, prepro_time] = the_table.loc[prepros, prepro_time].str[:] + the_table.loc[prepros, cores].map('~\\makebox[6mm][r]{{({:.0f})}}'.format)
# the_table.loc[customizations, customization_time] = the_table.loc[customizations, customization_time].str[:] + the_table.loc[customizations, cores].map('~\\makebox[6mm][r]{{({:.0f})}}'.format)

the_table = the_table.reindex(relevant, level=0)[[prepro_time, cores, space, query_time, error, max_error]]

lines = the_table.to_latex(escape=False).split("\n")
lines = [
  '\\begin{tabular}{llrrrrrrrr}',
  R'\toprule'
  R"{} & {} & \multicolumn{2}{c}{Preprocessing} & Index & \multicolumn{3}{c}{Query} \\ \cmidrule(lr){3-4} \cmidrule(lr){6-8}",
  R"{} & {} & Time & Cores & size &    Time & \multicolumn{2}{c}{Rel. error} \\ \cmidrule(lr){7-8}"
  R"{} & {} &  [s] &       & [GB] &    [ms] & Avg. [\%] & Max. [\%] \\"
] + lines[4:]
# lines = lines[:3] + lines[4:]

def maybe_prefix(line):
  if 'Ger17' in line or 'Eur17' in line:
    return "\\addlinespace " + line
  else:
    return line

lines = [maybe_prefix(line) for line in lines]
output = "\n".join(lines) + "\n"
output = output.replace("TD-CCH", R"\textbf{\tdcch{}}")
output = output.replace("Ger06", R"\parbox[t]{3mm}{\multirow{18}{*}{\rotatebox[origin=c]{90}{Ger06}}}")
output = output.replace("Ger17", R"\parbox[t]{3mm}{\multirow{4}{*}{\rotatebox[origin=c]{90}{Ger17}}}")
output = output.replace("Eur17", R"\parbox[t]{3mm}{\multirow{4}{*}{\rotatebox[origin=c]{90}{Eur17}}}")
output = re.sub(re.compile('([0-9]{3}(?=[0-9]))'), '\\g<0>,\\\\', output[::-1])[::-1]

with open("paper/table/related_work.tex", 'w') as f:
  f.write(output)
