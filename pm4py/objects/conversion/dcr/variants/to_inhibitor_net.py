import os

from pm4py.objects.petri_net.obj import *
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter

from pm4py.objects.conversion.dcr.variants.to_petri_net_submodules import exceptional_cases, single_relations, preoptimizer, utils


class Dcr2PetriNet(object):

    def __init__(self, preoptimize=True, postoptimize=True, map_unexecutable_events=False, debug=False, **kwargs)  -> None:
        """
        Init the conversion object
        Parameters
        ----------
        preoptimize : If True it will remove unreachable DCR markings based on the DCR behaviour
        postoptimize : If True it will remove dead transitions based on the underlying petri net reachability graph
        map_unexecutable_events : If True it will map unexecutable events
        debug : If True it will print debug information
        kwargs
        """
        self.in_t_types = ['event', 'init', 'initpend', 'pend']
        self.helper_struct = {}
        self.preoptimize = preoptimize
        self.postoptimize = postoptimize
        self.map_unexecutable_events = map_unexecutable_events
        self.preoptimizer = preoptimizer.Preoptimizer()
        self.transitions = {}
        self.mapping_exceptions = None
        self.reachability_timeout = None
        self.print_steps = debug
        self.debug = debug

    def initialize_helper_struct(self, graph: dict) -> None:
        """
        Initializes a helper structure to keep track of DCR Events and their related places and transitions in the Petri Net
        Parameters
        ----------
        graph
            the DcrGraph
        Returns
        -------
            None
        """
        for event in graph['events']:
            self.helper_struct[event] = {}
            self.helper_struct[event]['places'] = {}
            self.helper_struct[event]['places']['included'] = None
            self.helper_struct[event]['places']['pending'] = None
            self.helper_struct[event]['places']['pending_excluded'] = None
            self.helper_struct[event]['places']['executed'] = None
            self.helper_struct[event]['transitions'] = []
            self.helper_struct[event]['trans_group_index'] = 0
            self.helper_struct[event]['t_types'] = self.in_t_types

            self.transitions[event] = {}
            for event_prime in graph['events']:
                self.transitions[event][event_prime] = []

    def create_event_pattern_places(self, event: str, graph: dict, net: PetriNet, m: Marking) -> (InhibitorNet, Marking):
        """
        Creates petri net places and the petri net marking for a single event
        """
        default_make_included = True
        default_make_pend = True
        default_make_pend_ex = True
        default_make_exec = True
        if self.preoptimize:
            default_make_included = event in self.preoptimizer.need_included_place
            default_make_pend = event in self.preoptimizer.need_pending_place
            default_make_pend_ex = event in self.preoptimizer.need_pending_excluded_place
            default_make_exec = event in self.preoptimizer.need_executed_place

        if default_make_included:
            inc_place = PetriNet.Place(f'included_{event}')
            net.places.add(inc_place)
            self.helper_struct[event]['places']['included'] = inc_place
            # fill the marking
            if event in graph['marking']['included']:
                m[inc_place] = 1

        if default_make_pend:
            pend_place = PetriNet.Place(f'pending_{event}')
            net.places.add(pend_place)
            self.helper_struct[event]['places']['pending'] = pend_place
            # fill the marking
            if event in graph['marking']['pending'] and event in graph['marking']['included']:
                m[pend_place] = 1

        if default_make_pend_ex:
            pend_excl_place = PetriNet.Place(f'pending_excluded_{event}')
            net.places.add(pend_excl_place)
            self.helper_struct[event]['places']['pending_excluded'] = pend_excl_place
            # fill the marking
            if event in graph['marking']['pending'] and not event in graph['marking']['included']:
                m[pend_excl_place] = 1

        if default_make_exec:
            exec_place = PetriNet.Place(f'executed_{event}')
            net.places.add(exec_place)
            self.helper_struct[event]['places']['executed'] = exec_place
            # fill the marking
            if event in graph['marking']['executed']:
                m[exec_place] = 1
        if self.preoptimize:
            ts = ['event']
            if default_make_exec and not event in graph['marking']['executed'] and not event in self.preoptimizer.no_init_t:
                ts.append('init')
            if default_make_exec and default_make_pend and not event in self.preoptimizer.no_initpend_t:
                ts.append('initpend')
            if default_make_pend:
                ts.append('pend')
            self.helper_struct[event]['t_types'] = ts

        return net, m

    def create_event_pattern(self, event: str, graph: dict, net: PetriNet, m: Marking) -> (InhibitorNet, Marking):
        """
        Creates the petri net for a single event
        """
        net, m = self.create_event_pattern_places(event, graph, net, m)
        net, ts = utils.create_event_pattern_transitions_and_arcs(net, event, self.helper_struct,
                                                                  self.mapping_exceptions)
        self.helper_struct[event]['transitions'].extend(ts)
        return net, m

    def post_optimize_petri_net_reachability_graph(self, net, m, graph=None, merge_parallel_places=True) -> InhibitorNet:
        """
        Removes dead regions in the petri net based on the reachability graph.
        Parameters
        ----------
        merge_parallel_places
            If True it will remove duplicate places that behave the same in their marking
        Returns
        -------
        Reduced petri net
        """
        from pm4py.objects.petri_net.utils import petri_utils
        from pm4py.objects.petri_net.inhibitor_reset import semantics as inhibitor_semantics
        from pm4py.objects.conversion.dcr.variants import reachability_analysis
        max_elab_time = 2 * 60 * 60  # 2 hours
        if self.reachability_timeout:
            max_elab_time = self.reachability_timeout
        trans_sys = reachability_analysis.construct_reachability_graph(net, m, use_trans_name=True,
                                                                    parameters={
                                                                        'petri_semantics': inhibitor_semantics.InhibitorResetSemantics(),
                                                                        'max_elab_time': max_elab_time
                                                                    })
        if self.debug:
            from pm4py.visualization.transition_system import visualizer as ts_visualizer
            gviz = ts_visualizer.apply(trans_sys, parameters={ts_visualizer.Variants.VIEW_BASED.value.Parameters.FORMAT: "png"})
            ts_visualizer.view(gviz)
        fired_transitions = set()

        for transition in trans_sys.transitions:
            fired_transitions.add(transition.name)

        ts_to_remove = set()
        for t in net.transitions:
            if t.name not in fired_transitions:
                ts_to_remove.add(t)
        for t in ts_to_remove:
            net = petri_utils.remove_transition(net, t)

        changed_places = set()
        for state_list in trans_sys.states:
            for state in state_list.name:
                changed_places.add(state)

        parallel_places = set()
        places_to_rename = {}
        ps_to_remove = set(net.places).difference(changed_places)

        if graph and merge_parallel_places:
            for event in graph['events']:
                for type, event_place in self.helper_struct[event]['places'].items():
                    for type_prime, event_place_prime in self.helper_struct[event]['places'].items():
                        if event_place and event_place_prime and event_place.name != event_place_prime.name and \
                                event_place not in parallel_places:
                            is_parallel = False
                            ep_ins = event_place.in_arcs
                            epp_ins = event_place_prime.in_arcs
                            ep_outs = event_place.out_arcs
                            epp_outs = event_place_prime.out_arcs
                            if len(ep_ins) == len(epp_ins) and len(ep_outs) == len(epp_outs):
                                ep_sources = set()
                                epp_sources = set()
                                for ep_in in ep_ins:
                                    ep_sources.add(ep_in.source)
                                for epp_in in epp_ins:
                                    epp_sources.add(epp_in.source)
                                ep_targets = set()
                                epp_targets = set()
                                for ep_out in ep_outs:
                                    ep_targets.add(ep_out.target)
                                for epp_out in epp_outs:
                                    epp_targets.add(epp_out.target)
                                if ep_sources == epp_sources and ep_targets == epp_targets:
                                    is_parallel = True
                            if is_parallel and m[event_place] == m[event_place_prime]:
                                parallel_places.add(event_place_prime)
                                places_to_rename[event_place] = f'{type_prime}_{event_place.name}'
        ps_to_remove = ps_to_remove.union(parallel_places)

        for p in ps_to_remove:
            net = petri_utils.remove_place(net, p)

        for p, name in places_to_rename.items():
            p.name = name
        return net

    def export_debug_net(self, net, m, path, step, pn_export_format):
        """
        Helper function to export a petri net at any intermediary step in the conversion of the DcrGraph
        """
        path_without_extension, extens = os.path.splitext(path)
        debug_save_path = f'{path_without_extension}_{step}{extens}'
        pnml_exporter.apply(net, m, debug_save_path, variant=pn_export_format, parameters={'isTimed': False})

    def apply(self, graph, pn_path=None, **kwargs) -> (InhibitorNet, Marking):
        self.initialize_helper_struct(graph)
        self.mapping_exceptions = exceptional_cases.ExceptionalCases(self.helper_struct)
        self.preoptimizer = preoptimizer.Preoptimizer()
        induction_step = 0
        pn_export_format = pnml_exporter.TAPN
        if pn_path and pn_path.endswith("pnml"):
            pn_export_format = pnml_exporter.PNML

        tapn = InhibitorNet("Dcr2Pn")
        m = Marking()
        # pre-optimize mapping based on DCR graph behaviour
        if self.preoptimize:
            if self.print_steps:
                print('[i] preoptimizing')
            self.preoptimizer.pre_optimize_based_on_dcr_behaviour(graph)
            if not self.map_unexecutable_events:
                graph = self.preoptimizer.remove_un_executable_events_from_dcr(graph)

        # including the handling of exception cases from the induction step
        graph = self.mapping_exceptions.filter_exceptional_cases(graph)
        if self.preoptimize:
            if self.print_steps:
                print('[i] finding exceptional behaviour')
            self.preoptimizer.preoptimize_based_on_exceptional_cases(graph, self.mapping_exceptions)

        # map events
        if self.print_steps:
            print('[i] mapping events')
        for event in graph['events']:
            tapn, m = self.create_event_pattern(event, graph, tapn, m)

        if self.debug and pn_path:
            self.export_debug_net(tapn, m, pn_path, f'{induction_step}event', pn_export_format)
            induction_step += 1

        sr = single_relations.SingleRelations(self.helper_struct, self.mapping_exceptions)
        # map constraining relations
        if self.print_steps:
            print('[i] map constraining relations')
        for event in graph['conditionsFor']:
            for event_prime in graph['conditionsFor'][event]:
                tapn = sr.create_condition_pattern(event, event_prime, tapn)
                if self.debug and pn_path:
                    self.export_debug_net(tapn, m, pn_path, f'{induction_step}conditionsFor', pn_export_format)
                    induction_step += 1
        for event in graph['milestonesFor']:
            for event_prime in graph['milestonesFor'][event]:
                tapn = sr.create_milestone_pattern(event, event_prime, tapn)
                if self.debug and pn_path:
                    self.export_debug_net(tapn, m, pn_path, f'{induction_step}milestonesFor', pn_export_format)
                    induction_step += 1

        # map effect relations
        if self.print_steps:
            print('[i] map effect relations')
        for event in graph['includesTo']:
            for event_prime in graph['includesTo'][event]:
                tapn = sr.create_include_pattern(event, event_prime, tapn)
                if self.debug and pn_path:
                    self.export_debug_net(tapn, m, pn_path, f'{induction_step}includesTo', pn_export_format)
                    induction_step += 1
        for event in graph['excludesTo']:
            for event_prime in graph['excludesTo'][event]:
                tapn = sr.create_exclude_pattern(event, event_prime, tapn)
                if self.debug and pn_path:
                    self.export_debug_net(tapn, m, pn_path, f'{induction_step}{event}excludesTo{event_prime}', pn_export_format)
                    induction_step += 1
        for event in graph['responseTo']:
            for event_prime in graph['responseTo'][event]:
                tapn = sr.create_response_pattern(event, event_prime, tapn)
                if self.debug and pn_path:
                    self.export_debug_net(tapn, m, pn_path, f'{induction_step}responseTo', pn_export_format)
                    induction_step += 1
        for event in graph['noResponseTo']:
            for event_prime in graph['noResponseTo'][event]:
                tapn = sr.create_no_response_pattern(event, event_prime, tapn)
                if self.debug and pn_path:
                    self.export_debug_net(tapn, m, pn_path, f'{induction_step}noResponseTo', pn_export_format)
                    induction_step += 1

        # handle all relation exceptions
        if self.print_steps:
            print('[i] handle all relation exceptions')
        tapn = self.mapping_exceptions.map_exceptional_cases_between_events(tapn, m)

        if self.debug and pn_path:
            self.export_debug_net(tapn, m, pn_path, f'{induction_step}exceptions', pn_export_format)
            induction_step += 1

        # post-optimize based on the petri net reachability graph
        if self.postoptimize:
            if self.print_steps:
                print('[i] post optimizing')
            tapn = self.post_optimize_petri_net_reachability_graph(tapn, m, graph)

        if pn_path:
            if self.print_steps:
                print(f'[i] export to {pn_path}')

            pnml_exporter.apply(tapn, m, pn_path, variant=pn_export_format, parameters={'isTimed': False})

        return tapn, m


def apply(dcr, parameters):
    d2p = Dcr2PetriNet(**parameters)
    tapn, m = d2p.apply(dcr, **parameters)
    return tapn, m
