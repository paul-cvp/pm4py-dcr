from datetime import timedelta

import numpy as np
import pandas as pd
from copy import deepcopy

from pm4py.objects.dcr.obj import TemplateRelations as Relations

from pm4py.objects.petri_net.timed_arc_net.obj import *
from pm4py.objects.petri_net.utils import petri_utils as pn_utils
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
from pm4py.objects.petri_net import properties as pn_props

from pm4py.objects.conversion.dcr_apt.variants.to_timed_arc_petri_net_submodules import timed_exceptional_cases, timed_preoptimizer


class Dcr2TimedArcPetri(object):

    def __init__(self, preoptimize=False, postoptimize=False, map_unexecutable_events=False, debug=False, **kwargs) -> None:
        self.preoptimize = preoptimize
        self.postoptimize = postoptimize
        self.map_unexecutable_events = map_unexecutable_events
        self.preoptimizer = timed_preoptimizer.TimedPreoptimizer()
        self.transitions = {}
        self.mapping_exceptions = None
        self.reachability_timeout = None
        self.debug = debug
        if debug:
            self.aprs = {}
        self.base_case = pd.DataFrame([[3, 3, 4, 0],
                                       [3, 5, 4, 0],
                                       [3, 5, 2, 0],
                                       [3, 3, 2, 0]], columns=['In', 'Ex', 'Re', 'Rex'])
        self.unique_deadline = {}
        self.event_to_deadline_map = {}
        self.p_dict = {}
        self.delay_dict = {}


    def initialize_helper_struct(self, G) -> None:
        # determine all deadlines
        def do_work(v, event, all_unique_deadlines):
            if isinstance(v,int):
                if v > 0:
                    if v not in all_unique_deadlines:
                        all_unique_deadlines[v] = set()
                    all_unique_deadlines[v].add(event)
                elif v == 0:
                    if np.inf not in all_unique_deadlines:
                        all_unique_deadlines[np.inf] = set()
                    all_unique_deadlines[np.inf].add(event)
            else:
                if v > timedelta(0):
                    if v not in all_unique_deadlines:
                        all_unique_deadlines[v] = set()
                    all_unique_deadlines[v].add(event)
                elif v == timedelta(0):
                    if np.inf not in all_unique_deadlines:
                        all_unique_deadlines[np.inf] = set()
                    all_unique_deadlines[np.inf].add(event)

        # for each event we have a list of all unique deadlines (can be infinity)
        # + all events that determine each unique deadline
        # can be initially pending then we use init
        # or self response then we have [event][unique deadline][event]
        for event in G['events']:
            self.unique_deadline[event] = {}
        for event, v in G['marking']['pendingDeadline'].items():
            do_work(v, 'init', self.unique_deadline[event])
        for event in set(G['marking']['pending']).difference(set(G['marking']['pendingDeadline'].keys())):
            do_work(0, 'init', self.unique_deadline[event])
        resp_with_deadlines = set()
        for event in G['responseToDeadlines']:
            for event_prime, v in G['responseToDeadlines'][event].items():
                do_work(v, event, self.unique_deadline[event_prime])
                resp_with_deadlines.add(frozenset([event,event_prime]))
        for event in G['responseTo']:
            for event_prime in G['responseTo'][event]:
                if frozenset([event,event_prime]) not in resp_with_deadlines:
                    do_work(0, event, self.unique_deadline[event_prime])

        # for event in G['events']:
        #     if event in G['marking']['pendingDeadline']:
        #         v = G['marking']['pendingDeadline'][event]
        #         do_work(v, 'init', self.unique_deadline[event])
        #     if event in G['marking']['pending']:
        #         do_work(0, 'init', self.unique_deadline[event])
        #     if event in G['responseToDeadlines']:
        #         for event_prime, v in G['responseToDeadlines'][event].items():
        #             do_work(v, event, self.unique_deadline[event_prime])
        #     elif event in G['responseTo']:
        #         for event_prime in G['responseTo'][event]:
        #             do_work(0, event, self.unique_deadline[event_prime])
        for event in G['conditionsForDelays']:
            for event_prime in G['conditionsForDelays'][event]:
                delay = G['conditionsForDelays'][event][event_prime]
                #TODO: find out if it needs more advanced parsing
                self.delay_dict[frozenset([event, event_prime])] = int(delay)

    def create_event_pattern(self, event, G):
        event_base_case = deepcopy(self.base_case)

        # this if statement handles self response exclude
        if event in self.mapping_exceptions.self_exceptions[frozenset([Relations.R.value, Relations.E.value])]:
            # change the base case to the exception case
            event_base_case['In'] = event_base_case['In'] - 1
            event_base_case['Rex'] = event_base_case['Rex'] + 1
        # this if statement handles self exclude
        if event in self.mapping_exceptions.self_exceptions[Relations.E.value]:
            event_base_case['In'] = event_base_case['In'] - 1
        # this if statement handles self response
        if event in self.mapping_exceptions.self_exceptions[Relations.R.value]:
            event_base_case['Re'] = event_base_case['Re'] + 1

        default_make_included = event in self.preoptimizer.need_included_place if self.preoptimize else True
        default_make_pend = event in self.preoptimizer.need_pending_place if self.preoptimize else True
        default_make_pend_ex = event in self.preoptimizer.need_pending_excluded_place if self.preoptimize else True
        default_make_exec = event in self.preoptimizer.need_executed_place if self.preoptimize else True
        # if event == 'gate_down':
        if event == 'MakePayment' or event == 'AddOrder':
            default_make_exec = True
        event_columns = []
        re_columns = {}
        rex_columns = {}
        if default_make_included:
            event_columns.append('In')

        if default_make_exec:
            event_columns.append('Ex')

        if default_make_pend:
            rows = []
            n = len(self.unique_deadline[event])
            col_vals = [[] for i in range(n)]
            for i, (deadline, events) in enumerate(self.unique_deadline[event].items()):
                re_columns[f'Re_{deadline}'] = events
                event_base_case[f'Re_{deadline}'] = event_base_case['Re']
                if event not in self.event_to_deadline_map:
                    self.event_to_deadline_map[event] = {}
                for e in events:
                    self.event_to_deadline_map[event][e] = deadline

                rows.extend([2, 3])
                for k in range(n):
                    if k == i:
                        col_vals[i].extend([2, 2])
                    else:
                        col_vals[i].extend([0, 0])
            rrrr = [0, 1]
            rrrr.extend(rows)
            new_bc = event_base_case.loc[rrrr]
            new_bc = new_bc.reset_index(drop=True)
            new_bc = new_bc.astype(int)
            col_vals_df = pd.DataFrame(col_vals, dtype=int).T
            col_vals_df.columns = re_columns.keys()  # ['Re0', 'Re1', 'Re2']
            col_vals_df.index = col_vals_df.index + 2
            new_bc.loc[2:, re_columns.keys()] = col_vals_df
            event_base_case = new_bc
            event_columns.extend(re_columns.keys())

        if default_make_pend_ex:
            for deadline, events in self.unique_deadline[event].items():
                rex_columns[f'Rex_{deadline}'] = events
                event_base_case[f'Rex_{deadline}'] = event_base_case['Rex']
            event_columns.extend(rex_columns.keys())

        base_case_rows = set(event_base_case.index)
        n = len(base_case_rows)
        if self.preoptimize:
            # this tells which rows to create in the base case: 0 = event, 1 = init, 2 = initpend, 3 = pend
            base_case_rows = {0}
            if default_make_exec and event not in G['marking']['executed'] and event not in self.preoptimizer.no_init_t:
                base_case_rows.add(1)
            if default_make_exec and default_make_pend and event not in self.preoptimizer.no_initpend_t:
                base_case_rows = base_case_rows.union(set([i for i in range(2, n, 2)]))
            if default_make_pend:
                base_case_rows = base_case_rows.union(set([i for i in range(3, n, 2)]))

        # this if statement handles self condition
        if event in self.mapping_exceptions.self_exceptions[Relations.C.value]:
            base_case_rows = base_case_rows.difference({1}.union(set([i for i in range(2, n, 2)])))

        res_base_case = event_base_case[event_columns].loc[list(base_case_rows)]
        if len(event_columns) == 0 and len(base_case_rows) == 1:
            res_base_case = pd.DataFrame(columns=['No'])  # 'In', 'Re', 'Rex', 'Ex'])
            res_base_case.loc[0] = [0]  # , 0, 0, 0]
        res_base_case = res_base_case.astype(int)

        # fill the marking
        m = {}
        if event in G['marking']['included']:
            m['In'] = 1
        if event in G['marking']['pending']:
            if event in G['marking']['included']:
                m['Re'] = 1
            else:
                m['Rex'] = 1
        if event in G['marking']['pendingDeadline']:
            m['Deadline_Re'] = G['marking']['pendingDeadline'][event]
            if event in G['marking']['included']:
                m['Re'] = 1
            else:
                m['Rex'] = 1
        if event in G['marking']['executed']:
            m['Ex'] = 1

        return res_base_case, m

    def post_optimize_petri_net_reachability_graph(self, tapn, m, G=None) -> TimedArcNet:
        # from pm4py.objects.petri_net.utils import petri_utils
        from pm4py.objects.conversion.dcr.variants import reachability_analysis
        # from pm4py.objects.petri_net.timed_arc_net import semantics as tapn_semantics
        from pm4py.objects.petri_net.inhibitor_reset import semantics as inhibitor_semantics

        max_elab_time = 2 * 60 # 2 minutes
        if self.reachability_timeout:
            max_elab_time = self.reachability_timeout
        trans_sys = reachability_analysis.construct_reachability_graph(tapn, m, use_trans_name=True,
                                                                    parameters={
                                                                        'petri_semantics': inhibitor_semantics.InhibitorResetSemantics(),
                                                                        # 'petri_semantics': tapn_semantics.TimedArcSemantics(),
                                                                        'max_elab_time': max_elab_time})
        if self.debug:
            from pm4py.visualization.transition_system import visualizer as ts_visualizer
            gviz = ts_visualizer.apply(trans_sys, parameters={ts_visualizer.Variants.VIEW_BASED.value.Parameters.FORMAT: "png"})
            ts_visualizer.view(gviz)

        fired_transitions = set()

        for transition in trans_sys.transitions:
            fired_transitions.add(transition.name)

        ts_to_remove = set()
        for t in tapn.transitions:
            if t.name not in fired_transitions:
                ts_to_remove.add(t)

        for t in ts_to_remove:
            tapn = pn_utils.remove_transition(tapn, t)

        changed_places = set()
        for state_list in trans_sys.states:
            for state in state_list.name:
                changed_places.add(state)

        parallel_places = set()
        places_to_rename = {}
        ps_to_remove = set(tapn.places).difference(changed_places)
        if G:
            for event in G['events']:
                for (e, type), event_place in self.p_dict.items():
                    for (e_prime, type_prime), event_place_prime in self.p_dict.items():
                        # TODO: if type is (pending or pending_excluded) then event_place is a set
                        # if type_prime is (pending or pending_excluded) then event_place_prime is a set
                        if type in ['pending', 'pending_excluded'] and type_prime in ['pending', 'pending_excluded']:
                            for ep, _ in event_place:
                                for epp, _ in event_place_prime:
                                    self.post_optimize_parallel_places(ep, epp, parallel_places, places_to_rename, type_prime, m)
                        elif type in ['pending', 'pending_excluded']:
                            for ep, _ in event_place:
                                self.post_optimize_parallel_places(ep, event_place_prime, parallel_places, places_to_rename, type_prime, m)
                        elif type_prime in ['pending', 'pending_excluded']:
                            for epp, _ in event_place_prime:
                                self.post_optimize_parallel_places(event_place, epp, parallel_places, places_to_rename, type_prime, m)
                        else:
                            self.post_optimize_parallel_places(event_place, event_place_prime, parallel_places, places_to_rename, type_prime, m)

        ps_to_remove = ps_to_remove.union(parallel_places)
        for p in ps_to_remove:
            tapn = pn_utils.remove_place(tapn, p)

        for p, name in places_to_rename.items():
            p.name = name

        return tapn

    @staticmethod
    def post_optimize_parallel_places(event_place, event_place_prime, parallel_places, places_to_rename, type_prime, m):
        if event_place and event_place_prime and event_place.name != event_place_prime.name and event_place not in parallel_places:
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
                by_who = ''
                if pn_props.AGE_INVARIANT not in event_place.properties and pn_props.AGE_INVARIANT in event_place_prime.properties:
                    event_place.properties[pn_props.AGE_INVARIANT] = event_place_prime.properties[pn_props.AGE_INVARIANT]
                    by_who = f"_by_{str.split(event_place_prime.name,'_')[-1]}"
                places_to_rename[event_place] = f'{type_prime}_{event_place.name}{by_who}'

    def map_events(self, G):
        events = G['events']
        base_case_dict = {}
        marking = {}
        if self.debug:
            print('[i] mapping events')
        for event in events:
            event_base_case, m = self.create_event_pattern(event, G)
            base_case_dict[event] = event_base_case
            marking[event] = m

        row_tuples = []
        # Step 3: Create a multilevel column index for each dataframe
        for event in base_case_dict:
            base_case_dict[event] = base_case_dict[event].reset_index(drop=True)
            row_tuples.extend([(event, idx) for idx in range(base_case_dict[event].shape[0])])
            base_case_dict[event].columns = pd.MultiIndex.from_product([[event], base_case_dict[event].columns])

        master_df = pd.concat(base_case_dict, ignore_index=True)
        master_df = master_df.fillna(0)
        master_df = master_df.astype(int)
        multi_index = pd.MultiIndex.from_tuples(row_tuples, names=["Event", "Index"])
        master_df.index = multi_index
        return master_df, marking

    def apply(self, G, tapn_path=None, **kwargs):
        # self.basic = False  # True (basic) = inc,ex,resp,cond | False = basic + no-resp,mil
        self.timed = True  # False = untimed | True = timed cond (delay) and resp (deadline)
        # self.transport_idx = 0
        self.initialize_helper_struct(G)
        self.mapping_exceptions = timed_exceptional_cases.TimedExceptionalCases(self.event_to_deadline_map, self.debug)
        self.preoptimizer = timed_preoptimizer.TimedPreoptimizer()

        # pre-optimize mapping based on DCR graph behaviour
        if self.preoptimize:
            if self.debug:
                print('[i] preoptimizing')
            self.preoptimizer.pre_optimize_based_on_dcr_behaviour(G)
            if not self.map_unexecutable_events:
                G = self.preoptimizer.remove_un_executable_events_from_dcr(G)

        # including the handling of exception cases from the induction step
        G, transition_types = self.mapping_exceptions.filter_exceptional_cases(G)
        if self.preoptimize:
            if self.debug:
                print('[i] finding exceptional behaviour')
            self.preoptimizer.preoptimize_based_on_exceptional_cases(G, self.mapping_exceptions)

        # map events
        master_df, marking = self.map_events(G)
        if self.debug:
            self.aprs['events'] = deepcopy(master_df)

        if self.debug:
            print('[i] handle all relations')
        master_df = self.mapping_exceptions.map_exceptional_cases_between_events(master_df)
        if self.debug:
            self.aprs = {**self.aprs, **self.mapping_exceptions.aprs}

        # Part 2
        pn_export_format = pnml_exporter.TAPN
        if tapn_path and tapn_path.endswith("pnml"):
            pn_export_format = pnml_exporter.PNML

        master_df = master_df.drop('No', axis=1, level=1, errors='ignore') #19.09.2024 new entry
        tapn, m = self.arc_pattern_table_to_petri(master_df, marking)
        # post-optimize based on the petri net reachability graph
        if self.postoptimize:
            if self.debug:
                print('[i] post optimizing')
            # for k in tapn.places:
            #     m.timed_dict[k] = 0
            tapn = self.post_optimize_petri_net_reachability_graph(tapn, m, G)

        if tapn_path:
            if self.debug:
                print(f'[i] export to {tapn_path}')

            pnml_exporter.apply(tapn, m, tapn_path, variant=pn_export_format, parameters={'isTimed': self.timed})

        return tapn, m, master_df

    def arc_pattern_table_to_petri(self, master_df, marking):
        res_pn = TimedArcNet("TapnfromDcr")
        res_m = TimedMarking()

        p_dict = {}
        for event, place_type in master_df.columns:
            if event not in p_dict:
                p_dict[event] = set()
            p_dict[event].add(place_type)
        for event, place_types in p_dict.items():
            init_pending_inf = True
            if 'Re_inf' in place_types and 'Deadline_Re' in marking[event]:
                if int(marking[event]['Deadline_Re'])>0:
                    init_pending_inf = False

            for place_type in place_types:
                if place_type != 'No':
                    p = PetriNet.Place(name=f'{event}_{place_type}')
                    self.p_dict[(event, place_type)] = p
                    res_pn.places.add(p)
                    pt = place_type
                    if place_type.startswith('Re_'):
                        pt, deadline = place_type.split('_')
                        if deadline.isdigit() and int(deadline) > 0:
                            p.properties['ageinvariant'] = int(deadline)
                            if 'Deadline_Re' in marking[event] and marking[event]['Deadline_Re']==int(deadline):
                                res_m.timed_dict[p] = marking[event]['Deadline_Re']
                                res_m[p] = marking[event][pt]
                        elif deadline == 'inf' and pt in marking[event] and init_pending_inf:
                            res_m[p] = marking[event][pt]

                    elif pt in marking[event]:
                        res_m[p] = marking[event][pt]
        transport_idx = 0
        increase = False
        for event, idx in master_df.index:
            t = PetriNet.Transition(name=f'{event}_{idx}', label=f'{event}_{idx}_label')
            res_pn.transitions.add(t)
            for (event_prime, place_type), arc_type in dict(master_df.loc[(event, idx)]).items():
                if arc_type > 0:
                    match arc_type:
                        case 1:  # TtoP -->
                            pn_utils.add_arc_from_to_apt(t, self.p_dict[(event_prime, place_type)], res_pn)
                        case 2:  # PtoT <--
                            pn_utils.add_arc_from_to_apt(self.p_dict[(event_prime, place_type)], t, res_pn)
                        case 3:  # Read Both <-->
                            pn_utils.add_arc_from_to_apt(self.p_dict[(event_prime, place_type)], t, res_pn)
                            pn_utils.add_arc_from_to_apt(t, self.p_dict[(event_prime, place_type)], res_pn)
                        case 4:  # Inhib o--
                            pn_utils.add_arc_from_to_apt(self.p_dict[(event_prime, place_type)], t, res_pn, type='inhibitor')
                        case 5:  # TtoPandInhib o-->
                            pn_utils.add_arc_from_to_apt(t, self.p_dict[(event_prime, place_type)], res_pn)
                            pn_utils.add_arc_from_to_apt(self.p_dict[(event_prime, place_type)], t, res_pn, type='inhibitor')
                        case 6: # TtP 6 # --<>
                            ttp = pn_utils.add_arc_from_to_apt(t, self.p_dict[(event_prime, place_type)], res_pn, type='transport')
                            ttp.properties['transportindex'] = transport_idx
                            if increase:
                                transport_idx += 1
                                increase = False
                            else:
                                increase = True
                        case 7: # PtT 7 # <>--
                            ptt = pn_utils.add_arc_from_to_apt(self.p_dict[(event_prime, place_type)], t, res_pn, type='transport')
                            ptt.properties['transportindex'] = transport_idx
                            if increase:
                                transport_idx += 1
                                increase = False
                            else:
                                increase = True
                        case 8: # TRead TBoth 8 # <>-<>
                            if increase == True:
                                print('[X] increase is true this should not happen!')
                            ttp = pn_utils.add_arc_from_to_apt(t, self.p_dict[(event_prime, place_type)], res_pn, type='transport')
                            ttp.properties['transportindex'] = transport_idx
                            ptt = pn_utils.add_arc_from_to_apt(self.p_dict[(event_prime, place_type)], t, res_pn, type='transport')
                            ptt.properties['transportindex'] = transport_idx
                            # this should work because only conditions have this type of arc
                            delay = self.delay_dict[frozenset([event, event_prime])] if frozenset([event, event_prime]) in self.delay_dict else None
                            if delay and delay > 0:
                                ptt.properties['agemin'] = delay
                            transport_idx += 1
                            increase = False

        return res_pn, res_m

if __name__ == "__main__":
    import os
    print(os.getcwd())
    os.chdir('/home/vco/Projects/pm4py-dcr2tapn/')
    print(os.getcwd())
    from pm4py.objects.dcr.importer import importer as dcr_importer
    example = 'models/dcr-original.xml'
    dcr_dict = dcr_importer.apply(example, parameters={'as_dcr_object': True, 'labels_as_ids': True})
    dcr_dict = dcr_dict.obj_to_template()
    dcr2tapn = Dcr2TimedArcPetri(debug=False, preoptimize=True, postoptimize=True)
    tapn, m, master_df = dcr2tapn.apply(dcr_dict, tapn_path='models/original.tapn')
