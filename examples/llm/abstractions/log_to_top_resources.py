from pm4py.objects.conversion.log import converter as log_converter
from typing import Union, Optional, Dict, Any
from pm4py.objects.log.obj import EventLog, EventStream
from enum import Enum
from pm4py.util import exec_utils, constants, xes_constants
import pandas as pd
import pm4py
from copy import copy


class Parameters(Enum):
    MAX_LEN = "max_len"
    RESPONSE_HEADER = "response_header"
    DEFAULT_MIN_ACTIVITIES = "default_min_activities"
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    RESOURCE_KEY = constants.PARAMETER_CONSTANT_RESOURCE_KEY


def get_abstr_from_dict(ret, activities_dict, response_header):
    """
    Internal method to get the textual abstraction starting from the computations already performed.
    """
    abstr = ["\n\n"]

    if response_header:
        abstr.append(
            "In the following text, you find the top activities along with their number of occurrences in the event log and the number of unique resources performing them.")
        abstr.append("The top resources for such activities are included.\n\n")

    sort_act = sorted([(x, activities_dict[x][0], activities_dict[x][1], ret[x]) for x in ret],
                      key=lambda x: (x[1], x[2], x[0]), reverse=True)

    for el in sort_act:
        abstr.append("%s (num.occ=%d ; num.resources=%d)" % (el[0], el[1], el[2]))

        if el[3]:
            abstr.append(" top resources=[")

            this_res = sorted([(x, y) for x, y in el[3].items()], key=lambda z: (z[1], z[0]), reverse=True)

            for i in range(len(this_res)):
                if i > 0:
                    abstr.append("; ")
                abstr.append("%s=%d" % (this_res[i][0], this_res[i][1]))
            abstr.append("]")

        abstr.append("\n")

    abstr.append("\n\n")

    abstr1 = "".join(abstr)
    return abstr1


