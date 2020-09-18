"""

import pandas as pd
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter

log_csv = pd.read_csv('15CASI-3EVAL_noquote.csv', sep=',')
log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: 'NEWCASEID'}
log_csv = log_csv.sort_values('TIMESTAMP')
event_log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)

"""


from pm4py.objects.log.importer.xes import factory as xes_importer
import os
log_path = os.path.join("15casi_corretto.xes")
log = xes_importer.apply(log_path)


from pm4py.algo.filtering.log.attributes import attributes_filter
activities = attributes_filter.get_attribute_values(log, "concept:name")

from pm4py.algo.discovery.heuristics import factory as heuristics_miner
heu_net = heuristics_miner.apply_heu(log)


def get_resource(activity):
    for trace in log:
        for event in trace:
            if event["concept:name"] == activity:
                return event["RESOURCE"][:-1]

"""
for node in heu_net.nodes:
    print (node)
"""

dep_list = []

for activity in heu_net.dependency_matrix:
    for act in heu_net.dependency_matrix[activity].keys():
        dependency = "{}({}) -> {}({}) = {}".format(activity, get_resource(activity), act, get_resource(act), heu_net.dependency_matrix[activity][act])
        dep_list.append([activity, get_resource(activity), act, get_resource(act), heu_net.dependency_matrix[activity][act]])

for dep in dep_list:
    print(dep)


ccs = []

for dep in dep_list:
    #creazione di tutti i commit
    #cancella dep[1] != dep[3] per avere commit della stessa persona
    if  dep[4] >= 0.8:
        ccs.append([dep[1], dep[3], dep[0], dep[2]])
            
print("\nCOMMITMENTS:\n")
for cc in ccs:
    print(cc)

#creazione dei commit con OR
add_ccs = []

for cc1 in ccs:
    for cc2 in ccs:
        if cc1 != cc2 and cc1[2] == cc2[2] and cc1[3] != cc2[3]:
            add_ccs.append([cc1[0], cc1[1], cc1[2], "(" + cc1[3] + " V " + cc2[3] + ")"])
            if cc1 in ccs:
                ccs.remove(cc1)
            if cc2 in ccs:
                ccs.remove(cc2)

for cc in add_ccs:
    ccs.append(cc)

#concatenazione dei commit
for i in range(3):
    for cc1 in ccs:
        for cc2 in ccs:
            if cc1[3][-5] == cc2[2][-5] and cc1[0] != cc2[1]:
                cc2[0] = cc1[0]
                cc2[2] = cc1[2] + " . " + cc1[3]
                ccs.remove(cc1)

#aggiunta del precedente all'antecedente
for cc in ccs:
    cc[3] = cc[2] + " . " + cc[3]

print("\nFINAL COMMITMENTS:\n")
for cc in ccs:
    print(cc)
