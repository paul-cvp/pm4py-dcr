import os
import time
import pm4py
import pandas as pd

from math import sqrt
from copy import deepcopy

from pm4py.algo.discovery.dcr_discover import algorithm as dcr_discover_alg
from pm4py.algo.evaluation.declarative_complexity.algorithm import *
from pm4py.objects.dcr import semantics as dcr_semantics
from pm4py.objects.dcr.hierarchical.util import nested_groups_and_sps_to_flat_dcr


def pdc_f_score(tp, fp, tn, fn):
    try:
        posAcc = tp / (tp + fn)  # TPR - harmonic mean
        negAcc = tn / (tn + fp)  # TNR -
        res = 2 * posAcc * negAcc / (posAcc + negAcc)
        return res
    except:
        return 0


def f_score(tp, fp, tn, fn):
    try:
        recall = tp / (tp + fn)
        prec = tp / (tp + fp)
        res = 2 * recall * prec / (recall + prec)
        return res
    except:
        return 0


def balanced_accuracy(tp, fp, tn, fn):
    try:
        posAcc = tp / (tp + fn)
        negAcc = tn / (tn + fp)
        res = (posAcc + negAcc) / 2
        return res
    except:
        return 0


def mcc(tp, fp, tn, fn):
    try:
        num = tp * tn - fp * fn
        tmp = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
        denom = sqrt(tmp)
        res = num / denom
        return res
    except:
        return 0


def fitness(event_log, dcr_model, cmd_print=False):
    no_traces = len(event_log)
    no_accepting = 0
    for trace in event_log:
        trace_to_print = []
        can_execute = True
        dcr = deepcopy(dcr_model)
        semantics = dcr_semantics.DcrSemantics()
        for event in trace:
            (executed, _) = semantics.execute(event['concept:name'], dcr)
            trace_to_print.append(event['concept:name'])
            if executed is False:
                can_execute = False
                break
        accepting = semantics.is_accepting(dcr)
        if can_execute and accepting:
            no_accepting = no_accepting + 1
        else:
            print(f'[x] Failing trace: {trace_to_print}') if cmd_print else None
    return no_accepting, no_traces


def score_one_model(dcr_model, ground_truth_log):
    gt = ground_truth_log
    gt_cases = pm4py.convert_to_dataframe(gt).groupby('case:concept:name').first()['case:pdc:isPos']
    # test_log = pm4py.convert_to_dataframe(test)
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    for trace in gt:  # the trace is without subprocesses
        gt_is_pos = gt_cases[trace.attributes['concept:name']]
        dcr = nested_groups_and_sps_to_flat_dcr(deepcopy(dcr_model))
        semantics = dcr_semantics.DcrSemantics()
        can_execute = True
        events_so_far = []
        for event in trace:
            # How to project an execution in a subprocess dcr from an event log without them
            (executed, _) = semantics.execute(event['concept:name'],dcr)  # the graph is with subprocesses
            events_so_far.append(event['concept:name'])
            if executed is False:
                # if gt_is_pos:
                # print(f"[!] Failing at: {event['concept:name']}")
                # print(f'[Events so far] {events_so_far}')
                can_execute = False
                break
        accepting = semantics.is_accepting()
        test_is_pos = False
        if can_execute and accepting:
            test_is_pos = True
        if test_is_pos:
            if gt_is_pos:
                tp += 1
            else:
                fp += 1
        else:
            if gt_is_pos:
                fn += 1
            else:
                tn += 1
    print(f'tp: {tp} | fp: {fp} | tn: {tn} | fn: {fn}')
    return tp, fp, tn, fn