def apply(log: Union[EventLog, EventStream, pd.DataFrame], parameters: Optional[Dict[Any, Any]] = None) -> str:
    """
    Textually abstracts the top activities/resources combinations in the event log.


    Minimum Viable Example:

        import pm4py
        from pm4py.algo.querying.llm.abstractions import log_to_resources


        log = pm4py.read_xes("C:/receipt.xes")
        res = log_to_resources.apply(log)
        print(res)


    Example output:

    In the following text, you find the top activities along with their number of occurrences in the event log and the number of unique resources performing them.The top resources for such activities are included.

        Confirmation of receipt (num.occ=1434 ; num.resources=41) top resources=[Resource01=195; admin2=114; Resource02=102; Resource03=87; Resource04=81; Resource07=78; Resource08=74; Resource06=70; Resource05=65; Resource11=58; Resource09=55; Resource15=51; Resource12=49; Resource13=47; Resource14=44; Resource17=43; Resource27=37; Resource16=35; Resource18=29; Resource10=21; Resource21=19; Resource20=18; Resource23=14; Resource22=12; Resource26=7; Resource25=7; Resource30=4; Resource33=2; Resource31=2; Resource29=2; Resource28=2; admin3=1; admin1=1; Resource43=1; Resource42=1; Resource38=1; Resource37=1; Resource36=1; Resource35=1; Resource34=1; Resource19=1]
        T06 Determine necessity of stop advice (num.occ=1416 ; num.resources=34) top resources=[Resource01=203; Resource02=114; Resource04=85; Resource03=85; Resource05=84; Resource07=83; Resource08=75; Resource06=75; Resource11=74; Resource12=72; Resource09=67; Resource15=58; Resource13=53; Resource14=48; Resource17=43; Resource16=36; Resource18=28; admin2=20; Resource20=18; Resource21=16; Resource22=15; Resource23=14; Resource26=12; Resource25=12; Resource29=6; Resource28=6; Resource37=2; Resource35=2; Resource34=2; Resource33=2; Resource31=2; Resource30=2; test=1; Resource36=1]
        T02 Check confirmation of receipt (num.occ=1368 ; num.resources=40) top resources=[Resource01=209; Resource02=95; Resource04=91; Resource03=86; Resource06=73; Resource08=65; Resource05=65; Resource19=64; Resource10=62; Resource13=55; Resource09=51; Resource07=50; Resource24=44; Resource12=44; Resource14=43; Resource16=36; Resource17=32; Resource15=32; Resource18=30; Resource11=30; Resource21=18; Resource20=18; Resource22=13; Resource23=12; admin2=9; Resource32=9; Resource25=6; Resource26=5; Resource28=4; Resource30=3; Resource39=2; Resource34=2; Resource31=2; Resource29=2; admin1=1; TEST=1; Resource38=1; Resource36=1; Resource35=1; Resource33=1]
        T04 Determine confirmation of receipt (num.occ=1307 ; num.resources=37) top resources=[Resource10=240; Resource01=184; Resource03=81; Resource04=68; Resource02=67; Resource06=66; Resource19=61; Resource05=60; Resource07=58; Resource09=46; Resource14=41; Resource12=41; Resource13=40; Resource18=36; Resource16=36; Resource08=31; Resource11=29; Resource15=28; Resource20=18; Resource21=15; Resource17=13; Resource22=12; Resource23=11; admin2=3; Resource26=3; Resource25=3; admin3=2; admin1=2; Resource31=2; Resource29=2; Resource28=2; Resource38=1; Resource36=1; Resource35=1; Resource34=1; Resource33=1; Resource24=1]


    Parameters
    ----------------
    log
        Log object
    parameters
        Parameters of the algorithm, including:
        - Parameters.ACTIVITY_KEY => the attribute to be used as activity
        - Parameters.RESOURCE_KEY => the attribute to be used as resource
        - Parameters.DEFAULT_MIN_ACTIVITIES => minimum number of different activities to include in the textual abstraction
        - Parameters.ACTIVITY_KEY => attribute of the log to be used as activity
        - Parameters.RESOURCE_KEY => attribute of the log to be used as resource

    Returns
    ----------------
    textual_abstraction
        Textual abstraction
    """
    if parameters is None:
        parameters = {}

    max_len = exec_utils.get_param_value(Parameters.MAX_LEN, parameters, constants.OPENAI_MAX_LEN)
    response_header = exec_utils.get_param_value(Parameters.RESPONSE_HEADER, parameters, True)
    default_min_activities = exec_utils.get_param_value(Parameters.DEFAULT_MIN_ACTIVITIES, parameters, 15)
    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_constants.DEFAULT_NAME_KEY)
    resource_key = exec_utils.get_param_value(Parameters.RESOURCE_KEY, parameters, xes_constants.DEFAULT_RESOURCE_KEY)

    log = log_converter.apply(log, variant=log_converter.Variants.TO_DATA_FRAME, parameters=parameters)

    activities = log[activity_key].value_counts().to_dict()
    activities_unq_resources = log.groupby(activity_key)[resource_key].nunique().to_dict()
    activities = [(x, y, activities_unq_resources[x]) for x, y in activities.items()]
    activities_dict = {x[0]: (x[1], x[2]) for x in activities}

    activities = sorted(activities, key=lambda z: (z[1], z[2], z[0]), reverse=True)

    ret = {}
    for i in range(min(len(activities), default_min_activities)):
        new_ret = copy(ret)
        new_ret[activities[i][0]] = {}

        if len(get_abstr_from_dict(new_ret, activities_dict, response_header)) > max_len:
            break

        ret = new_ret

    activities_resources = log.groupby([activity_key, resource_key]).size().to_dict()
    activities_resources = sorted([(x, y) for x, y in activities_resources.items()], key=lambda z: (z[1], z[0]),
                                  reverse=True)

    for el in activities_resources:
        new_ret = copy(ret)
        if el[0][0] not in new_ret:
            new_ret[el[0][0]] = {}
        new_ret[el[0][0]][el[0][1]] = el[1]

        if len(get_abstr_from_dict(new_ret, activities_dict, response_header)) > max_len:
            break

        ret = new_ret

    return get_abstr_from_dict(ret, activities_dict, response_header)


if __name__ == "__main__":
    log = pm4py.read_xes("../../../tests/input_data/receipt.xes")
    textual_abstraction = apply(log)
    print(textual_abstraction)
