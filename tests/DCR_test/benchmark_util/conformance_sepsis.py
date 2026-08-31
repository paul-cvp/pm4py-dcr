
import os
import pandas as pd
import time
from pm4py.algo.conformance.dcr.variants.classic import apply
from pm4py.algo.conformance.declare.variants.classic import apply as declare_apply


def write_csv(temp, res_file):
    data = pd.DataFrame(temp)
    if os.path.isfile(res_file):
        data.to_csv(res_file, sep=",", mode="a", header=False,
                    index=False)
    else:
        data.to_csv(res_file, sep=";", index=False)

def benchmark_conformance_sepsis(graph, test_log, res_file, repeat):
    times = []

    no_traces = 0
    trace_len = len(test_log[0])
    for i in range(repeat):
        start = time.perf_counter()
        res = apply(test_log, graph)
        end = (time.perf_counter() - start) * 1000
        times.append(end)
        print(end)
        no_traces = len(res)

    temp = {"avg_run_time": [(sum(times) / len(times))], "no_traces": [no_traces], "trace_len": [trace_len]}
    write_csv(temp, res_file)

def benchmark_conformance_sepsis_declare(model, test_log, res_file, repeat):
    times = []

    no_traces = 0
    trace_len = len(test_log[0])
    for i in range(repeat):
        start = time.perf_counter()
        res = declare_apply(test_log, model)
        end = (time.perf_counter() - start) * 1000
        times.append(end)
        print(end)
        no_traces = len(res)

    temp = {"avg_run_time": [(sum(times) / len(times))], "no_traces": [no_traces], "trace_len": [trace_len]}
    write_csv(temp, res_file)