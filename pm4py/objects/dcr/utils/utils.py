import re

from pandas import Timedelta

from pm4py.objects.dcr.hierarchical.obj import HierarchicalDcrGraph
from pm4py.objects.dcr.obj import DcrGraph, TemplateRelations, Relations, dcr_template
from copy import deepcopy

from pm4py.objects.dcr.timed.obj import TimedDcrGraph


def time_to_iso_string(time, time_precision='D'):
    '''

    Parameters
    ----------
    time
    time_precision: valid values are D H M S

    Returns
    -------

    '''
    if not isinstance(time,Timedelta):
        time = Timedelta(time)
    iso_time = time.floor(freq='s').isoformat()
    if time_precision:
        iso_time = iso_time.split(time_precision)[0] + time_precision
    return iso_time

def clean_input(graph: DcrGraph, white_space_replacement=None, all=False):
    pattern = '[^0-9a-zA-Z_]+'
    if white_space_replacement is None:
        return graph
        #white_space_replacement = ' '
    # remove all space characters and put conditions and milestones in the correct order (according to the actual arrows)
    # for k, v in deepcopy(dcr).items():
    for k in [r.value for r in Relations]:
        if hasattr(graph, k):
            v_new = {}
            for k2, v2 in graph.__getattribute__(k).items():
                v_new[re.sub(pattern, '', k2.strip()).replace(' ', white_space_replacement)] = set(
                    [re.sub(pattern, '', v3.strip()).replace(' ', white_space_replacement) for v3 in v2])
            graph.__setattr__(k, v_new)

    for k in ['timedconditions', 'timedresponses']:
        if hasattr(graph, k):
            v_new = {}
            for k2, v2 in graph.__getattribute__(k).items():
                v_new[re.sub(pattern, '', k2.strip()).replace(' ', white_space_replacement)] = {
                    re.sub(pattern, '', v3.strip()).replace(' ', white_space_replacement): d for v3, d in v2.items()}
            graph.__setattr__(k, v_new)

    for k2 in ['executed', 'included', 'pending']:
        if hasattr(graph.marking, k2):
            new_v = set([re.sub(pattern, '', v2.strip()).replace(' ', white_space_replacement) for v2 in graph.marking.__getattribute__(k2)])
            graph.marking.__setattr__(k2, new_v)

    for k in ['subprocesses', 'nestedgroups', 'role_assignments', 'principals_assignments']:
        if hasattr(graph, k):
            v_new = {}
            for k2, v2 in graph.__getattribute__(k).items():
                v_new[re.sub(pattern, '', k2.strip()).replace(' ', white_space_replacement)] = set(
                    [re.sub(pattern, '', v3.strip()).replace(' ', white_space_replacement) for v3 in v2])
            graph.__setattr__(k, v_new)

    k = 'nestedgroups_map'
    if hasattr(graph, k):
        v_new = {}
        for k2, v2 in graph.__getattribute__(k).items():
            v_new[re.sub(pattern, '', k2.strip()).replace(' ', white_space_replacement)] = v2.strip().replace(' ', white_space_replacement)
        graph.__setattr__(k, v_new)

    k = 'label_map'
    if hasattr(graph, k):
        v_new = {}
        for k2, v2 in graph.__getattribute__(k).items():
            if all:
                v_new[re.sub(pattern, '', k2.strip()).replace(' ', white_space_replacement)] = v2.strip().replace(' ', white_space_replacement)
            else:
                v_new[re.sub(pattern, '', k2.strip()).replace(' ', white_space_replacement)] = v2
        graph.__setattr__(k, v_new)
    # these are just sets
    remaining_k = ['events', 'roles', 'principals']
    if all:
        remaining_k.append('labels')
    for k in remaining_k:
        if hasattr(graph, k):
            new_v = set([re.sub(pattern, '', v2.strip()).replace(' ', white_space_replacement) for v2 in graph.__getattribute__(k)])
            graph.__setattr__(k, new_v)
    #TODO for any other k
    # new_v = set([re.sub(pattern, '', v2.strip()).replace(' ', white_space_replacement) for v2 in graph.__getattribute__(k)])
    # graph.__setattr__(k, new_v)

    return graph


