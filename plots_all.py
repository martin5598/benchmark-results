#!/usr/bin/env python3
import csv
import decimal
import math
import os
from os import listdir
from os.path import isfile, isdir

import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
#from matplotlib.ticker import ScalarFormatter
import matplotlib.ticker as ticker
import xml.etree.ElementTree as ET
import pandas as pd



#benchmark_set = "smokers"
#file_name_modifier = "_part2"

params = {'legend.fontsize': 'x-large',
          'figure.figsize': (15, 5),
         'axes.labelsize': 'x-large',
         'axes.titlesize':'x-large',
         'xtick.labelsize':'xx-small',
         'ytick.labelsize':'x-large'}
pylab.rcParams.update(params)

class Instance:
    def __init__(self, name):
        self.name = name[:-3]
        self.times = {"compilation": [], "counting": [], "wall": []} 
        self.times_preproc = {"compilation": [], "counting": [], "preprocessing": [], "wall": []} 
        self.timeout_reached = False
        self.memlimit_reached = False
        self.incomplete = False
        self.error_occurred = False

        
    def add_run_stats(self, run):
        comp_t = run.find('.//measure[@name="compilation_time"]')
        count_t = run.find('.//measure[@name="counting_time"]')
        if comp_t == None:
            self.times["compilation"].append(0)
        else: 
            self.times["compilation"].append(float(comp_t.get('val')))
        if count_t == None:
            self.times["counting"].append(0)
        else: 
            self.times["counting"].append(float(count_t.get('val')))
        self.times["wall"].append(float(run.find('.//measure[@name="wall"]').get('val')))
    
    def add_run_stats_preproc(self, run):
        comp_t = run.find('.//measure[@name="compilation_time"]')
        count_t = run.find('.//measure[@name="counting_time"]')
        if comp_t == None:
            self.times_preproc["compilation"].append(0)
        else: 
            self.times_preproc["compilation"].append(float(comp_t.get('val')))
        if count_t == None:
            self.times_preproc["counting"].append(0)
        else: 
            self.times_preproc["counting"].append(float(count_t.get('val')))
        self.times_preproc["wall"].append(float(run.find('.//measure[@name="wall"]').get('val')))
        #print(run.find('.//measure[@name="instance"]').get('val'))
        self.times_preproc["preprocessing"].append(float(run.find('.//measure[@name="preprocessing_time"]').get('val')))
    
    def add_run_stats1(self, compilation_time, counting_time, wall):
        self.times["compilation"].append(compilation_time)
        self.times["counting"].append(counting_time)
        self.times["wall"].append(wall)
    def add_run_stats_preproc1(self, preprocessing_time, compilation_time, counting_time, wall):
        self.times_preproc["compilation"].append(compilation_time)
        self.times_preproc["counting"].append(counting_time)
        self.times_preproc["preprocessing"].append(preprocessing_time)
        self.times_preproc["wall"].append(wall)
    
    def has_enough_values(self):
        print(self.name + ": " + str(len(self.times["wall"])) + ", " + str(len(self.times_preproc["wall"])))
        return len(self.times["wall"]) >= 2 and len(self.times_preproc["wall"]) >= 2
        
    def get_avg_time(self, key):
        #print("avg time " + self.name + ": " + str(np.mean(self.times[key])) + " (" + key + ")")
        return np.mean(self.times[key])
    def get_avg_time_preproc(self, key):
        return np.mean(self.times_preproc[key])        
    def get_csv_row(self):
        return [self.name, str(self.times["wall"]), str(self.times["compilation"]), str(self.times["counting"]), 
        str(self.times_preproc["wall"]), str(self.times_preproc["preprocessing"]), str(self.times_preproc["compilation"]), str(self.times_preproc["counting"])]


settings_stats = []
instances_filtered = []

for benchmark_set in ["blood", "blood_maxtimes", "gh", "gh_maxtimes", "gnb", "gnb_maxtimes", "simple_paths", "smokers"]:
    instances = {}
    results_file = "XML/results_" + benchmark_set + ".xml"
    tree = ET.parse(results_file)
    root = tree.getroot()

    timeout = root.find('pbsjob').get('timeout')

    settings_stats.append(("arguments", root.find('system').find('.//setting[@name="problog"]').get('cmdline')))
    settings_stats.append(("timeout", timeout))
    settings_stats.append(("memory limit", root.find('machine').get('memory')))

    for inst in root.find('benchmark')[0]:
        instances[inst.get('id')] = Instance(inst.get('name'))

    for spec in root.find('project').findall('runspec'):
        for inst in spec[0]:
            for run in inst:
                time = run.find('.//measure[@name="time"]').get('val') # time encodes the errors for some reason
                if time == timeout:
                    instances[inst.get('id')].timeout_reached = True
                elif time == str(int(timeout)+4):
                    instances[inst.get('id')].memlimit_reached = True
                elif time == str(int(timeout)+5):
                    instances[inst.get('id')].incomplete = True
                elif time == str(int(timeout)+1):
                    instances[inst.get('id')].error_occurred = True
                elif time != str(int(timeout)+6):
                    if spec.get('setting') == "problog":
                        instances[inst.get('id')].add_run_stats(run)
                    elif spec.get('setting') == "problog_preprocessing":
                        instances[inst.get('id')].add_run_stats_preproc(run)
                else:
                    print("warning: missing values in run " + run.get('number') + " of instance " + run.find('.//measure[@name="instance"]').get('val'))
    
    instances_filtered.extend(filter(lambda x: x.has_enough_values(), instances.values()))
#settings_stats.append(("instances with timeout reached", str(len(list(filter(lambda x: x.timeout_reached, instances.values()))))))
#settings_stats.append(("instances with memory limit reached", str(len(list(filter(lambda x: x.memlimit_reached, instances.values()))))))
#settings_stats.append(("instances with errors", str(len(list(filter(lambda x: x.error_occurred, instances.values()))))))
#settings_stats.append(("incomplete instances", str(len(list(filter(lambda x: x.incomplete, instances.values()))))))

#print(len(instances))



x = np.array([inst.get_avg_time("wall") for inst in instances_filtered])
y = np.array([(inst.get_avg_time_preproc("wall") - inst.get_avg_time("wall")) * 100 / inst.get_avg_time("wall") for inst in instances_filtered])

ax = plt.gca()
ax.scatter(x, y, s=3)

ax.set_xscale('log')
#ax.xaxis.set_major_formatter(ScalarFormatter())
plt.axhline(y=0, color='r', linestyle='-', linewidth=1)

plt.xlabel('wall time [s]')
plt.ylabel('wall time after preprocessing [%]')

plt.ylim([-100,1200])

ax.yaxis.set_major_locator(ticker.MultipleLocator(100))
plt.xticks(fontsize=9)
plt.tight_layout()

plt.savefig('output/plots/all_scatter.png')



