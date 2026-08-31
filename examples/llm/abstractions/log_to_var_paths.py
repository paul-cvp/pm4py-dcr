from pm4py.objects.conversion.log import converter as log_converter
from typing import Union, Optional, Dict, Any
from pm4py.objects.log.obj import EventLog, EventStream
from enum import Enum
from pm4py.util import exec_utils, constants, xes_constants
import pm4py
import pandas as pd


class Parameters(Enum):
    MAX_LEN = "max_len"
    RESPONSE_HEADER = "response_header"
    PERFORMANCE_AGGREGATION = "performance_aggregation"
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY


def apply(log_obj: Union[EventLog, EventStream, pd.DataFrame], parameters: Optional[Dict[Any, Any]] = None) -> str:
    """
    Provides an abstraction of the paths performance for the process variants of the provided event log.

    Minimum Viable Example:

        import pm4py
        from pm4py.algo.querying.llm.abstractions import log_to_var_paths

        log = pm4py.read_xes("tests/input_data/receipt.xes")
        print(log_to_var_paths.apply(log))


    Example output:

        Below your find a description of the top process variants of the event logs, along with their frequency. The paths of every reported variant are decorated with an aggregation (mean) of the performance of the path in the given variant.

        Confirmation of receipt -(8064.44 s)-> T02 Check confirmation of receipt -(29250.98 s)-> T04 Determine confirmation of receipt -(218458.20 s)-> T05 Print and send confirmation of receipt -(39225.28 s)-> T06 Determine necessity of stop advice [frequency=713]
        Confirmation of receipt -(3621.01 s)-> T06 Determine necessity of stop advice -(157907.57 s)-> T10 Determine necessity to stop indication -(116514.54 s)-> T02 Check confirmation of receipt -(144858.47 s)-> T04 Determine confirmation of receipt [frequency=123]
        Confirmation of receipt -(79543.37 s)-> T02 Check confirmation of receipt -(169.38 s)-> T06 Determine necessity of stop advice -(144037.68 s)-> T10 Determine necessity to stop indication -(86823.89 s)-> T04 Determine confirmation of receipt [frequency=115]


    Parameters
    ---------------
    log_obj
        Log object
    parameters
        Optional parameters of the algorithm, including:
        - Parameters.MAX_LEN => desidered length of the textual abstraction
        - Parameters.RESPONSE_HEADER => includes an header in the textual abstraction, which explains the context
        - Parameters.PERFORMANCE_AGGREGATION => performance metric to be used to express the performance (e.g., mean). Available options: mean, median, stdev, min, max, sum
        - Parameters.ACTIVITY_KEY => the attribute of the log to be used as activity
        - Parameters.TIMESTAMP_KEY => the attribute of the log to be used as timestamp
        - Parameters.CASE_ID_KEY => the attribute of the log to be used as case identifier

    Returns
    --------------
    textual_abstraction
        Textual abstraction of the paths' performance for every process variant
    """
    if parameters is None:
        parameters = {}

    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_constants.DEFAULT_NAME_KEY)
    timestamp_key = exec_utils.get_param_value(Parameters.TIMESTAMP_KEY, parameters,
                                               xes_constants.DEFAULT_TIMESTAMP_KEY)
    case_id_key = exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters, constants.CASE_CONCEPT_NAME)
    performance_aggregation = exec_utils.get_param_value(Parameters.PERFORMANCE_AGGREGATION, parameters, "mean")

    response_header = exec_utils.get_param_value(Parameters.RESPONSE_HEADER, parameters, True)
    max_len = exec_utils.get_param_value(Parameters.MAX_LEN, parameters, constants.OPENAI_MAX_LEN)

    log_obj = log_converter.apply(log_obj, variant=log_converter.Variants.TO_DATA_FRAME, parameters=parameters)

    import pm4py.stats
    var_paths0 = pm4py.stats.get_variants_paths_duration(log_obj, activity_key=activity_key,
                                                         timestamp_key=timestamp_key, case_id_key=case_id_key,
                                                         times_agg=performance_aggregation).to_dict("records")
    var_paths = []
    for el in var_paths0:
        if el["@@index_in_trace"] == 0:
            var_paths.append([])
        var_paths[-1].append(el)

    ret = "\n\n"

    if response_header:
        ret += "Below your find a description of the top process variants of the event logs, along with their frequency. The paths of every reported variant are decorated with an aggregation (" + performance_aggregation + ") of the performance of the path in the given variant.\n\n"

    for var in var_paths:
        ths = var[0][activity_key]
        for i in range(1, len(var)):
            ths += " -(%.2f s)-> %s" % (var[i]["@@flow_time"], var[i][activity_key])

        ths += " [frequency=%d]\n" % (var[0]["@@variant_count"])

        if len(ret) + len(ths) < max_len:
            ret = ret + ths
        else:
            break

    ret = ret + "\n\n"

    return ret


if __name__ == "__main__":
    log = pm4py.read_xes("../../../tests/input_data/receipt.xes")
    textual_abstraction = apply(log)
    print(textual_abstraction)
