from copy import deepcopy

import pandas as pd
from typing import Optional, Any, Union, Dict
import pm4py
from pm4py.objects.dcr.obj import DcrGraph
from pm4py.util import exec_utils, constants, xes_constants
from pm4py.objects.dcr.timed.obj import TimedDcrGraph
from pm4py.objects.log.obj import EventLog


def apply(log, graph: DcrGraph, parameters) -> TimedDcrGraph:
    """
    this method calls the time miner

    Parameters
    ----------
    log: EventLog | pandas.Dataframe
        Event log to use in the time miner
    graph: DCR_Graph
        Dcr graph to apply additional attributes to
    parameters
        Parameters of the algorithm, including:


    Returns
    -------
    :class:´TimedDcrGraph`
        return a DCR graph
    """
    time_mine = TimeMining()
    return time_mine.mine(log, graph, parameters)


class TimeMining:
    """
    The TimeMining provides a simple algorithm to mine timing data of an event log for DCR graphs

    After initialization, user can call mine(log, G, parameters), which will return a DCR Graph with time.

    Attributes
    ----------
    graph: Dict[str,Any]

    Methods
    -------
    mine(log, G, parameters)

    Notes
    ------
    *
    """
    def __init__(self):
        self.timing_dict = {"conditionsForDelays": {}, "responseToDeadlines": {}}


    def get_log_with_pair(self, event_log, e1, e2):
        '''
        when selecting the case ids (cids) here there is a difference when taking
        strictly less than < and strictly less than or equal <=
        Less than or equal <= allows for instant executions (so a time of 0 between events e1 and e2)
        '''
        first_e1 = event_log[event_log['concept:name'] == e1].groupby('case:concept:name')[
            ['case:concept:name', 'time:timestamp']].first().reset_index(drop=True)
        subset_is_in = first_e1.merge(event_log, on='case:concept:name', how='inner', suffixes=('_e1', ''))
        cids = subset_is_in[
            ((subset_is_in['time:timestamp_e1'] <= subset_is_in['time:timestamp']) & (subset_is_in['concept:name'] == e2))][
            'case:concept:name'].unique()
        return event_log[event_log['case:concept:name'].isin(cids)].copy(deep=True)


    def get_delta_between_events(self, filtered_df, event_pair, rule=None):
        e1 = event_pair[0]
        e2 = event_pair[1]
        filtered_df = filtered_df[['case:concept:name', 'concept:name', 'time:timestamp']]
        filtered_df = filtered_df[filtered_df['concept:name'].isin(event_pair)]
        filtered_df['time:timestamp'] = pd.to_datetime(filtered_df['time:timestamp'], utc=True)
        deltas = []
        # for idx, g in filtered_df[filtered_df['concept:name'].isin([e1, e2])].groupby('case:concept:name'):
        for idx, g in filtered_df.groupby('case:concept:name'):
            g = g.sort_values(by='time:timestamp').reset_index(drop=True)
            g['time:timestamp:to'] = g['time:timestamp'].shift(-1)
            g['concept:name:to'] = g['concept:name'].shift(-1)
            temp_df = deepcopy(g)
            res = []
            if rule == 'RESPONSE':
                g_e1 = deepcopy(g[g['concept:name'] == e1])
                if len(g_e1) >= 1:
                    g_e1 = g_e1.reset_index(drop=False)
                    g_e1['index_below'] = g_e1['index'].shift(-1)
                    g_e1 = g_e1[((g_e1['index_below'] - g_e1['index']) == 1)]
                    g_e1['delta'] = g_e1['time:timestamp:to'] - g_e1['time:timestamp']
                    res.extend(g_e1['delta'])
                temp_df = temp_df[
                    (temp_df['concept:name'] == e1) & (temp_df['concept:name:to'] == e2)]
                temp_df['delta'] = temp_df['time:timestamp:to'] - temp_df['time:timestamp']
                res.extend(temp_df['delta'])
            elif rule == 'CONDITION':
                temp_df = temp_df[
                    (temp_df['concept:name'] == e1) & (temp_df['concept:name:to'] == e2)]
                temp_df['delta'] = temp_df['time:timestamp:to'] - temp_df['time:timestamp']
                res.extend(temp_df['delta'])
            else:
                temp_df = temp_df[
                    (temp_df['concept:name'] == e1) & (temp_df['concept:name:to'] == e2)]
                temp_df['delta'] = temp_df['time:timestamp:to'] - temp_df['time:timestamp']
                res.extend(temp_df['delta'])
            deltas.extend(res)
        return deltas


    def mine(self, log: Union[pd.DataFrame, EventLog], graph, parameters: Optional[Dict[str, Any]]):
        activity_key = exec_utils.get_param_value(constants.PARAMETER_CONSTANT_ACTIVITY_KEY, parameters,
                                                  xes_constants.DEFAULT_NAME_KEY)
        # perform mining on event logs
        if not isinstance(log, pd.DataFrame):
            log = pm4py.convert_to_dataframe(log)
        activities = log[activity_key].unique()

        timing_input_dict = {'CONDITION': set(), 'RESPONSE': set()}
        for e1 in graph.conditions.keys():
            for e2 in graph.conditions[e1]:
                timing_input_dict['CONDITION'].add((e2, e1))

        for e1 in graph.responses.keys():
            for e2 in graph.responses[e1]:
                timing_input_dict['RESPONSE'].add((e1, e2))

        timings = {}
        for rule, event_pairs in timing_input_dict.items():
            for event_pair in event_pairs:
                if event_pair[0] in activities and event_pair[1] in activities:
                    filtered_df = self.get_log_with_pair(log, event_pair[0], event_pair[1])
                    data = self.get_delta_between_events(filtered_df, event_pair, rule)
                    timings[(rule, event_pair[0], event_pair[1])] = data

        # these are a dict with events as keys and tuples as values
        for timing, value in timings.items():
            if timing[0] == 'CONDITION':
                e1 = timing[2]
                e2 = timing[1]
                if e1 not in self.timing_dict['conditionsForDelays']:
                    self.timing_dict['conditionsForDelays'][e1] = {}
                # to have perfect fitness we extract the minimum delay for conditions
                self.timing_dict['conditionsForDelays'][e1][e2] = min(value)
            elif timing[0] == 'RESPONSE':
                e1 = timing[1]
                e2 = timing[2]
                if e1 not in self.timing_dict['responseToDeadlines']:
                    self.timing_dict['responseToDeadlines'][e1] = {}
                # to have perfect fitness we extract the maximum deadline for responses
                self.timing_dict['responseToDeadlines'][e1][e2] = max(value)

        return TimedDcrGraph({**graph.obj_to_template(), **self.timing_dict})
