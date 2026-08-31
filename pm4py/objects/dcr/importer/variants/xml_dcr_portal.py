import copy

import isodate

from pm4py.util import constants
from copy import deepcopy
from pm4py.objects.dcr.obj import Relations, dcr_template
from pm4py.objects.dcr.utils.utils import cast_to_dcr_object, clean_input, clean_input_as_dict

I = Relations.I.value
E = Relations.E.value
R = Relations.R.value
N = Relations.N.value
C = Relations.C.value
M = Relations.M.value


def apply(path, parameters=None):
    '''
    Reads a DCR graph from an XML file
    Marquard et al. "Web-Based Modelling and Collaborative Simulation of Declarative Processes" https://doi.org/10.1007/978-3-319-23063-4_15
    Parameters
    ----------
    path
        Path to the XML file
    parameters
        Params
    Returns
    -------
    dcr
        DCR graph object
    '''
    if parameters is None:
        parameters = {}

    from lxml import etree, objectify

    parser = etree.XMLParser(remove_comments=True)
    xml_tree = objectify.parse(path, parser=parser)

    return import_xml_tree_from_root(xml_tree.getroot(), **parameters)


def import_xml_tree_from_root(root, white_space_replacement=' ', as_dcr_object=True, labels_as_ids=True):
    dcr = copy.deepcopy(dcr_template)
    dcr = __parse_element__(root, None, dcr)
    dcr = clean_input_as_dict(dcr, white_space_replacement=white_space_replacement)

    if labels_as_ids:
        from pm4py.objects.dcr.utils.utils import map_labels_to_events
        dcr = map_labels_to_events(dcr)
    '''
    Transform the dictionary into a DCRGraph object
    '''
    if as_dcr_object:
        return cast_to_dcr_object(dcr)
    else:
        return dcr


def import_from_string(dcr_string, parameters=None):
    if parameters is None:
        parameters = {}

    if type(dcr_string) is str:
        dcr_string = dcr_string.encode(constants.DEFAULT_ENCODING)

    from lxml import etree, objectify

    parser = etree.XMLParser(remove_comments=True)
    root = objectify.fromstring(dcr_string, parser=parser)

    return import_xml_tree_from_root(root)


