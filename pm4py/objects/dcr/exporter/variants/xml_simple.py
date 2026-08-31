from lxml import etree

from pm4py.objects.dcr.obj import DcrGraph
from pm4py.objects.dcr.timed.obj import TimedDcrGraph


def export_dcr_graph(graph : DcrGraph, root, parents_dict=None, replace_whitespace=None, time_precision='H'):
    '''

    Parameters
    ----------
    dcr
    root
    parents_dict
    replace_whitespace
    time_precision: valid values are D H M S

    Returns
    -------

    '''
    if replace_whitespace is None:
        replace_whitespace = ' '

    for event in graph.events:
        xml_event = etree.SubElement(root, "events")
        xml_event_id = etree.SubElement(xml_event, "id")
        xml_event_id.text = event.replace(' ', replace_whitespace)
        xml_event_label = etree.SubElement(xml_event, "label")
        xml_event_label.text = event.replace(' ', replace_whitespace)
        if parents_dict and event in parents_dict:
            xml_event_parent = etree.SubElement(xml_event, "parent")
            xml_event_parent.text = parents_dict[event].replace(' ', replace_whitespace)

        for event_prime in graph.events:
            if event in graph.conditions and event_prime in graph.conditions[event]:
                xml_condition = etree.SubElement(root, "rules")
                xml_type = etree.SubElement(xml_condition, "type")
                xml_type.text = "condition"
                xml_source = etree.SubElement(xml_condition, "source")
                xml_source.text = event_prime.replace(' ', replace_whitespace)
                xml_target = etree.SubElement(xml_condition, "target")
                xml_target.text = event.replace(' ', replace_whitespace)
                if hasattr(graph, 'timedconditions') and event in graph.timedconditions and event_prime in graph.timedconditions[event]:
                    time = graph.timedconditions[event][event_prime]
                    if time.floor(freq='S').to_numpy() > 0:
                        xml_target = etree.SubElement(xml_condition, "duration")
                        iso_time = time.floor(freq='S').isoformat()
                        if time_precision:
                            iso_time = iso_time.split(time_precision)[0] + time_precision
                        xml_target.text = iso_time
            if event in graph.responses and event_prime in graph.responses[event]:
                xml_response = etree.SubElement(root, "rules")
                xml_type = etree.SubElement(xml_response, "type")
                xml_type.text = "response"
                xml_source = etree.SubElement(xml_response, "source")
                xml_source.text = event.replace(' ', replace_whitespace)
                xml_target = etree.SubElement(xml_response, "target")
                xml_target.text = event_prime.replace(' ', replace_whitespace)
                if hasattr(graph, 'timedresponses') and event in graph.timedresponses and event_prime in graph.timedresponses[event]:
                    time = graph.timedresponses[event][event_prime]
                    if time.floor(freq='S').to_numpy() > 0:
                        xml_target = etree.SubElement(xml_response, "duration")
                        iso_time = time.floor(freq='S').isoformat()
                        if time_precision:
                            iso_time = iso_time.split(time_precision)[0] + time_precision
                        xml_target.text = iso_time
            if event in graph.includes and event_prime in graph.includes[event]:
                xml_include = etree.SubElement(root, "rules")
                xml_type = etree.SubElement(xml_include, "type")
                xml_type.text = "include"
                xml_source = etree.SubElement(xml_include, "source")
                xml_source.text = event.replace(' ', replace_whitespace)
                xml_target = etree.SubElement(xml_include, "target")
                xml_target.text = event_prime.replace(' ', replace_whitespace)
            if event in graph.excludes and event_prime in graph.excludes[event]:
                xml_exclude = etree.SubElement(root, "rules")
                xml_type = etree.SubElement(xml_exclude, "type")
                xml_type.text = "exclude"
                xml_source = etree.SubElement(xml_exclude, "source")
                xml_source.text = event.replace(' ', replace_whitespace)
                xml_target = etree.SubElement(xml_exclude, "target")
                xml_target.text = event_prime.replace(' ', replace_whitespace)
            if hasattr(graph, 'milestones') and event in graph.milestones and event_prime in graph.milestones[event]:
                xml_exclude = etree.SubElement(root, "rules")
                xml_type = etree.SubElement(xml_exclude, "type")
                xml_type.text = "milestone"
                xml_source = etree.SubElement(xml_exclude, "source")
                xml_source.text = event.replace(' ', replace_whitespace)
                xml_target = etree.SubElement(xml_exclude, "target")
                xml_target.text = event_prime.replace(' ', replace_whitespace)
            if hasattr(graph, 'noresponses') and event in graph.noresponses and event_prime in graph.noresponses[event]:
                xml_exclude = etree.SubElement(root, "rules")
                xml_type = etree.SubElement(xml_exclude, "type")
                xml_type.text = "coresponse"
                xml_source = etree.SubElement(xml_exclude, "source")
                xml_source.text = event.replace(' ', replace_whitespace)
                xml_target = etree.SubElement(xml_exclude, "target")
                xml_target.text = event_prime.replace(' ', replace_whitespace)

        # TODO: export the marking with XML simple
        # if event in dcr['marking']['executed']:
        #     marking_exec = etree.SubElement(executed, "event")
        #     marking_exec.set("id", event)
        # if event in dcr['marking']['included']:
        #     marking_incl = etree.SubElement(included, "event")
        #     marking_incl.set("id", event)
        # if event in dcr['marking']['pending']:
        #     marking_pend = etree.SubElement(pendingResponse,"event")
        #     marking_pend.set("id",event)


