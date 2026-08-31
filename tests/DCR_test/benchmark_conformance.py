import time

import pm4py
import os
import pandas as pd
from pm4py.discovery import discover_dcr, discover_declare
from pm4py.objects.log.obj import EventLog, Event, Trace
from tests.DCR_test.benchmark_util.conformance_sepsis import benchmark_conformance_sepsis, benchmark_conformance_sepsis_declare
from tests.DCR_test.benchmark_util.conformance_ground_truth import conformance_ground_truth
from shutil import rmtree
from zipfile import ZipFile
from collections import Counter


import matplotlib.pyplot as plt

def get_files(path, folder):
    extract_path = os.path.join(path,folder)
    with ZipFile(extract_path+".zip", 'r') as zipObj:
        zipObj.extractall(extract_path)

def remove_files(path, folder):
    extract_path = os.path.join(path, folder)
    rmtree(extract_path)


def generate_log_using_petri_net(path, log, log_configuration, trace_configuration):
    # petri met to produce synthetic log for
    from pm4py.algo.simulation.playout.petri_net.variants.basic_playout import apply_playout
    print(os.path.join(path,log))
    log = pm4py.read_xes(os.path.join(path,log))
    net, im, fm = pm4py.discover_petri_net_alpha(log)
    for i in log_configuration:
        for j in trace_configuration:
            log = apply_playout(net, im, i, j)
            path = os.path.join(path,path+"_"+str(i)+"_"+str(j)+".xes")
            pm4py.write_xes(log,path)

def export_graph(graph, path, name):
    from pm4py.objects.dcr.exporter.exporter import DCR_JS_PORTAL
    print(os.path.join(path))
    pm4py.write_dcr_xml(dcr_graph=graph,path=os.path.join(path,name+".xml"),variant=DCR_JS_PORTAL,dcr_title=name)

def import_graph(path,name):
    from pm4py.objects.dcr.importer.importer import XML_DCR_PORTAL
    graph = pm4py.read_dcr_xml(file_path=os.path.join(path,name+".xml"),variant=XML_DCR_PORTAL)
    return graph


def sepsis(name):
    print("running sepsis with synthetic logs")
    # to generate synthetic sepsis logs
    configuration_trace_len = [10, 20, 30, 40, 50]
    max_trace = [25000, 50000, 75000, 100000]
    path = "sepsis"
    import_log = "Sepsis Cases - Event Log.xes"
    #generate_log_using_petri_net(path, import_log, max_trace, configuration_trace_len)

    # specify test files
    res_file = "results/"+name+".csv"
    training_log_path = "Sepsis Cases - Event Log.xes"
    training_log = pm4py.read_xes(os.path.join("sepsis", training_log_path))
    graph, _ = discover_dcr(training_log)
    for test_file in os.listdir("sepsis"):
        if test_file == training_log_path:
            continue
        test_log = pm4py.read_xes(os.path.join("sepsis", test_file), return_legacy_log_object=True)
        benchmark_conformance_sepsis(graph, test_log, res_file, 10)

def sepsis_declare():
    print("running sepsis with synthetic logs for declare")

    # specify test files
    res_file = "results/sepsis_run_times_declare.csv"
    training_log_path = "Sepsis Cases - Event Log.xes"
    training_log = pm4py.read_xes(os.path.join("sepsis", training_log_path))
    model = discover_declare(training_log)
    no = 0
    for test_file in os.listdir("sepsis"):
        if test_file == training_log_path:
            continue
        test_log = pm4py.read_xes(os.path.join("sepsis", test_file), return_legacy_log_object=True)
        benchmark_conformance_sepsis_declare(model, test_log, res_file, 10)

def traffic_management():
    path = "Road_Traffic_Fine_Management_Process"
    import_log = "Road_Traffic_Fine_Management_Process.xes"

    log = pm4py.read_xes(os.path.join("../input_data", "roadtraffic100traces.xes"))
    graph, _ = pm4py.discover_dcr(log)
    print(graph)
    name_of_xml = "road_traffic"
    #export for visualization and analysis of control flow
    export_graph(graph, path, name_of_xml)
    log = pm4py.read_xes(os.path.join(path, import_log))
    graph, _ = pm4py.discover_dcr(log)
    cases = log['case:concept:name'].unique()
    print("running")
    # create a data frame dictionary to store your data frames
    i = 0
    for elem in cases:
        trace = log[log['case:concept:name'] == elem]
        print(trace['concept:name'])
        """
        start = time.perf_counter()
        conf_res = pm4py.conformance_dcr(trace, graph)
        end = (time.perf_counter() - start) * 1000
        print(end)
        print(conf_res)
        """

if __name__ == "__main__":
    sepsis("new test")
    #sepsis_declare()
    #traffic_management()

