from typing import Union

import pm4py
import pandas as pd

from copy import deepcopy

from pm4py.objects.dcr.obj import DcrGraph
from pm4py.objects.dcr.semantics import DcrSemantics
from pm4py.objects.log.obj import EventLog


def apply(log: Union[pd.DataFrame,EventLog], graph: DcrGraph, parameters):
    """
    An extension to the DCR Graphs discovery algorithm for the discovery of initially pending events
    Parameters
    ----------
    log
        Event log / Pandas dataframe
    graph
        DCR Graph
    ignore_lifecycle
        If True it does not take into account the 'lifecycle:transition'  attribute of the log event else False

    Returns
    ----------
    An updated DCR Graph with the Pending Marking updated to contain initially pending events
    """
    ignore_lifecycle = True
    if 'ignore_lifecycle' in parameters:
        ignore_lifecycle = parameters["ignore_lifecycle"]

    if isinstance(log, pd.DataFrame):
        log = pm4py.convert_to_event_log(log)

    at_least_once_all_traces = set(graph.events)
    end_excluded_all_traces = set(graph.events)

    for trace in log:
        executed_events = set()
        im = deepcopy(graph.marking)
        temp_graph = deepcopy(graph)
        complete = True
        semantics_obj = DcrSemantics()
        for event in trace:
            semantics_obj.execute(temp_graph, event['concept:name'])
            if event['concept:name'] in temp_graph.marking.executed:
                executed_events.add(event['concept:name'])
            if not ignore_lifecycle:
                complete = complete and event['lifecycle:transition'] == 'complete'
        if complete:
            fm = temp_graph.marking
            excluded_events = im.included.difference(fm.included)
            at_least_once_all_traces = at_least_once_all_traces.intersection(executed_events)
            end_excluded_all_traces = end_excluded_all_traces.intersection(excluded_events)

    initially_pending = at_least_once_all_traces.union(end_excluded_all_traces)
    graph.marking.pending = graph.marking.pending.union(initially_pending)
    return graph
