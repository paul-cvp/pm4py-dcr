from copy import deepcopy
from enum import Enum, auto
import pandas as pd
import networkx as nx
from typing import Optional, Any, Union, Dict

from pm4py.objects.dcr.obj import dcr_template, DcrGraph, TemplateRelations as Relations
from pm4py.objects.dcr.hierarchical.obj import HierarchicalDcrGraph
from pm4py.objects.log.obj import EventLog


class NestVariants(Enum):
    CHOICE = auto()
    NEST = auto()
    CHOICE_NEST = auto()


def apply(graph, parameters):
    """
    this method calls the nesting miner

    Parameters
    ----------
    log: EventLog | pandas.Dataframe
        Event log to use in the role miner
    graph: DCR_Graph
        Dcr graph to apply additional attributes to
    parameters
        Parameters of the algorithm, including:
            nest_variant : the nesting algorithm to use from the enum above: CHOICE|NEST|CHOICE_NEST
    Returns
    -------
    :class:´GroupSubprocessDcrGraph`
        return a DCR graph, that contains nested groups
    """
    nesting_mine = NestingMining()
    return nesting_mine.mine(graph, parameters)


class NestingMining:
    """
    The NestingMining provides a simple algorithm to mine nestings

    After initialization, user can call mine(log, G, parameters), which will return a DCR Graph with nested groups.

    Reference paper:
    Cosma et al. "Improving Simplicity by Discovering Nested Groups in Declarative Models" https://doi.org/10.1007/978-3-031-61057-8_26
    Attributes
    ----------
    graph: Dict[str,Any]
        A template that will be used collecting organizational data

    Methods
    -------
    mine(log, G, parameters)
        calls the main mining function, extract nested groups

    Notes
    ------
    *
    """

    def mine(self, graph, parameters: Optional[Dict[str, Any]]):
        """
        Main nested groups mining algorithm

        Parameters
        ----------
        graph: DCRGraph
            DCR graph to append additional attributes
        parameters: Optional[Dict[str, Any]]
            optional parameters used for role mining
        Returns
        -------
        NestedDCRGraph(G, dcr)
            returns a DCR graph with nested groups
        """
        nest_variant = NestVariants.CHOICE_NEST
        if 'nest_variant' in parameters:
            nest_variant = parameters['nest_variant']
        # from the parameters ask which type of nesting do you want
        match nest_variant.value:
            case NestVariants.CHOICE.value:
                return self.apply_choice(graph)
            case NestVariants.NEST.value:
                return self.apply_nest(graph)
            case NestVariants.CHOICE_NEST.value:
                return self.apply_nest(self.apply_choice(graph))

    def apply_choice(self, graph):
        choice = Choice()
        return choice.apply_choice(graph)

    def apply_nest(self, graph):
        existing_nestings = deepcopy(graph.nestedgroups) if len(graph.nestedgroups)>0 else None
        nesting = Nesting()
        nesting.create_encoding(graph.obj_to_template())
        nesting.nest(graph.events)
        nesting.remove_redundant_nestings()
        return nesting.get_nested_dcr_graph(graph,existing_nestings)