def export_dcr_xml(graph: DcrGraph, output_file_name, dcr_title='DCR from pm4py', dcr_description=None, replace_whitespace=' '):
    '''
    Writes a DCR graph object to disk in the ``.xml`` file format (exported as ``.xml`` file).
    The file can be imported and visualised in the DCR solutions portal (https://dcrgraphs.net/)

    Parameters
    -----------
    dcr
        the DCR graph
    output_file_name
        dcrxml file name
    dcr_title
        title of the DCR graph
    dcr_description
        description of the DCR graph
    replace_whitespace
        a character to replace white space
    '''
    root = etree.Element("DCRModel")
    if dcr_title:
        title = etree.SubElement(root, "title")
        title.text = dcr_title
    if dcr_description:
        desc = etree.SubElement(root, "description")
        desc.text = dcr_description
    graph_type = etree.SubElement(root, "graphType")
    graph_type.text = "DCRModel"
    # this needs to exist so it can be imported inside dcr graphs with the app
    role = etree.SubElement(root, "roles")
    role_title = etree.SubElement(role, "title")
    role_title.text = "User"
    role_description = etree.SubElement(role, "description")
    role_description.text = "Dummy user"
    parents_dict = {}
    if hasattr(graph, 'subprocesses'):
        for sp_name, sp_events in graph.subprocesses.items():
            xml_event = etree.SubElement(root, "events")
            xml_event_id = etree.SubElement(xml_event, "id")
            xml_event_id.text = sp_name
            xml_event_label = etree.SubElement(xml_event, "label")
            xml_event_label.text = sp_name
            xml_event_type = etree.SubElement(xml_event, "type")
            xml_event_type.text = "subprocess"
            for sp_event in sp_events:
                parents_dict[sp_event] = sp_name
    if hasattr(graph, 'nestedgroups'):
        for n_name, n_events in graph.nestedgroups.items():
            xml_event = etree.SubElement(root, "events")
            xml_event_id = etree.SubElement(xml_event, "id")
            xml_event_id.text = n_name
            xml_event_label = etree.SubElement(xml_event, "label")
            xml_event_label.text = n_name
            xml_event_type = etree.SubElement(xml_event, "type")
            xml_event_type.text = "nesting"
            for n_event in n_events:
                parents_dict[n_event] = n_name
    if len(parents_dict) > 0:
        export_dcr_graph(graph, root, parents_dict, replace_whitespace=replace_whitespace)
    else:
        export_dcr_graph(graph, root, None, replace_whitespace=replace_whitespace)

    tree = etree.ElementTree(root)
    tree.write(output_file_name, pretty_print=True)