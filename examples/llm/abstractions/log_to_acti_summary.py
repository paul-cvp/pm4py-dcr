import pm4py
from pm4py.objects.conversion.log import converter as log_converter
from typing import Union, Optional, Dict, Any
from pm4py.objects.log.obj import EventLog, EventStream
from enum import Enum
from pm4py.util import exec_utils, constants, xes_constants
from pm4py.statistics.service_time.pandas import get as service_time_get
from pm4py.statistics.eventually_follows.pandas import get as eventually_follows
import pandas as pd


class Parameters(Enum):
    MAX_LEN = "max_len"
    RESPONSE_HEADER = "response_header"
    PERFORMANCE_AGGREGATION = "performance_aggregation"
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    START_TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY


def apply(log_obj: Union[EventLog, EventStream, pd.DataFrame],
          parameters: Optional[Dict[Union[str, Parameters], Any]] = None) -> str:
    """
    Provides an abstraction of the activities' frequency and performance.

    Minimum Viable Example:

        import pm4py
        from pm4py.algo.querying.llm.abstractions import log_to_acti_summary

        log = pm4py.read_xes("tests/input_data/receipt.xes")
        print(log_to_acti_summary.apply(log))

    Example output:

        Below you find the top activities of the event log, specified with their total number of occurrences, the number of cases in which they occur, an aggregation of the service time, an aggregation of the times from the preceding activities and to the succeeding activities.

        Confirmation of receipt [tot.occ=1434; num.cases=1434; service time=0.00 s; time from prec.=0.00 s; time to succ.=76014.05 s]
        T02 Check confirmation of receipt [tot.occ=1368; num.cases=1316; service time=0.00 s; time from prec.=100581.24 s; time to succ.=44701.62 s]
        T06 Determine necessity of stop advice [tot.occ=1416; num.cases=1309; service time=0.00 s; time from prec.=186313.29 s; time to succ.=44757.08 s]
        T04 Determine confirmation of receipt [tot.occ=1307; num.cases=1303; service time=0.00 s; time from prec.=36815.50 s; time to succ.=65668.55 s]


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
        Textual abstraction of the activities frequency and of their performance.
    """
    if parameters is None:
        parameters = {}

    response_header = exec_utils.get_param_value(Parameters.RESPONSE_HEADER, parameters, True)
    max_len = exec_utils.get_param_value(Parameters.MAX_LEN, parameters, constants.OPENAI_MAX_LEN)

    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_constants.DEFAULT_NAME_KEY)
    timestamp_key = exec_utils.get_param_value(Parameters.TIMESTAMP_KEY, parameters,
                                               xes_constants.DEFAULT_TIMESTAMP_KEY)
    start_timestamp_key = exec_utils.get_param_value(Parameters.START_TIMESTAMP_KEY, parameters,
                                                     xes_constants.DEFAULT_TIMESTAMP_KEY)
    case_id_key = exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters, constants.CASE_CONCEPT_NAME)
    performance_aggregation = exec_utils.get_param_value(Parameters.PERFORMANCE_AGGREGATION, parameters, "mean")

    log_obj = log_converter.apply(log_obj, variant=log_converter.Variants.TO_DATA_FRAME, parameters=parameters)
    log_obj = log_obj[list({activity_key, timestamp_key, start_timestamp_key, case_id_key})]

    num_occ = log_obj[activity_key].value_counts().to_dict()
    num_cases = log_obj.groupby([case_id_key, activity_key]).first().reset_index()[
        activity_key].value_counts().to_dict()

    parameters["aggregationMeasure"] = performance_aggregation
    service_times = service_time_get.apply(log_obj, parameters=parameters)

    dir_follo_dataframe = eventually_follows.get_partial_order_dataframe(log_obj.copy(), activity_key=activity_key,
                                                                         start_timestamp_key=start_timestamp_key,
                                                                         timestamp_key=timestamp_key,
                                                                         case_id_glue=case_id_key,
                                                                         sort_caseid_required=False,
                                                                         sort_timestamp_along_case_id=False,
                                                                         reduce_dataframe=False)

    post_times = dir_follo_dataframe.groupby(activity_key)[constants.DEFAULT_FLOW_TIME].agg(
        performance_aggregation).to_dict()
    pre_times = dir_follo_dataframe.groupby(activity_key + "_2")[constants.DEFAULT_FLOW_TIME].agg(
        performance_aggregation).to_dict()

    activities_list = []
    for act in num_occ:
        activities_list.append({"activity": act, "num_occ": num_occ[act], "num_cases": num_cases[act],
                                "agg_service_time": service_times[act] if act in service_times else 0.0,
                                "agg_pre_times": pre_times[act] if act in pre_times else 0.0,
                                "agg_post_times": post_times[act] if act in post_times else 0.0})

    activities_list = sorted(activities_list, key=lambda x: (x["num_cases"], x["num_occ"], x["activity"]), reverse=True)

    ret = "\n\n"

    if response_header:
        ret += "Below you find the top activities of the event log, specified with their total number of occurrences, the number of cases in which they occur, an aggregation of the service time, an aggregation of the times from the preceding activities and to the succeeding activities.\n\n"

    for dct in activities_list:
        ths = "%s [tot.occ=%d; num.cases=%d; service time=%.2f s; time from prec.=%.2f s; time to succ.=%.2f s]\n" % (
            dct["activity"], dct["num_occ"], dct["num_cases"], dct["agg_service_time"], dct["agg_pre_times"],
            dct["agg_post_times"])
        if len(ret) + len(ths) < max_len:
            ret = ret + ths
        else:
            break

    ret += "\n\n"

    return ret


if __name__ == "__main__":
    log = pm4py.read_xes("../../../tests/input_data/receipt.xes")
    textual_abstraction = apply(log)
    print(textual_abstraction)