class Choice(object):

    def __init__(self):
        self.nesting_template = {"nestedgroups": {}, "nestedgroupsMap": {}, "subprocesses": {}}

    def apply_choice(self, graph):
        self.get_mutual_exclusions(graph)
        for name, me_events in self.nesting_template['nestedgroups'].items():
            graph.events.add(name)
            graph.marking.included.add(name)
            for me_event in me_events:
                self.nesting_template['nestedgroupsMap'][me_event] = name
                for me_prime in me_events:
                    graph.excludes[me_event].discard(me_prime)
                    graph.excludes[me_prime].discard(me_event)
            graph.excludes[name] = set([name])

        from pm4py.objects.dcr.obj import Relations as ObjRel
        for name, me_events in self.nesting_template['nestedgroups'].items():
            external_events_to_check = graph.events.difference(me_events.union(set(name)))
            for r in [ObjRel.C,ObjRel.R,ObjRel.I,ObjRel.E]:
                rel = r.value
                for e in external_events_to_check:
                    all_internal_same_relation = True
                    for internal_event in me_events:
                        all_internal_same_relation &= internal_event in getattr(graph, rel) and e in getattr(graph, rel)[internal_event]
                    if all_internal_same_relation:
                        if name not in getattr(graph, rel):
                            getattr(graph, rel)[name] = set()
                        getattr(graph, rel)[name].add(e)
                        for internal_event in me_events:
                            getattr(graph, rel)[internal_event].remove(e)
                for e in external_events_to_check:
                    all_internal_same_relation = True
                    for internal_event in me_events:
                        all_internal_same_relation &= e in getattr(graph, rel) and internal_event in getattr(graph, rel)[e]
                    if all_internal_same_relation:
                        if name not in getattr(graph, rel):
                            getattr(graph, rel)[e] = set()
                        getattr(graph, rel)[e].add(name)
                        getattr(graph, rel)[e] = getattr(graph, rel)[e].difference(me_events)
        return HierarchicalDcrGraph({**graph.obj_to_template(), **self.nesting_template})

    def get_mutual_exclusions(self, dcr, i:Optional[int]=0):
        """
        Get nested groups based on cliques. Updates the self.nesting_template dict
        Parameters
        ----------
        dcr
            A core Dcr Graph as mined from the DisCoveR miner
        i
            An integer seed for the naming of choice groups
        Returns
        -------

        """

        graph = self.get_mutually_excluding_graph(dcr)
        cliques = list(frozenset(s) for s in nx.enumerate_all_cliques(graph) if len(s) > 1)
        cliques = sorted(cliques, key=len, reverse=True)
        used_cliques = {}
        for c in cliques:
            used_cliques[c] = False

        used_events = set()
        for clique in cliques:
            if not used_cliques[clique]:
                if len(clique.intersection(used_events)) == 0:
                    # any new mutually exclusive subprocess must be disjoint from all existing ones
                    i += 1
                    self.nesting_template['nestedgroups'][f'Choice{i}'] = set(clique)
                    used_cliques[clique] = True
                    used_events = used_events.union(clique)

    def get_mutually_excluding_graph(self, graph):
        ind = pd.Index(sorted(graph.events), dtype=str)
        rel_matrix = pd.DataFrame(0, columns=ind, index=ind, dtype=int)
        for e in graph.events:
            for e_prime in graph.events:
                if e in graph.excludes and e_prime in graph.excludes[e]:
                    rel_matrix.at[e, e_prime] = 1

        self_excluding = set()
        for e in graph.events:
            if rel_matrix.at[e, e] == 1:
                self_excluding.add(e)
        mutually_excluding = []
        for e in self_excluding:
            for e_prime in self_excluding:
                if e != e_prime and rel_matrix.at[e, e_prime] == 1 and rel_matrix.at[e_prime, e] == 1:
                    if (e, e_prime) not in mutually_excluding and (e_prime, e) not in mutually_excluding:
                        mutually_excluding.append((e, e_prime))

        return nx.from_edgelist(mutually_excluding)

