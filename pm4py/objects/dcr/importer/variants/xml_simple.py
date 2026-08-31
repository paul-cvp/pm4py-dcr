import copy

from datetime import timedelta
import isodate
from pandas import Timedelta

from pm4py.objects.dcr.extended.obj import ExtendedDcrGraph
from pm4py.objects.dcr.timed.obj import TimedDcrGraph
from pm4py.util import constants
from copy import deepcopy
from pm4py.objects.dcr.obj import Relations, dcr_template, DcrGraph

I = Relations.I.value
E = Relations.E.value
R = Relations.R.value
N = Relations.N.value
C = Relations.C.value
M = Relations.M.value


def apply(path, parameters=None):
    '''
    Reads a DCR Graph from an XML file

    Parameters
    ----------
    path
        Path to the XML file

    Returns
    -------
    DCR_Graph
        DCR Graph object
    '''
    if parameters is None:
        parameters = {}

    from lxml import etree, objectify

    parser = etree.XMLParser(remove_comments=True)
    xml_tree = objectify.parse(path, parser=parser)

    return import_xml_tree_from_root(xml_tree.getroot())


def import_xml_tree_from_root(root, replace_whitespace=' ', **kwargs):
    '''
    Transform the dictionary into a DCR_Graph object
    '''

    dcr = copy.deepcopy(dcr_template)
    for event_elem in root.findall('.//events'):
        event_id = event_elem.find('id').text.replace(' ', replace_whitespace)
        label = event_elem.find('label').text.replace(' ', replace_whitespace)
        dcr['events'].add(event_id)
        dcr['marking']['included'].add(event_id)
        dcr['labelMapping'][event_id] = label
        dcr['labels'].add(label)

    for rule_elem in root.findall('.//rules'):
        rule_type = rule_elem.find('type').text
        source = rule_elem.find('source').text.replace(' ', replace_whitespace)
        target = rule_elem.find('target').text.replace(' ', replace_whitespace)

        if rule_type == 'condition':
            if 'conditionsFor' not in dcr:
                dcr['conditionsFor'] = {}
            if target not in dcr['conditionsFor']:
                dcr['conditionsFor'][target] = set()
            dcr['conditionsFor'][target].add(source)

            # Handle duration
            duration_elem = rule_elem.find('duration')
            if duration_elem is not None:
                duration = timedelta(seconds=float(duration_elem.text))
                if 'conditionsForDelays' not in dcr:
                    dcr['conditionsForDelays'] = {}
                if target not in dcr['conditionsForDelays']:
                    dcr['conditionsForDelays'][target] = {}
                dcr['conditionsForDelays'][target][source] = duration

        elif rule_type == 'response':
            if 'responseTo' not in dcr:
                dcr['responseTo'] = {}
            if source not in dcr['responseTo']:
                dcr['responseTo'][source] = set()
            dcr['responseTo'][source].add(target)

            # Handle duration
            duration_elem = rule_elem.find('duration')
            if duration_elem is not None:
                duration = timedelta(seconds=float(duration_elem.text))
                if 'responseToDeadlines' not in dcr:
                    dcr['responseToDeadlines'] = {}
                if source not in dcr['responseToDeadlines']:
                    dcr['responseToDeadlines'][source] = {}
                dcr['responseToDeadlines'][source][target] = duration

        elif rule_type == 'include':
            if 'includesTo' not in dcr:
                dcr['includesTo'] = {}
            if source not in dcr['includesTo']:
                dcr['includesTo'][source] = set()
            dcr['includesTo'][source].add(target)

        elif rule_type == 'exclude':
            if 'excludesTo' not in dcr:
                dcr['excludesTo'] = {}
            if source not in dcr['excludesTo']:
                dcr['excludesTo'][source] = set()
            dcr['excludesTo'][source].add(target)

        elif rule_type == 'milestone':
            if 'milestonesFor' not in dcr:
                dcr['milestonesFor'] = {}
            if target not in dcr['milestonesFor']:
                dcr['milestonesFor'][target] = set()
            dcr['milestonesFor'][target].add(source)

        elif rule_type == 'coresponse':
            if 'noResponseTo' not in dcr:
                dcr['noResponseTo'] = {}
            if source not in dcr['noResponseTo']:
                dcr['noResponseTo'][source] = set()
            dcr['noResponseTo'][source].add(target)

    if len(dcr['noResponseTo'])>0 or len(dcr['milestonesFor'])>0:
        graph = ExtendedDcrGraph(dcr)
    elif len(dcr['responseToDeadlines'])>0 or len(dcr['conditionsForDelays'])>0:
        graph = TimedDcrGraph(dcr)
    else:
        graph = DcrGraph(dcr)
    return graph


def import_from_string(dcr_string, parameters=None):
    if parameters is None:
        parameters = {}

    if type(dcr_string) is str:
        dcr_string = dcr_string.encode(constants.DEFAULT_ENCODING)

    from lxml import etree, objectify

    parser = etree.XMLParser(remove_comments=True)
    root = objectify.fromstring(dcr_string, parser=parser)

    return import_xml_tree_from_root(root)
