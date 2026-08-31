from lxml import etree

from pm4py.objects.dcr.obj import DcrGraph


def export_dcr_xml(graph:DcrGraph, output_file_name, dcr_title='DCR from pm4py',**parameters):
    '''
    Writes a DCR graph object to disk in the ``.xml`` file format (exported as ``.xml`` file).
    Marquard et al. "Web-Based Modelling and Collaborative Simulation of Declarative Processes" https://doi.org/10.1007/978-3-319-23063-4_15
    Parameters
    -----------
    dcr
        the DCR graph
    output_file_name
        dcrxml file name
    dcr_title
        title of the DCR graph
    '''
    root = etree.Element("dcrgraph")
    if dcr_title:
        root.set("title", dcr_title)
    specification = etree.SubElement(root, "specification")
    resources = etree.SubElement(specification, "resources")
    events = etree.SubElement(resources, "events")
    labels = etree.SubElement(resources, "labels")
    labelMappings = etree.SubElement(resources, "labelMappings")

    constraints = etree.SubElement(specification, "constraints")
    conditions = etree.SubElement(constraints, "conditions")
    responses = etree.SubElement(constraints, "responses")
    excludes = etree.SubElement(constraints, "excludes")
    includes = etree.SubElement(constraints, "includes")

    runtime = etree.SubElement(root, "runtime")
    marking = etree.SubElement(runtime, "marking")
    executed = etree.SubElement(marking, "executed")
    included = etree.SubElement(marking, "included")
    pendingResponse = etree.SubElement(marking, "pendingResponses")

    for event in graph.events:
        xml_event = etree.SubElement(events, "event")
        xml_event.set("id", event)
        xml_label = etree.SubElement(labels, "label")
        xml_label.set("id", event)
        xml_labelMapping = etree.SubElement(labelMappings, "labelMapping")
        xml_labelMapping.set("eventId", event)
        xml_labelMapping.set("labelId", event)

        for event_prime in graph.events:
            if event in graph.conditions and event_prime in graph.conditions[event]:
                xml_condition = etree.SubElement(conditions, "condition")
                xml_condition.set("sourceId", event_prime)
                xml_condition.set("targetId", event)
            if event in graph.responses and event_prime in graph.responses[event]:
                xml_response = etree.SubElement(responses, "response")
                xml_response.set("sourceId", event)
                xml_response.set("targetId", event_prime)
            if event in graph.includes and event_prime in graph.includes[event]:
                xml_include = etree.SubElement(includes, "include")
                xml_include.set("sourceId", event)
                xml_include.set("targetId", event_prime)
            if event in graph.excludes and event_prime in graph.excludes[event]:
                xml_exclude = etree.SubElement(excludes, "exclude")
                xml_exclude.set("sourceId", event)
                xml_exclude.set("targetId", event_prime)
            # TODO: allow for more advanced graphs than just the core ones
        if event in graph.marking.executed:
            marking_exec = etree.SubElement(executed, "event")
            marking_exec.set("id", event)
        if event in graph.marking.included:
            marking_incl = etree.SubElement(included, "event")
            marking_incl.set("id", event)
        if event in graph.marking.pending:
            marking_pend = etree.SubElement(pendingResponse, "event")
            marking_pend.set("id", event)

    tree = etree.ElementTree(root)
    tree.write(output_file_name, pretty_print=True)