class Nesting(object):

    def __init__(self):
        self.nesting_template = {"nestedgroups": {}, "nestedgroupsMap": {}, "subprocesses": {}}
        self.nesting_ids = set()
        self.nesting_map = {}
        self.nest_id = 0
        self.enc = None
        self.in_rec_step = 0
        self.out_rec_step = 0
        self.debug = False

    def encode(self, G):
        enc = {}
        for e in G['events']:
            enc[e] = set()
        for e in G['events']:
            for e_prime in G['events']:
                for rel in Relations:
                    if e in G[rel.value] and e_prime in G[rel.value][e]:
                        if rel in [Relations.C, Relations.M]:
                            enc[e].add((e_prime, rel.value, 'in'))
                        else:
                            enc[e].add((e_prime, rel.value, 'out'))
                    if e_prime in G[rel.value] and e in G[rel.value][e_prime]:
                        if rel in [Relations.C, Relations.M]:
                            enc[e].add((e_prime, rel.value, 'out'))
                        else:
                            enc[e].add((e_prime, rel.value, 'in'))
        return enc

    def get_opposite_rel_dict_str(self, relStr, direction, event, nestingId):
        relation_dict_str_del = (event, relStr, "out" if direction == "in" else "in")
        relation_dict_str_add = (nestingId, relStr, "out" if direction == "in" else "in")

        return relation_dict_str_del, relation_dict_str_add

    def create_encoding(self, dcr_graph):
        self.enc = self.encode(dcr_graph)

    def find_largest_nesting(self, events_source, parent_nesting=None):
        cands = {}
        events = deepcopy(events_source)
        for e in events:
            for j in events:
                arrow_s = frozenset(self.enc[e].intersection(self.enc[j]))
                if len(arrow_s) > 0:
                    if not arrow_s in cands:
                        cands[arrow_s] = set([])
                    cands[arrow_s] = cands[arrow_s].union(set([e, j]))

        best_score = 0
        best = None
        for arrow_s in cands.keys():
            cand_score = (len(cands[arrow_s]) - 1) * len(arrow_s)
            if cand_score > best_score:
                best_score = cand_score
                best = arrow_s

        if best and len(cands[best]) > 1 and len(best) >= 1:
            if self.debug:
                print(
                    f'[out]:{self.out_rec_step} [in]:{self.in_rec_step} \n'
                    f'     [events] {events} \n'
                    f'[cands[best]] {cands[best]} \n'  # these are the events inside the nesting
                    f'       [best] {best} \n'
                    f'        [enc] {self.enc} \n '
                    f'      [cands] {cands} \n'
                )
            self.nest_id += 1
            nest_event = f'Group{self.nest_id}'
            self.nesting_ids.add(nest_event)
            self.enc[nest_event] = set(best)

            if parent_nesting:
                parent_nesting['events'] = parent_nesting['events'].difference(cands[best])
                parent_nesting['events'].add(nest_event)
                self.nesting_map[nest_event] = parent_nesting['id']

            for e in cands[best]:
                self.nesting_map[e] = nest_event
                self.enc[e] = self.enc[e].difference(best)
                for (e_prime, rel, direction) in best:
                    op_rel_del, op_rel_add = self.get_opposite_rel_dict_str(rel, direction, e, nest_event)
                    # TODO: find out why sometimes it tries to remove non-existing encodings
                    self.enc[e_prime].discard(op_rel_del)  # .remove(op_rel_del)
                    self.enc[e_prime].add(op_rel_add)

            retval = [{'nestingEvents': cands[best], 'sharedRels': best}]
            found = True
            while found:
                temp_retval = self.find_largest_nesting(events_source=cands[best], parent_nesting={'id': f'Group{self.nest_id}', 'events': cands[best]})
                if temp_retval and len(temp_retval) > 0:
                    retval.extend(temp_retval)
                    for tmp in temp_retval:
                        events = events.difference(tmp['nestingEvents'])
                else:
                    found = False
                self.in_rec_step += 1
            return retval

    def nest(self, events_source):
        nestings_arr = [{'nestingEvents': set(), 'sharedRels': set()}]
        events = deepcopy(events_source)

        while True:
            temp_retval = self.find_largest_nesting(events)
            if temp_retval and len(temp_retval) > 0:
                nestings_arr.extend(temp_retval)
                for tmp in temp_retval:
                    events = events.difference(tmp['nestingEvents'])
            else:
                break
            self.out_rec_step += 1

        return self.nesting_map, self.nesting_ids

    def remove_redundant_nestings(self):
        nestings = {}
        for n in self.nesting_ids:
            nestings[n] = set()
        for k, v in self.nesting_map.items():
            nestings[v].add(k)

        # Removing redundant nestings
        nests_to_remove = set([])
        for key in nestings:
            val = nestings[key]
            if len(val) == 1:
                nests_to_remove.add(list(val)[0])

        for nest_to_remove in nests_to_remove:
            parent = self.nesting_map[nest_to_remove]
            for k, v in list(self.nesting_map.items()):
                if v == nest_to_remove:
                    self.nesting_map[k] = parent
            print("Deleting: ", nest_to_remove)
            del self.nesting_map[nest_to_remove]
            self.nesting_ids.remove(nest_to_remove)

            for e, v in deepcopy(list(self.enc.items())):
                for r in v:  #I get a set changed error here
                    (e_prime, rel, direction) = r
                    if e_prime == nest_to_remove:
                        self.enc[e].remove(r)
                        self.enc[e].add((parent, rel, direction))
                if e == nest_to_remove:
                    self.enc[parent] = self.enc[parent].union(self.enc[e])
                    del self.enc[e]

    def should_add(self, rel, direction):
        return direction == 'in' if rel in [Relations.C.value, Relations.M.value] else direction == 'out'

    def get_nested_dcr_graph(self, graph, existing_nestings=None):
        res_dcr = graph.obj_to_template()
        events = set(self.enc.keys())
        res_dcr['events'] = events
        res_dcr['marking']['included'] = events

        for n in self.nesting_ids:
            res_dcr['nestedgroups'][n] = set()
        for k, v in self.nesting_map.items():
            res_dcr['nestedgroups'][v].add(k)

        for e, v in self.enc.items():
            for e_prime, rel, direction in v:
                if self.should_add(rel, direction):
                    if e not in res_dcr[rel]:
                        res_dcr[rel][e] = set()
                    res_dcr[rel][e].add(e_prime)

        if existing_nestings:
            for me, me_events in existing_nestings.items():
                if me not in res_dcr['nestedgroups']:
                    res_dcr['nestedgroups'][me] = set()
                for me_event in me_events:
                    if me_event in self.nesting_map:
                        highest_nesting = self.nesting_map[me_event]
                        while True:
                            if highest_nesting in self.nesting_map:
                                highest_nesting = self.nesting_map[highest_nesting]
                            else:
                                break
                        if highest_nesting not in res_dcr['nestedgroups'][me]:
                            res_dcr['nestedgroups'][me].add(highest_nesting)
                    else:
                        res_dcr['nestedgroups'][me].add(me_event)
                    self.nesting_map[me_event] = me
                if self.debug:
                    print(self.nesting_map[me])
                    print(self.nesting_map)
                    print(res_dcr['nestedgroups'])

        res_dcr['nestedgroupsMap'] = deepcopy(self.nesting_map)

        return HierarchicalDcrGraph(res_dcr)
        # return res_dcr
