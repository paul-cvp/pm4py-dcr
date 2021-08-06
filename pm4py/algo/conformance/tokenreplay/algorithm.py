from pm4py.algo.conformance.tokenreplay.variants import token_replay, backwards
from pm4py.objects.conversion.log import converter as log_converter
from enum import Enum
from pm4py.util import exec_utils
from typing import Optional, Dict, Any, Union, Tuple
from pm4py.objects.log.obj import EventLog, EventStream
import pandas as pd
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.util import typing


class Variants(Enum):
    TOKEN_REPLAY = token_replay
    BACKWARDS = backwards

VERSIONS = {Variants.TOKEN_REPLAY, Variants.BACKWARDS}
DEFAULT_VARIANT = Variants.TOKEN_REPLAY


def apply(log: Union[EventLog, EventStream, pd.DataFrame], net: PetriNet, initial_marking: Marking, final_marking: Marking, parameters: Optional[Dict[Any, Any]] = None, variant=DEFAULT_VARIANT) -> typing.ListAlignments:
    """
    Method to apply token-based replay
    
    Parameters
    -----------
    log
        Log
    net
        Petri net
    initial_marking
        Initial marking
    final_marking
        Final marking
    parameters
        Parameters of the algorithm, including:
            Parameters.ACTIVITY_KEY -> Activity key
    variant
        Variant of the algorithm to use:
            - Variants.TOKEN_REPLAY
            - Variants.BACKWARDS
    """
    if parameters is None:
        parameters = {}
    return exec_utils.get_variant(variant).apply(log_converter.apply(log, parameters, log_converter.TO_EVENT_LOG), net, initial_marking,
                             final_marking, parameters=parameters)


def get_diagnostics_dataframe(log: Union[EventLog, EventStream, pd.DataFrame], tbr_output: typing.ListAlignments, variant=DEFAULT_VARIANT, parameters: Optional[Dict[Any, Any]] = None) -> pd.DataFrame:
    """
    Gets the results of token-based replay in a dataframe

    Parameters
    --------------
    log
        Event log
    tbr_output
        Output of the token-based replay technique
    variant
        Variant of the algorithm to use:
            - Variants.TOKEN_REPLAY
            - Variants.BACKWARDS

    Returns
    --------------
    dataframe
        Diagnostics dataframe
    """
    if parameters is None:
        parameters = {}

    return exec_utils.get_variant(variant).get_diagnostics_dataframe(log, tbr_output, parameters=parameters)