def clean_input_as_dict(dcr, white_space_replacement=None):
    if white_space_replacement is None:
        white_space_replacement = ' '
    # remove all space characters and put conditions and milestones in the correct order (according to the actual arrows)
    for k, v in deepcopy(dcr).items():
        if k in [tr.value for tr in TemplateRelations]:
            v_new = {}
            for k2, v2 in v.items():
                v_new[k2.strip().replace(' ', white_space_replacement)] = set(
                    [v3.strip().replace(' ', white_space_replacement) for v3 in v2])
            dcr[k] = v_new
        elif k in ['conditionsForDelays', 'responseToDeadlines']:
            v_new = {}
            for k2, v2 in v.items():
                v_new[k2.strip().replace(' ', white_space_replacement)] = {
                    v3.strip().replace(' ', white_space_replacement): d for v3, d in v2.items()}
            dcr[k] = v_new
        elif k == 'marking':
            for k2 in ['executed', 'included', 'pending']:
                new_v = set([v2.strip().replace(' ', white_space_replacement) for v2 in dcr[k][k2]])
                dcr[k][k2] = new_v
        elif k in ['subprocesses', 'nestedgroups', 'roleAssignments', 'readRoleAssignments', 'principalsAssignments']:
            v_new = {}
            for k2, v2 in v.items():
                v_new[k2.strip().replace(' ', white_space_replacement)] = set(
                    [v3.strip().replace(' ', white_space_replacement) for v3 in v2])
            dcr[k] = v_new
        elif k in ['labelMapping']:
            v_new = {}
            for k2, v2 in v.items():
                v_new[k2.strip().replace(' ', white_space_replacement)] = v2.strip().replace(' ', white_space_replacement)
            dcr[k] = v_new
        else:
            new_v = set([v2.strip().replace(' ', white_space_replacement) for v2 in dcr[k]])
            dcr[k] = new_v
    return dcr


def map_labels_to_events(graph):
    '''
    Events, ids are unique (and are often derived from the concept:name attribute)
    Labels or activities are not unique (in general do not have an equivalent in event log nomenclature). Many events or ids can map to an activity or label.
    At most one label/activity for an event/id.
    In Dcr Discovery algorithms usually 1 event/id = 1 label/activity. So we can simplify the mapping.
    '''
    is_dcr_object = isinstance(graph, DcrGraph)
    if is_dcr_object:
        dcr = graph.obj_to_template()
    else:
        dcr = graph
    id_to_label = dcr['labelMapping']
    dcr_res = deepcopy(dcr_template)
    new_label_map = {v:v for k,v in id_to_label.items()}
    for k, v in dcr.items():
        if k in id_to_label:
            k = id_to_label[k]
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if k2 in id_to_label:
                    k2 = id_to_label[k2]
                if isinstance(v2, dict):
                    for k22, v22 in v2.items():
                        if k22 in id_to_label:
                            k22 = id_to_label[k22]
                        if isinstance(v22, dict):
                            for k3, v3 in v22.items():
                                if k3 in id_to_label:
                                    k3 = id_to_label[k3]
                                dcr_res[k][k2][k3] = v3
                        elif k in ['conditionsForDelays', 'responseToDeadlines']:
                            dcr_res[k][k2] = {id_to_label[i0]: i1 for i0, i1 in v2.items()}
                        elif k2 == 'pendingDeadline':
                            dcr_res[k][k2][k22] = v22
                        else:
                            dcr_res[k][k2][k22] = set([id_to_label[i] for i in v22])

                elif k not in ['labelMapping']:
                    dcr_res[k][k2] = set([id_to_label[i] for i in v2])

        else:
            if k not in ['labels', 'roles']:
                dcr_res[k] = set([id_to_label[i] for i in v])
    dcr_res['labelMapping'] = new_label_map
    if is_dcr_object:
        return cast_to_dcr_object(dcr_res)
    else:
        return dcr_res


def cast_to_dcr_object(dcr):
    if len(dcr['conditionsForDelays']) > 0 or len(dcr['responseToDeadlines']) > 0:
        from pm4py.objects.dcr.timed.obj import TimedDcrGraph
        return TimedDcrGraph(dcr)
    elif len(dcr['subprocesses']) > 0 or len(dcr['nestedgroups']) > 0:
        from pm4py.objects.dcr.hierarchical.obj import HierarchicalDcrGraph
        return HierarchicalDcrGraph(dcr)
    elif len(dcr['noResponseTo']) > 0 or len(dcr['milestonesFor']):
        from pm4py.objects.dcr.extended.obj import ExtendedDcrGraph
        return ExtendedDcrGraph(dcr)
    elif len(dcr['roles']) > 0:
        from pm4py.objects.dcr.distributed.obj import DistributedDcrGraph
        return DistributedDcrGraph(dcr)
    else:
        return DcrGraph(dcr)


