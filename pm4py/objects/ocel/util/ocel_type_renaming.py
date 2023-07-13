from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.ocel.util import names_stripping
from copy import deepcopy
from typing import Dict, Optional


def __rename_types_from_maps(ocel: OCEL, event_types_map: Optional[Dict[str, str]], object_types_map: Optional[Dict[str, str]]) -> OCEL:
    ret_ocel = deepcopy(ocel)

    if event_types_map is not None:
        ret_ocel.events[ocel.event_activity] = ret_ocel.events[ocel.event_activity].map(event_types_map)
        ret_ocel.relations[ocel.event_activity] = ret_ocel.relations[ocel.event_activity].map(event_types_map)

    if object_types_map is not None:
        ret_ocel.objects[ocel.object_type_column] = ret_ocel.objects[ocel.object_type_column].map(object_types_map)
        ret_ocel.relations[ocel.object_type_column] = ret_ocel.relations[ocel.object_type_column].map(object_types_map)
        ret_ocel.object_changes[ocel.object_type_column] = ret_ocel.object_changes[ocel.object_type_column].map(object_types_map)

    return ret_ocel


def rename_strip_spaces(ocel: OCEL) -> OCEL:
    """
    Creates a copy of the object-centric event log in which
    spaces and non-alphanumeric characters inside the event/object types are stripped

    Parameters
    ----------------
    ocel
        Object-centric event log

    Returns
    ----------------
    ocel
        Object-centric event log with stripped types
    """
    object_types = ocel.objects[ocel.object_type_column].value_counts().to_dict()
    event_types = ocel.events[ocel.event_activity].value_counts().to_dict()

    object_types_map = {x: names_stripping.apply(x) for x in object_types}
    event_types_map = {x: names_stripping.apply(x) for x in event_types}

    return __rename_types_from_maps(ocel, event_types_map, object_types_map)


def rename_ev_types_to_alphabet(ocel: OCEL) -> OCEL:
    """
    Creates a copy of the object-centric event log in which
    the event types are replaced by the letters of the alphabet (A being the most frequent event type, ...).
    This is particularly useful to textually abstract the object-centric event log.

    Parameters
    ----------------
    ocel
        Object-centric event log

    Returns
    ----------------
    ocel
        Object-centric event log with alphabetical event types
    """
    event_types = list(ocel.events[ocel.event_activity].value_counts().to_dict())

    event_types_map = {}
    for index, act in enumerate(event_types):
        result = ''
        while index >= 0:
            result = chr((index % 26) + ord('A')) + result
            index = index // 26 - 1
        event_types_map[act] = result

    return __rename_types_from_maps(ocel, event_types_map, None)
