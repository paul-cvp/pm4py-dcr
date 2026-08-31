from pm4py.objects.petri_net import properties
from pm4py.objects.petri_net.obj import *
from pm4py.objects.dcr.obj import TemplateRelations as Relations

def check_arc_exists(source, target, tapn:PetriNet):
    if source in tapn.arc_matrix and target in tapn.arc_matrix[source]:
        return tapn.arc_matrix[source][target]
    else:
        return False

def add_arc_from_to_with_check(fr, to, net: PetriNet, weight=1, type=None, with_check=False) -> PetriNet.Arc:
    """
    TODO: merge add_arc_from_to into add_arc_from_to_apt
    Adds an arc from a specific element to another element in some net. Assumes from and to are in the net!

    Parameters
    ----------
    fr: transition/place from
    to:  transition/place to
    net: net to use
    weight: weight associated to the arc

    Returns
    -------
    None
    """
    a = PetriNet.Arc(fr, to, weight)
    if with_check and (fr and to):
       with_check = check_arc_exists(fr, to, net)
    if (fr and to) and not with_check:  # and not check_arc_exists(fr,to,net):
        if type is not None:
            a.properties[properties.ARCTYPE] = type
        net.arcs.add(a)
        fr.out_arcs.add(a)
        to.in_arcs.add(a)
        if fr not in net.arc_matrix:
            net.arc_matrix[fr] = {}
        net.arc_matrix[fr][to] = True

    return a

def map_existing_transitions_of_copy_0(delta, copy_0, t, tapn) -> (PetriNet, PetriNet.Transition):
    trans = copy_0[delta]
    # if trans in tapn.transitions: # since this is a copy this cannot be checked here. trust me bro
    in_arcs = trans.in_arcs
    for arc in in_arcs:
        source = arc.source
        type = arc.properties['arctype'] if 'arctype' in arc.properties else None
        add_arc_from_to_with_check(source, t, tapn, type=type, with_check=True)
    out_arcs = trans.out_arcs
    for arc in out_arcs:
        target = arc.target
        type = arc.properties['arctype'] if 'arctype' in arc.properties else None
        add_arc_from_to_with_check(t, target, tapn, type=type, with_check=True)
    return tapn, t


def create_event_pattern_transitions_and_arcs(tapn, event, helper_struct, mapping_exceptions):
    '''
    TODO: handle self no-response (do nothing) and self milestone (cannot execute the event if it is pending)
    Parameters
    ----------
    tapn
    event
    helper_struct
    mapping_exceptions

    Returns
    -------

    '''
    inc_place = helper_struct[event]['places']['included']
    exec_place = helper_struct[event]['places']['executed']
    pend_place = helper_struct[event]['places']['pending']
    pend_exc_place = helper_struct[event]['places']['pending_excluded']
    i_copy = helper_struct[event]['trans_group_index']
    ts = []
    for t_name in helper_struct[event]['t_types']:  # ['event','init','initpend','pend']:
        t = PetriNet.Transition(f'{t_name}_{event}{i_copy}', f'{t_name}_{event}{i_copy}_label')
        tapn.transitions.add(t)
        # this if statement handles self response exclude
        if event in mapping_exceptions.self_exceptions[frozenset([Relations.E.value, Relations.R.value])]:
            add_arc_from_to_with_check(t, pend_exc_place, tapn)

        add_arc_from_to_with_check(inc_place, t, tapn)
        # this if statement handles self exclude and self response exclude
        if not ((event in mapping_exceptions.self_exceptions[Relations.E.value]) or (
                event in mapping_exceptions.self_exceptions[frozenset([Relations.E.value, Relations.R.value])])):
            add_arc_from_to_with_check(t, inc_place, tapn)

        # this if statement handles self response
        if event in mapping_exceptions.self_exceptions[Relations.R.value]:
            add_arc_from_to_with_check(t, pend_place, tapn)

        if t_name.__contains__('init'):
            add_arc_from_to_with_check(t, exec_place, tapn)
            add_arc_from_to_with_check(exec_place, t, tapn, type='inhibitor')
        else:
            add_arc_from_to_with_check(t, exec_place, tapn)
            add_arc_from_to_with_check(exec_place, t, tapn)

        if t_name.__contains__('pend'):
            add_arc_from_to_with_check(pend_place, t, tapn)
        else:
            add_arc_from_to_with_check(pend_place, t, tapn, type='inhibitor')
        ts.append(t)
    helper_struct[event]['trans_group_index'] += 1
    return tapn, ts


def get_expected_places_transitions_arcs(G):
    # 3^(conditions + milestones) * 2^((inc+exc)+(resp+no_resp))*2 for each event in relations
    expected_transitions = 0
    # 3*no of events
    expected_places = 4 * len(G['events'])
    # arcs:
    #   - events * 12
    #   - conditions * 9
    #   - milestones * 8
    #   - responses * 2
    #   - noResponses * 2
    #   - includes * 2
    #   - exludes * 2
    expected_arcs = 0

    for event in G['events']:
        expected_transitions += ((3 ** (len(G['conditionsFor'][event]) if event in G['conditionsFor'] else 0 +
len(G['milestonesFor'][event]) if event in G['milestonesFor'] else 0)) * (3 ** ((len(G['includesTo'][event]) if event in G['includesTo'] else 0 +
len(G['excludesTo'][event]) if event in G['excludesTo'] else 0)) * (4 ** (len(G['responseTo'][event]) if event in G['responseTo'] else 0 +
len(G['noResponseTo'][event]) if event in G['noResponseTo'] else 0)))) * 4
        expected_arcs += 2 ^ ((3 ^ (len(set(G['includesTo'][event] if event in G['includesTo'] else set()).union(
            set(G['excludesTo'][event] if event in G['excludesTo'] else set()))))) *
                              (4 ^ (len(set(G['responseTo'][event] if event in G['responseTo'] else set()).union(
                                  set(G['noResponseTo'][event] if event in G['noResponseTo'] else set()))))) *
                              (3 ^ ((len(set(G['conditionsFor'][event])) if event in G['conditionsFor'] else 0))) *
                              (3 ^ ((len(set(G['milestonesFor'][event])) if event in G['milestonesFor'] else 0))))

    expected_arcs += len(G['events']) * 24
    return expected_places, expected_transitions, expected_arcs