def time_to_int(graph: TimedDcrGraph, precision='days', inplace=False):
    if not inplace:
        graph = deepcopy(graph)
    for k in ['timedconditions', 'timedresponses']:
        if hasattr(graph, k):
            v = graph.__getattribute__(k)
            v_new = {}
            for k2, v2 in v.items():
                v_new[k2] = {}
                for v3, duration in v2.items():
                    try:
                        total_seconds = duration.total_seconds()
                        hours = int(total_seconds / 3600)
                        minutes = int(total_seconds / 60)
                        days = int(hours / 24)
                        if precision == 'hours':
                            v_new[k2][v3] = hours
                        elif precision == 'minutes':
                            v_new[k2][v3] = minutes
                        elif precision == 'seconds':
                            v_new[k2][v3] = int(total_seconds)
                        elif precision == 'days':
                            v_new[k2][v3] = days
                    except:
                        pass
            graph.__setattr__(k, v_new)
    if not inplace:
        return graph


def get_reverse_nesting(graph: HierarchicalDcrGraph):
    reverse_nesting = {}
    for k, v in graph.nestedgroups_map.items():
        if v not in reverse_nesting:
            reverse_nesting[v] = set()
        reverse_nesting[v].add(k)
    return reverse_nesting


def nested_groups_and_sps_to_flat_dcr(graph: HierarchicalDcrGraph) -> DcrGraph:
    graph.nestedgroups = {**graph.nestedgroups, **graph.subprocesses}
    for group, events in graph.subprocesses.items():
        for e in events:
            graph.nestedgroupsmap[e] = group
    graph.subprocesses = {}

    if len(graph.nestedgroups) == 0:
        return graph

    reverse_nesting = get_reverse_nesting(graph)
    all_atomic_events = set()
    nesting_top = {}
    for event in graph.events:
        atomic_events = set()

        def find_lowest(e):
            if e in reverse_nesting:
                for nested_event in reverse_nesting[e]:
                    if nested_event in reverse_nesting:
                        find_lowest(nested_event)
                    else:
                        atomic_events.add(nested_event)
            else:
                atomic_events.add(e)

        find_lowest(event)
        all_atomic_events = all_atomic_events.union(atomic_events)
        if event in graph.nestedgroups.keys():
            nesting_top[event] = atomic_events

    for nest, atomic_events in nesting_top.items():
        for r in Relations:
            k0 = r.value
            if nest in graph.__getattribute__(k0):
                for ae in atomic_events:
                    if ae not in graph.__getattribute__(k0):
                        graph.__getattribute__(k0)[ae] = set()
                    graph.__getattribute__(k0)[ae] = graph.__getattribute__(k0)[ae].union(graph.__getattribute__(k0)[nest])
                graph.__getattribute__(k0).pop(nest)
            for k, v in graph.__getattribute__(k0).items():
                if nest in v:
                    graph.__getattribute__(k0)[k] = graph.__getattribute__(k0)[k].union(atomic_events)
                    graph.__getattribute__(k0)[k].remove(nest)
        for k0 in ['timedconditions', 'timedresponses']:
            if nest in graph.__getattribute__(k0):
                for ae in atomic_events:
                    if ae not in graph.__getattribute__(k0):
                        graph.__getattribute__(k0)[ae] = {}
                    graph.__getattribute__(k0)[ae] = {**graph.__getattribute__(k0)[ae], **graph.__getattribute__(k0)[nest]}
                graph.__getattribute__(k0).pop(nest)
            for k, v in graph.__getattribute__(k0).items():
                for kv0, vv0 in v.items():
                    if nest == kv0:
                        for ae in atomic_events:
                            graph.__getattribute__(k0)[k][ae] = vv0
                        graph.__getattribute__(k0)[k].pop(nest)

    graph.events = all_atomic_events
    graph.marking.included = graph.marking.included.intersection(all_atomic_events)
    graph.nestedgroups = {}
    graph.nestedgroups_map = {}
    return graph