def score_everything(logs_name_path_dict, configs=None, create_train_test_split=False):
    if configs is None:
        print('[X] MUST PASS A CONFiG!!!!!!')
        return
    sub_folders = ['Ground Truth Logs', 'Test Logs', 'Training Logs']
    # now just take all .xes files and make sure they match across folders
    temp_results = []
    for l_name, log_path in logs_name_path_dict.items():
        print(f'[i] Started for {l_name}')
        if l_name.startswith('PDC'):
            for log_name in os.listdir(os.path.join(log_path, sub_folders[2])):
                print(f'[i] Log {log_name}')
                # gt = pm4py.read_xes(os.path.join(log_path, sub_folders[0], log_name), return_legacy_log_object=True, show_progress_bar=False)
                # test = pm4py.read_xes(os.path.join(base_dir,folder,sub_folders[1],log_name),return_legacy_log_object=True)

                # if l_name in ['PDC21', 'PDC22']:
                #     specific_log = f'{Path(log_name).stem}{0}.xes'
                #     print(os.path.join(log_path, sub_folders[2], specific_log))
                #     train = pm4py.read_xes(os.path.join(log_path, sub_folders[2], specific_log),
                #                            return_legacy_log_object=True, show_progress_bar=False)
                # else:
                #     print(os.path.join(log_path, sub_folders[2], log_name))
                train = pm4py.read_xes(os.path.join(log_path, sub_folders[2], log_name), return_legacy_log_object=True, show_progress_bar=False)
                i = 0
                for config in configs:
                    if 'alg_name' not in config:
                        config['alg_name'] = f'config {i}'
                        i += 1
                    temp_results.append(score_based_on_config(train, None, config, log_name, alg_name=config['alg_name']))
                    print(f'[i] Done for {log_path}')
        elif create_train_test_split:
            print('[TODO] create_train_test_split')
        else:
            single_log = pm4py.read_xes(log_path, return_legacy_log_object=True, show_progress_bar=False)
            i = 0
            for config in configs:
                if 'alg_name' not in config:
                    config['alg_name'] = f'config {i}'
                    i += 1
                temp_results.append(score_based_on_config(single_log, None, config, l_name, alg_name=config['alg_name']))

    results = pd.DataFrame(
        columns=['Log name', 'Algorithm',
                 'TP', 'FP', 'TN', 'FN', 'F1-PDC', 'F1',
                 'BAC', 'MCC', 'Training Fitness',
                 'Size', 'Density', 'Separability', 'Co-Separability', 'Constraint Variability',
                 '#Relations', '#Nestings', '#InNActivities',
                 '#Activities', 'Runtime'],
        data=temp_results)
    results.to_csv(path_or_buf='/home/vco/Projects/pm4py-dcr/models/results.csv', index=False)
    return results


def train_dcr_model(train, config):
    dcr_model, _ = dcr_discover_alg.apply(train, **config)
    return dcr_model


def get_number_of_edges(dcr):
    relation_count = 0
    rels = ['conditionsFor', 'responseTo', 'includesTo', 'excludesTo']
    for k, e1s in dcr.items():
        if k in rels:
            for e1, e2s in e1s.items():
                relation_count = relation_count + len(e2s)

    return relation_count


def score_based_on_config(train, ground_truth, config, log_name, alg_name='DisCoveR'):
    start_time = time.time()
    dcr = train_dcr_model(train, config)
    elapsed = time.time() - start_time

    size = dcr_size(dcr)
    density = dcr_density(dcr)
    separability = dcr_separability(dcr)
    co_separability = 1 - separability
    constraint_variability = dcr_constraint_variablity_metric(dcr)

    if ground_truth:
        fit = fitness(train, dcr)
        tp, fp, tn, fn = score_one_model(dcr, ground_truth)
        pdcfscore = pdc_f_score(tp, fp, tn, fn)
        fscore = f_score(tp, fp, tn, fn)
        b_acc = balanced_accuracy(tp, fp, tn, fn)
        m_c_c = mcc(tp, fp, tn, fn)
    else:
        fit = ''
        tp = ''
        fp = ''
        tn = ''
        fn = ''
        pdcfscore = ''
        fscore = ''
        b_acc = ''
        m_c_c = ''
    nested_events = 0
    for k, v in dcr['nestings'].items():
        nested_events += len(v)
    return {
        'Log name': log_name,
        'Algorithm': alg_name,
        'TP': tp, 'FP': fp, 'TN': tn, 'FN': fn,
        'F1-PDC': pdcfscore,
        'F1': fscore,
        'BAC': b_acc,
        'MCC': m_c_c,
        'Training Fitness': fit[0] / fit[1] if fit else '',  # fitness is on training
        'Size': size,
        'Density': density,
        'Separability': separability,
        'Co-Separability': 1 - co_separability,
        'Constraint Variability': constraint_variability,
        '#Relations': get_number_of_edges(dcr),
        '#Nestings': len(dcr['nestings']),
        '#InNActivities': nested_events,
        '#Activities': len(dcr['events']),
        'Runtime': elapsed
    }
