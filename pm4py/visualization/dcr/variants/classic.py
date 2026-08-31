import tempfile
from enum import Enum

from click import option
from graphviz import Digraph

from pm4py.objects.dcr.timed.obj import TimedDcrGraph
from pm4py.objects.dcr.utils.utils import time_to_iso_string
from pm4py.util import exec_utils, constants

filename = tempfile.NamedTemporaryFile(suffix=".gv")
filename.close()

class Parameters(Enum):
    FORMAT = "format"
    RANKDIR = "set_rankdir"
    AGGREGATION_MEASURE = "aggregationMeasure"
    FONT_SIZE = "font_size"
    BGCOLOR = "bgcolor"
    DECORATIONS = "decorations"


def create_edge(source, target, relation, viz, time = None, font_size = None,time_precision='D'):
    viz.edge_attr['labeldistance'] = '0.0'
    if font_size:
        font_size = int(font_size)
        font_size = str(int(font_size - 2/3*font_size))
    if time:
        time = time_to_iso_string(time, time_precision)
        match time_precision:
            case 'D':
                time = None if time=='P0D' else time
            case 'H':
                time = None if time=='P0DT0H' else time
            case 'M':
                time = None if time=='P0DT0H0M' else time
            case 'S':
                time = None if time=='P0DT0H0M0S' else time

    match relation:
        case 'condition':
            if time:
                viz.edge(source, target, color='#FFA500', arrowhead='dotnormal', label=time, labelfontsize=font_size)
            else:
                viz.edge(source, target, color='#FFA500', arrowhead='dotnormal')
        case 'exclude':
            viz.edge(source, target, color='#FC0C1B', arrowhead='normal', arrowtail='none', headlabel='%', labelfontcolor='#FC0C1B', labelfontsize='8')
        case 'include':
            viz.edge(source, target, color='#30A627', arrowhead='normal', arrowtail='none', headlabel='+', labelfontcolor='#30A627', labelfontsize='10')
        case 'response':
            if time:
                viz.edge(source, target, color='#2993FC', arrowhead='normal', arrowtail='dot', dir='both', label=time, labelfontsize=font_size)
            else:
                viz.edge(source, target, color='#2993FC', arrowhead='normal', arrowtail='dot', dir='both')
        case 'noresponse':
            viz.edge(source, target, color='#7A514D', arrowhead='normal', headlabel='x', labelfontcolor='#7A514D', labelfontsize='8', arrowtail='dot', dir='both')
        case 'milestone':
            viz.edge(source, target, color='#A932D0', arrowhead='normal', headlabel='&#9671;', labelfontcolor='#A932D0', labelfontsize='8', arrowtail='dot', dir='both')
    return


def apply(dcr: TimedDcrGraph, parameters):
    if parameters is None:
        parameters = {}

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    set_rankdir = exec_utils.get_param_value(Parameters.RANKDIR, parameters, 'LR')
    font_size = exec_utils.get_param_value(Parameters.FONT_SIZE, parameters, "12")
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)

    viz = Digraph("", filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor, 'rankdir': set_rankdir},
                  node_attr={'shape': 'Mrecord'}, edge_attr={'arrowsize': '0.5'})

    for event in dcr.events:
        label = None
        try:
            roles = []
            key_list = list(dcr.role_assignments.keys())
            value_list = list(dcr.role_assignments.values())
            for count, value in enumerate(value_list):
                if event in value:
                    roles.append(key_list[count])
            roles = ', '.join(roles)
        except AttributeError:
            roles = ''
        pending_record = ''
        if event in dcr.marking.pending:
            pending_record = '!'
        executed_record = ''
        if event in dcr.marking.executed:
            executed_record = '&#x2713;'
        label_map = ''
        if event in dcr.label_map:
            label_map = dcr.label_map[event]
        label = '{ ' + roles  + ' | ' + executed_record + ' ' + pending_record + ' } | { ' + label_map + ' }'
        included_style = 'solid'
        if event not in dcr.marking.included:
            included_style = 'dashed'
        viz.node(event, label, style=included_style,font_size=font_size)
    for event in dcr.conditions:
        for event_prime in dcr.conditions[event]:
            time = None
            if hasattr(dcr,'timedconditions') and event in dcr.timedconditions and event_prime in dcr.timedconditions[event]:
                time = dcr.timedconditions[event][event_prime]
            create_edge(event_prime, event, 'condition', viz, time, font_size)
    for event in dcr.responses:
        for event_prime in dcr.responses[event]:
            time = None
            if hasattr(dcr,'timedresponses') and event in dcr.timedresponses and event_prime in dcr.timedresponses[event]:
                time = dcr.timedresponses[event][event_prime]
            create_edge(event, event_prime, 'response', viz, time, font_size)
    for event in dcr.includes:
        for event_prime in dcr.includes[event]:
            create_edge(event, event_prime, 'include', viz)
    for event in dcr.excludes:
        for event_prime in dcr.excludes[event]:
            create_edge(event, event_prime, 'exclude', viz)
    if hasattr(dcr, 'noresponses'):
        for event in dcr.noresponses:
            for event_prime in dcr.noresponses[event]:
                create_edge(event, event_prime, 'noresponse', viz)
    if hasattr(dcr, 'milestones'):
        for event in dcr.milestones:
            for event_prime in dcr.milestones[event]:
                create_edge(event, event_prime, 'milestone', viz)

    viz.attr(overlap='false')

    viz.format = image_format.replace("html", "plain-text")

    return viz
