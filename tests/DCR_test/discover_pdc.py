from shutil import rmtree

import pm4py
import pandas as pd
import time
import os

from pm4py.algo.discovery.dcr_discover.variants.dcr_discover import apply
from zipfile import ZipFile

def get_files(path, folder):
    extract_path = os.path.join(path,folder)
    with ZipFile(extract_path+".zip", 'r') as zipObj:
        zipObj.extractall(extract_path)

def remove_files(path, folder):
    extract_path = os.path.join(path, folder)
    rmtree(extract_path)

def benchmark_discover_run_time_2019(test_path: str,training_logs, repeat: int):
    log_path = os.path.join(test_path,training_logs)

    final_times = []
    graphs = []
    for file in os.listdir(log_path):
        # reset accumalating variables
        times = []
        no_event = []
        no_of_act = []

        log = pm4py.read_xes(os.path.join(log_path,file))
        add = pd.date_range('2018-04-09', periods=len(log), freq='20min')
        log['time:timestamp'] = add
        for i in range(repeat):
            start = time.perf_counter()
            graph, _ = apply(log)

            if i == 0:
                graphs.append(graph)

            times.append((time.perf_counter() - start)*1000)
            #append time values and no_of_act per trace
            no_of_act.append(len(set(log['concept:name'])))

        final_time = (sum(times) / repeat)
        print("result from test: " + file + ": " + str(final_time) + " ms")
        print("length of event log: " + str(len(log)))
        # print("number of actitivies: " + str(len(set(training_log['concept:name']))))
        #append number of event, size of log
        no_event.append(len(log))
        final_times.append(final_time)
        temp = {"process": [file], "avg_time": [final_time], "no events": [len(log)]}
        data = pd.DataFrame(temp)

        if os.path.isfile("results/"+str(test_path)+" run time.csv"):
            data.to_csv("results/"+str(test_path)+" run time.csv", sep=";", mode="a", header=False,
                        index=False)
        else:
            data.to_csv("results/"+str(test_path)+" run time.csv", sep=";", index=False)

    return graphs


def test_ground_truth_compliance(graphs, test_path, test_log_path, gt_log_path):
    from pm4py.algo.evaluation.compliance.variants.confusion_matrix import ComplianceChecker
    ct = ComplianceChecker()
    ct_values = None

    log_test_path = os.path.join(test_path,test_log_path)
    log_gt_path = os.path.join(test_path, gt_log_path)
    for graph, test_file, gt_file in zip(graphs, os.listdir(log_test_path), os.listdir(log_gt_path)):
        test_log = pm4py.read_xes(os.path.join(log_test_path,test_file),return_legacy_log_object=True)
        gt_log = pm4py.read_xes(os.path.join(log_gt_path, gt_file), return_legacy_log_object=True)

        # call the compliance checker for traces
        ct_values = ct.compliant_traces(graph, test_log, gt_log)
        com = ComplianceChecker()
        # for individual traces
        res = com.compliant_traces(graph,test_log,gt_log)
        f = res.get_classification_values()
        print(test_file+" has "+" tp: "+str(f[0])+" fp: "+str(f[1])+" tn: "+str(f[2])+" fn: "+str(f[3]))

    print(ct_values.get_classification_values())
    print("collective binary classification results:")
    print("positive precision: " + str(round(ct_values.compute_positive_precision(), 2)))
    print("negative precision: " + str(round(ct_values.compute_negative_precision(), 2)))
    print("positive recall: " + str(round(ct_values.compute_positive_recall(), 2)))
    print("negative recall: " + str(round(ct_values.compute_negative_recall(), 2)))
    print("positive f_1 score: " + str(round(ct_values.get_positive_f_score(), 2)))
    print("negative f_1 score: " + str(round(ct_values.get_negative_f_score(), 2)))
    print("accuracy: " + str(round(ct_values.compute_accuracy() * 100, 1)))
    print("mcc: " + str(round(ct_values.mcc(), 2)))

def initiate_run_time_test(test_path:str, repeat: int):
    training_logs = "Training Logs"
    test_logs = "Test Logs"
    ground_truth_log = "Ground Truth Logs"

    get_files(test_path, training_logs)

    graphs = benchmark_discover_run_time_2019(test_path,training_logs,repeat)
    remove_files(test_path, training_logs)

    get_files(test_path, test_logs)
    get_files(test_path, ground_truth_log)

    test_ground_truth_compliance(graphs,test_path,test_logs, ground_truth_log)

    remove_files(test_path, test_logs)
    remove_files(test_path, ground_truth_log)



if __name__ == "__main__":
    #the folder to test
    pdc_test = "pdc_2019"


    #repeat the discover algo # of times
    repeat = 10

    #instantiate test
    initiate_run_time_test(pdc_test, repeat)