from enum import Enum
from pm4py.util import exec_utils
from pm4py.util import xes_constants, constants, pandas_utils
import pandas as pd
from typing import Dict, Optional, Any, Tuple
from pm4py.util.business_hours import soj_time_business_hours_diff
from pm4py.algo.discovery.ocel.link_analysis.variants import classic as link_analysis


class Parameters(Enum):
    SORTING_COLUMN = "sorting_column"
    INDEX_KEY = "index_key"
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    IN_COLUMN = "in_column"
    OUT_COLUMN = "out_column"
    NODE_COLUMN_SOURCE = "node_column_source"
    NODE_COLUMN_TARGET = "node_column_target"
    EDGE_COLUMN = "edge_column"
    INCLUDE_PERFORMANCE = "include_performance"
    BUSINESS_HOURS = "business_hours"
    WORKTIMING  = "worktiming"
    WEEKENDS = "weekends"
    WORKCALENDAR = "workcalendar"
    TIMESTAMP_DIFF_COLUMN = "timestamp_diff_column"
    EDGE_REFERENCE = "edge_reference"


def build_network_analysis_from_link_analysis(merged_df: pd.DataFrame, parameters: Optional[Dict[Any, Any]] = None) -> \
Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Builds the network analysis from the results of the link analysis (internal method)

    Parameters
    ------------------
    merged_df
        Dataframe obtained from the link analysis
    parameters
        Parameters of the method, including:
            - Parameters.NODE_COLUMN_SOURCE => the attribute to be used for the node definition of the source event (default: the resource of the log, org:resource)
            - Parameters.NODE_COLUMN_TARGET => the attribute to be used for the node definition of the target event (default: the resource of the log, org:resource)
            - Parameters.EDGE_COLUMN => the attribute to be used for the edge definition (default: the activity of the log, concept:name)
            - Parameters.EDGE_REFERENCE => the event into which the edge attribute should be picked:
                - _out  =>  the source event
                - _in   =>  the target event
            - Parameters.TIMESTAMP_COLUMN => the timestamp column
            - Parameters.TIMESTAMP_DIFF_COLUMN => timestamp diff column
            - Parameters.INCLUDE_PERFORMANCE => considers the performance of the edge
            - Parameters.BUSINESS_HOURS => boolean value that enables the business hours
            - Parameters.WORKTIMING => defines the worktiming of the organization (e.g. [7, 17]) if business hours are enabled
            - Parameters.WEEKENDS => defines the weekends of the organization (e.g. [6, 7]) if business hours are enabled

    Returns
    -----------------
    network_analysis
        Edges of the network analysis (first key: edge; second key: type; value: number of occurrences)
    """
    if parameters is None:
        parameters = {}

    node_column_source = exec_utils.get_param_value(Parameters.NODE_COLUMN_SOURCE, parameters, xes_constants.DEFAULT_RESOURCE_KEY)
    node_column_target = exec_utils.get_param_value(Parameters.NODE_COLUMN_TARGET, parameters, xes_constants.DEFAULT_RESOURCE_KEY)
    edge_column = exec_utils.get_param_value(Parameters.EDGE_COLUMN, parameters, xes_constants.DEFAULT_NAME_KEY)
    edge_reference = exec_utils.get_param_value(Parameters.EDGE_REFERENCE, parameters, "_out")
    timestamp_column = exec_utils.get_param_value(Parameters.TIMESTAMP_KEY, parameters,
                                                  xes_constants.DEFAULT_TIMESTAMP_KEY)
    timestamp_diff_column = exec_utils.get_param_value(Parameters.TIMESTAMP_DIFF_COLUMN, parameters, "@@timestamp_diff")

    include_performance = exec_utils.get_param_value(Parameters.INCLUDE_PERFORMANCE, parameters, False)
    business_hours = exec_utils.get_param_value(Parameters.BUSINESS_HOURS, parameters, False)
    worktiming = exec_utils.get_param_value(Parameters.WORKTIMING, parameters, [7, 17])
    weekends = exec_utils.get_param_value(Parameters.WEEKENDS, parameters, [6, 7])
    workcalendar = exec_utils.get_param_value(Parameters.WORKCALENDAR, parameters, constants.DEFAULT_BUSINESS_HOURS_WORKCALENDAR)

    edges = {}

    if business_hours:
        merged_df[timestamp_diff_column] = merged_df.apply(
            lambda x: soj_time_business_hours_diff(x[timestamp_column + "_out"], x[timestamp_column + "_in"],
                                                   worktiming,
                                                   weekends, workcalendar), axis=1)

    else:
        merged_df[timestamp_diff_column] = (
                merged_df[timestamp_column + "_in"] - merged_df[timestamp_column + "_out"]).astype(
            'timedelta64[s]')

    edges0 = merged_df.dropna(subset=[node_column_source + "_out", node_column_target + "_in", edge_column + edge_reference], how="any").groupby([node_column_source + "_out", node_column_target + "_in", edge_column + edge_reference])[
        timestamp_diff_column].apply(list).to_dict()

    for e0 in edges0:
        edge = (e0[0], e0[1])
        edge_value = e0[2]
        if edge not in edges:
            edges[edge] = {}
        if edge_value not in edges[edge]:
            if include_performance:
                edges[edge][edge_value] = edges0[e0]
            else:
                edges[edge][edge_value] = len(edges0[e0])

    return edges


def apply(dataframe: pd.DataFrame, parameters: Optional[Dict[Any, Any]] = None) -> Dict[
    Tuple[str, str], Dict[str, Any]]:
    """
    Performs the network analysis on the provided dataframe

    Parameters
    -----------------
    dataframe
        Dataframe
    parameters
        Parameters of the method, including:
        - Parameters.SORTING_COLUMN => the column that should be used to sort the log
        - Parameters.IN_COLUMN => the target column of the link (default: the case identifier; events of the same case are linked)
        - Parameters.OUT_COLUMN => the source column of the link (default: the case identifier; events of the same case are linked)
        - Parameters.INDEX_KEY => the name for the index attribute in the log (inserted during the execution)
        - Parameters.NODE_COLUMN_SOURCE => the attribute to be used for the node definition of the source event (default: the resource of the log, org:resource)
        - Parameters.NODE_COLUMN_TARGET => the attribute to be used for the node definition of the target event (default: the resource of the log, org:resource)
        - Parameters.EDGE_COLUMN => the attribute to be used for the edge definition (default: the activity of the log, concept:name)
        - Parameters.EDGE_REFERENCE => the event into which the edge attribute should be picked:
                - _out  =>  the source event
                - _in   =>  the target event
        - Parameters.TIMESTAMP_COLUMN => the timestamp column
        - Parameters.TIMESTAMP_DIFF_COLUMN => timestamp diff column
        - Parameters.INCLUDE_PERFORMANCE => considers the performance of the edge
        - Parameters.BUSINESS_HOURS => boolean value that enables the business hours
        - Parameters.WORKTIMING => defines the worktiming of the organization (e.g. [7, 17]) if business hours are enabled
        - Parameters.WEEKENDS => defines the weekends of the organization (e.g. [6, 7]) if business hours are enabled

    Returns
    -----------------
    network_analysis
        Edges of the network analysis (first key: edge; second key: type; value: number of occurrences)
    """
    if parameters is None:
        parameters = {}

    sorting_column = exec_utils.get_param_value(Parameters.SORTING_COLUMN, parameters,
                                                xes_constants.DEFAULT_TIMESTAMP_KEY)
    index_key = exec_utils.get_param_value(Parameters.INDEX_KEY, parameters, constants.DEFAULT_INDEX_KEY)
    timestamp_column = exec_utils.get_param_value(Parameters.TIMESTAMP_KEY, parameters,
                                                  xes_constants.DEFAULT_TIMESTAMP_KEY)
    in_column = exec_utils.get_param_value(Parameters.IN_COLUMN, parameters, constants.CASE_CONCEPT_NAME)
    out_column = exec_utils.get_param_value(Parameters.OUT_COLUMN, parameters, constants.CASE_CONCEPT_NAME)
    node_column_source = exec_utils.get_param_value(Parameters.NODE_COLUMN_SOURCE, parameters, xes_constants.DEFAULT_RESOURCE_KEY)
    node_column_target = exec_utils.get_param_value(Parameters.NODE_COLUMN_TARGET, parameters, xes_constants.DEFAULT_RESOURCE_KEY)
    edge_column = exec_utils.get_param_value(Parameters.EDGE_COLUMN, parameters, xes_constants.DEFAULT_NAME_KEY)

    dataframe = dataframe[{timestamp_column, in_column, out_column, node_column_source, node_column_target, edge_column, sorting_column}]

    parameters_la = {link_analysis.Parameters.OUT_COLUMN: out_column, link_analysis.Parameters.IN_COLUMN: in_column,
                     link_analysis.Parameters.INDEX_COLUMN: index_key,
                     link_analysis.Parameters.SORTING_COLUMN: sorting_column,
                     link_analysis.Parameters.LOOK_FORWARD: True, link_analysis.Parameters.KEEP_FIRST_OCCURRENCE: True,
                     link_analysis.Parameters.PROPAGATE: False}

    merged_df = link_analysis.apply(dataframe, parameters=parameters_la)

    return build_network_analysis_from_link_analysis(merged_df, parameters=parameters)