def __parse_element__(curr_el, parent, dcr):
    # Create the DCR graph
    tag = curr_el.tag.lower()
    match tag:
        case 'event':
            id = curr_el.get('id')
            if id:
                dcr['events'].add(id)
                event_type = curr_el.get('type')
                match event_type:
                    case 'subprocess':
                        dcr['subprocesses'][id] = set()
                    case 'nesting':
                        dcr['nestedgroups'][id] = set()
                        pass
                    case _:
                        pass
                match parent.get('type'):
                    case 'subprocess':
                        dcr['subprocesses'][parent.get('id')].add(id)
                    case 'nesting':
                        dcr['nestedgroups'][parent.get('id')].add(id)
                        pass
                    case _:
                        pass
                match parent.tag:
                    case 'included' | 'executed':
                        dcr['marking'][parent.tag].add(id)
                    case 'pendingResponses':
                        dcr['marking']['pending'].add(id)
                        initial_deadline = curr_el.get('deadline')
                        if initial_deadline:
                            if initial_deadline.isdecimal():
                                initial_deadline = int(initial_deadline)
                            else:
                                initial_deadline = isodate.parse_duration(initial_deadline)
                            dcr['marking']['pendingDeadline'][id] = initial_deadline
                    case _:
                        pass
                for role in curr_el.findall('.//role'):
                    if role.text:
                        if role.text not in dcr['roleAssignments']:
                            dcr['roleAssignments'][role.text] = set([id])
                        else:
                            dcr['roleAssignments'][role.text].add(id)
                for role in curr_el.findall('.//readRole'):
                    if role.text:
                        if role.text not in dcr['readRoleAssignments']:
                            dcr['readRoleAssignments'][role.text] = set([id])
                        else:
                            dcr['readRoleAssignments'][role.text].add(id)
        case 'label':
            id = curr_el.get('id')
            dcr['labels'].add(id)
        case 'labelmapping':
            eventId = curr_el.get('eventId')
            labelId = curr_el.get('labelId')
            if eventId not in dcr['labelMapping']:
                dcr['labelMapping'][eventId] = labelId
                # dcr['labelMapping'][eventId] = set()
            # dcr['labelMapping'][eventId].add(labelId)
        case 'condition':
            event = curr_el.get('sourceId')
            event_prime = curr_el.get('targetId')
            filter_level = curr_el.get('filterLevel')
            iso_description = curr_el.get('description')  # might have an ISO format duration
            description = None
            if iso_description:
                description = iso_description.strip()  # might have an ISO format duration
            delay = curr_el.get('time')
            groups = curr_el.get('groups')
            if not dcr['conditionsFor'].__contains__(event_prime):
                dcr['conditionsFor'][event_prime] = set()
            dcr['conditionsFor'][event_prime].add(event)

            if delay:
                if not dcr['conditionsForDelays'].__contains__(event_prime):
                    dcr['conditionsForDelays'][event_prime] = {}
                if delay.isdecimal():
                    delay = int(delay)
                else:
                    delay = isodate.parse_duration(delay)
                dcr['conditionsForDelays'][event_prime][event] = delay

        case 'response':
            event = curr_el.get('sourceId')
            event_prime = curr_el.get('targetId')
            filter_level = curr_el.get('filterLevel')
            iso_description = curr_el.get('description')  # might have an ISO format duration
            description = None
            if iso_description:
                description = iso_description.strip()  # might have an ISO format duration
            deadline = curr_el.get('time')
            groups = curr_el.get('groups')
            if not dcr['responseTo'].__contains__(event):
                dcr['responseTo'][event] = set()
            dcr['responseTo'][event].add(event_prime)

            if deadline:
                if not dcr['responseToDeadlines'].__contains__(event):
                    dcr['responseToDeadlines'][event] = {}
                if deadline.isdecimal():
                    deadline = int(deadline)
                else:
                    deadline = isodate.parse_duration(deadline)
                dcr['responseToDeadlines'][event][event_prime] = deadline
        case 'role':
            if curr_el.text:
                dcr['roles'].add(curr_el.text)
                if curr_el.text not in dcr['roleAssignments']:
                    dcr['roleAssignments'][curr_el.text] = set()
                if curr_el.text not in dcr['readRoleAssignments']:
                    dcr['readRoleAssignments'][curr_el.text] = set()
        case 'include' | 'exclude':
            event = curr_el.get('sourceId')
            event_prime = curr_el.get('targetId')
            filter_level = curr_el.get('filterLevel')
            iso_description = curr_el.get('description')  # might have an ISO format duration
            description = None
            if iso_description:
                description = iso_description.strip()  # might have an ISO format duration
            deadline = curr_el.get('time')
            groups = curr_el.get('groups')
            if not dcr[f'{tag}sTo'].__contains__(event):
                dcr[f'{tag}sTo'][event] = set()
            dcr[f'{tag}sTo'][event].add(event_prime)
        case 'coresponse' | 'noresponse':
            event = curr_el.get('sourceId')
            event_prime = curr_el.get('targetId')
            filter_level = curr_el.get('filterLevel')
            iso_description = curr_el.get('description')  # might have an ISO format duration
            description = None
            if iso_description:
                description = iso_description.strip()  # might have an ISO format duration
            deadline = curr_el.get('time')
            groups = curr_el.get('groups')
            if not dcr[f'noResponseTo'].__contains__(event):
                dcr[f'noResponseTo'][event] = set()
            dcr[f'noResponseTo'][event].add(event_prime)
        case 'milestone':
            event = curr_el.get('sourceId')
            event_prime = curr_el.get('targetId')
            filter_level = curr_el.get('filterLevel')
            iso_description = curr_el.get('description')  # might have an ISO format duration
            description = None
            if iso_description:
                description = iso_description.strip()  # might have an ISO format duration
            deadline = curr_el.get('time')
            groups = curr_el.get('groups')
            if not dcr[f'{tag}sFor'].__contains__(event_prime):
                dcr[f'{tag}sFor'][event_prime] = set()
            dcr[f'{tag}sFor'][event_prime].add(event)
        case _:
            pass
    for child in curr_el:
        dcr = __parse_element__(child, curr_el, dcr)

    return dcr
