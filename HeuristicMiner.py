import pandas as pd
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter

log_csv = pd.read_csv('totale.csv', sep=',')
log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
log_csv = log_csv.sort_values('TIMESTAMP')
log_csv.rename(columns={'ACTIVITY': 'concept:name'}, inplace=True)
parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: 'NEWCASEID'}
log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)


from pm4py.algo.discovery.heuristics import factory as heuristics_miner
heu_net = heuristics_miner.apply_heu(log)

#visualization of the heuristic net
# from pm4py.visualization.heuristics_net import visualizer as hn_visualizer
# gviz = hn_visualizer.apply(heu_net)
# hn_visualizer.view(gviz)

#obtaining resource of an activity
def get_resource(activity):
    for trace in log:
        for event in trace:
            if event["concept:name"] == activity:
                return event["RESOURCE"].strip()

#creating the list of the dependencies of the activities with the correspondent resources
dep_list = []
for activity in heu_net.dependency_matrix:
    for act in heu_net.dependency_matrix[activity].keys():
        dep_list.append([activity.strip(), get_resource(activity), act.strip(), get_resource(act), heu_net.dependency_matrix[activity][act]])
        #dependency = (activity1, resource1, activity2, resource2)

print("\n\n DEPENDENCIES:")
for dep in dep_list:
    print(dep)

#calculate the number of total final activities
number_of_final_activities = 0
for key in heu_net.end_activities[0].keys():
    number_of_final_activities += heu_net.end_activities[0][key]

#used to check if an activity is not in more than 5% of the finals ones
def check_not_final(activity):
    if activity in heu_net.end_activities[0].keys():
        if (heu_net.end_activities[0][activity] / number_of_final_activities * 100) > 5:
            print("percentage of",activity, "=",  heu_net.end_activities[0][activity] / number_of_final_activities * 100)
            return False
    return True

#creation of all the basics commitments
#note that debtor and creditor, for now, can be the same
ccs = []
for dep in dep_list:
    if  dep[4] > 0.8 and check_not_final(dep[0]):
        ccs.append([dep[3], dep[1], dep[0], dep[2]])
        #cc(debtor, creditor, antecedent, consequent)

print("\nCOMMITMENTS:")
for cc in ccs:
    print(cc)


#union of comitments with OR
add_ccs = []
for cc1 in ccs:
    for cc2 in ccs:
        if cc1 != cc2 and cc1[2] == cc2[2] and cc1[3] != cc2[3]:
        #antecedent equal but consequent different
            add_ccs.append([cc1[0], cc1[1], cc1[2], "(" + cc1[3] + " V " + cc2[3] + ")"])
            ccs.remove(cc1)
            ccs.remove(cc2)

for cc in add_ccs:
    ccs.append(cc)

print("\nCOMMITMENTS WITH OR:")
for cc in ccs:
    print(cc)


#concatenation of commitments
#the range is the maximum length of a concatenation
for i in range(5):
    for cc1 in ccs:
        for cc2 in ccs:
            if cc1 != cc2 and cc1[3] == cc2[2] and cc1[1] != cc2[0]: #checking also that creditor of cc1 and debtor of cc2 are not the same
                if cc2[0] == cc1[0]: #making sure that no activities of the debtor will be in the antecedent
                    cc1[3] = cc1[3] + " . " + cc2[3] #putting those activities in the consequent instead
                    ccs.remove(cc2)
                else: #putting the activities in the antecedent
                    cc2[1] = cc1[1]
                    cc2[2] = cc1[2] + " . " + cc2[2]
                    ccs.remove(cc1)

print("\nCOMMITMENTS CONCATENATED:")
for cc in ccs:
    print(cc)

#adding the antecedent to the consequent
for cc in ccs:
    cc[3] = cc[2] + " . " + cc[3]

#removing commitments where debtor is creditor too
for cc in ccs:
    if cc[0] == cc[1]:
        ccs.remove(cc)

print("\nFINAL COMMITMENTS:")
for cc in ccs:
    print(cc)
