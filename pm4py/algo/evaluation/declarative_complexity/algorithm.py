"""
Metrics for declarative models:
https://www.sciencedirect.com/science/article/pii/S0957417423014264
"""

import numpy as np
import networkx as nx

from pm4py.objects.dcr.obj import Relations


def run_all_dcr_metrics(G):
    metrics_dict = {}
    size = len(G['events'])
    for rel in Relations:
        for k, v in G[rel.value].items():
            size += len(v)
    metrics_dict['size'] = size

    nxG = dcr_to_networkx(G)
    comps = [c for c in nx.weakly_connected_components(nxG)]

    largest_cc = max(comps, key=len)
    a_c = len(largest_cc)
    c_c = 0
    for rel in Relations:
        for k, v in G[rel.value].items():
            if k in largest_cc:
                for v0 in v:
                    if v0 in largest_cc:
                        c_c += 1
    metrics_dict['density'] = c_c / a_c

    len_cc = nx.number_weakly_connected_components(nxG)
    metrics_dict['separability'] = len_cc / size

    cv = float('-inf')
    for comp in comps:
        pct, rels_in_comp, comp_c_c = dcr_rel_relative_freq_in_comp(G, comp)
        cv_sum = 0.0
        if comp_c_c > 0:
            for rel in Relations:
                cv_sum += pct[rel.value] * np.emath.logn(rels_in_comp, pct[rel.value])
            neg_sum = - cv_sum
            if neg_sum > cv:
                cv = neg_sum
    metrics_dict['constraint_variability'] = cv

    return metrics_dict


def dcr_size(G):
    size = len(G['events'])
    for rel in Relations:
        for k, v in G[rel.value].items():
            size += len(v)
    return size


def dcr_density(G):
    nxG = dcr_to_networkx(G)
    largest_cc = max(nx.weakly_connected_components(nxG), key=len)
    a_c = len(largest_cc)
    c_c = 0
    for rel in Relations:
        for k, v in G[rel.value].items():
            if k in largest_cc:
                for v0 in v:
                    if v0 in largest_cc:
                        c_c += 1
    return c_c / a_c


def dcr_separability(G):
    nxG = dcr_to_networkx(G)
    len_cc = nx.number_weakly_connected_components(nxG)
    size_g = dcr_size(G)

    return len_cc / size_g


def dcr_co_separability(G):
    return 1 - dcr_separability(G)


def dcr_constraint_variablity_metric(G):
    nxG = dcr_to_networkx(G)
    comps = nx.weakly_connected_components(nxG)
    cv = float('-inf')
    for comp in comps:
        pct, rels_in_comp, comp_c_c = dcr_rel_relative_freq_in_comp(G, comp)
        cv_sum = 0.0
        if comp_c_c > 0:
            for rel in Relations:
                if pct[rel.value] != 0 and np.log(rels_in_comp) != 0:
                    cv_sum += pct[rel.value] * np.emath.logn(rels_in_comp, pct[rel.value])
            neg_sum = - cv_sum
            if neg_sum > cv:
                cv = neg_sum
    return cv


def dcr_to_networkx(G):
    nxG = nx.DiGraph()
    nxG.add_nodes_from(G['events'])
    for rel in Relations:
        for k, v in G[rel.value].items():
            for v0 in v:
                nxG.add_edge(k, v0)
    return nxG


def dcr_rel_relative_freq_in_comp(G, comp):
    comp_c_c = 0
    rel_comp_t_c = {}
    rels_in_comp = 0
    for rel in Relations:
        comp_t_c = 0
        for k, v in G[rel.value].items():
            if k in comp:
                for v0 in v:
                    if v0 in comp:
                        comp_t_c += 1
                        comp_c_c += 1
        if comp_t_c > 0:
            rels_in_comp += 1
        rel_comp_t_c[rel.value] = comp_t_c
    for k, v in rel_comp_t_c.items():
        rel_comp_t_c[k] = v / comp_c_c if comp_c_c > 0 else 0
    return rel_comp_t_c, rels_in_comp, comp_c_c
