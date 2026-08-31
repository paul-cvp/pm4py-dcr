import os
from copy import deepcopy

import pandas as pd

from pm4py.objects.dcr.obj import TemplateRelations as Relations
from pm4py.objects.petri_net.utils import petri_utils as pn_utils
# from pm4py.objects.petri_net.utils import reduction
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter

from pm4py.objects.conversion.dcr_apt.variants.to_petri_net_submodules import exceptional_cases, preoptimizer


class Dcr2PetriNet(object):

    def __init__(self, preoptimize=True, postoptimize=True, map_unexecutable_events=False, debug=False, **kwargs) -> None:
        self.preoptimize = preoptimize
        self.postoptimize = postoptimize
        self.map_unexecutable_events = map_unexecutable_events
        self.preoptimizer = preoptimizer.Preoptimizer()
        self.transitions = {}
        self.mapping_exceptions = None
        self.reachability_timeout = None
        self.print_steps = debug
        self.p_dict = {}
        # self.debug = debug
        self.base_case = pd.DataFrame([[3, 3, 4, 0],
                                       [3, 5, 4, 0],
                                       [3, 5, 2, 0],
                                       [3, 3, 2, 0]], columns=['In', 'Ex', 'Re', 'Rex'])

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

        event_columns = []
        if default_make_included:
            event_columns.append('In')

        if default_make_pend:
            event_columns.append('Re')

        if default_make_pend_ex:
            event_columns.append('Rex')

        if default_make_exec:
            event_columns.append('Ex')
        base_case_rows = {0, 1, 2, 3}
        if self.preoptimize:
            # this tells which rows to create in the base case: 0 = event, 1 = init, 2 = initpend, 3 = pend
            base_case_rows = {0}
            if default_make_exec and event not in G['marking']['executed'] and event not in self.preoptimizer.no_init_t:
                base_case_rows.add(1)
            if default_make_exec and default_make_pend and event not in self.preoptimizer.no_initpend_t:
                base_case_rows.add(2)
            if default_make_pend:
                base_case_rows.add(3)

        # this if statement handles self condition
        if event in self.mapping_exceptions.self_exceptions[Relations.C.value]:
            base_case_rows = base_case_rows.difference({1, 2})
        res_base_case = event_base_case[event_columns].loc[list(base_case_rows)]
        if len(event_columns) == 0 and len(base_case_rows) == 1:
            res_base_case = pd.DataFrame(columns=['No'])#'In', 'Re', 'Rex', 'Ex'])
            res_base_case.loc[0] = [0]#, 0, 0, 0]
        res_base_case = res_base_case.astype(int)

        # fill the marking
        m = {}
        if event in G['marking']['included']:
            m['In'] = 1
        if event in G['marking']['pending'] and event in G['marking']['included']:
            m['Re'] = 1
        if event in G['marking']['pending'] and not event in G['marking']['included']:
            m['Rex'] = 1
        if event in G['marking']['executed']:
            m['Ex'] = 1

        return res_base_case, m

    # def create_event_pattern(self, event, G):
    #     event_base_case, m = self.create_event_base_case(event, G)
    #     # if event_base_case.shape[1] == 0 then it is a single transition without any places
    #     # TODO: double check that whenever event_base_case.shape[1] == 0 that event_base_case.shape[0] == 1
    #     return event_base_case, m

    def post_optimize_petri_net_reachability_graph(self, tapn, m, merge_parallel_places=True):
        from pm4py.objects.petri_net.utils import reachability_graph
        from pm4py.objects.petri_net.inhibitor_reset import semantics as inhibitor_semantics
        max_elab_time = 2 * 60 * 60  # 2 hours
        if self.reachability_timeout:
            max_elab_time = self.reachability_timeout
        trans_sys = reachability_graph.construct_reachability_graph(tapn, m, use_trans_name=True,
                                                                    parameters={
                                                                        'petri_semantics': inhibitor_semantics.InhibitorResetSemantics(),
                                                                        'max_elab_time': max_elab_time
                                                                    })
        # if self.debug:
        #     from pm4py.visualization.transition_system import visualizer as ts_visualizer
        #     gviz = ts_visualizer.apply(trans_sys, parameters={ts_visualizer.Variants.VIEW_BASED.value.Parameters.FORMAT: "png"})
        #     ts_visualizer.view(gviz)
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

        ps_to_remove = set(tapn.places).difference(changed_places)

        parallel_places = set()
        places_to_rename = {}
        if merge_parallel_places:
            for (e, type), event_place in self.p_dict.items():
                for (e_prime, type_prime), event_place_prime in self.p_dict.items():
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
        for p, name in places_to_rename.items():
            p.name = name

        for p in ps_to_remove:
            tapn = pn_utils.remove_place(tapn, p)

        return tapn

    def apply(self, G, tapn_path=None, **kwargs):
        # self.basic = False  # True (basic) = inc,ex,resp,cond | False = basic + no-resp,mil
        self.timed = False  # False = untimed | True = timed cond (delay) and resp (deadline)
        self.mapping_exceptions = exceptional_cases.ExceptionalCases()
        self.preoptimizer = preoptimizer.Preoptimizer()

        # pre-optimize mapping based on DCR graph behaviour
        if self.preoptimize:
            if self.print_steps:
                print('[i] preoptimizing')
            self.preoptimizer.pre_optimize_based_on_dcr_behaviour(G)
            if not self.map_unexecutable_events:
                G = self.preoptimizer.remove_un_executable_events_from_dcr(G)

        # including the handling of exception cases from the induction step
        # G_old = deepcopy(G)
        G, transition_types = self.mapping_exceptions.filter_exceptional_cases(G)
        events = G['events']
        if self.preoptimize:
            if self.print_steps:
                print('[i] finding exceptional behaviour')
            self.preoptimizer.preoptimize_based_on_exceptional_cases(G, self.mapping_exceptions)

        # map events
        base_case_dict = {}
        marking = {}
        if self.print_steps:
            print('[i] mapping events')
        for event in events:
            event_base_case, m = self.create_event_pattern(event, G)
            base_case_dict[event] = event_base_case
            marking[event] = m
            # if self.print_steps:
            #     print(f'{event} ---------------------------')
            #     print(event_base_case)

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

        # handle all relations
        if self.print_steps:
            print('[i] handle all relations')
        master_df = self.mapping_exceptions.map_exceptional_cases_between_events(master_df)
        # return master_df, marking

        # Part 2 make the net based on the petri net matrix representation
        tapn, m = self.arc_pattern_table_to_petri(master_df, marking)
        pn_export_format = pnml_exporter.TAPN
        if tapn_path and tapn_path.endswith("pnml"):
            pn_export_format = pnml_exporter.PNML
        # post-optimize based on the petri net reachability graph
        if self.postoptimize:
            if self.print_steps:
                print('[i] post optimizing')
            tapn = self.post_optimize_petri_net_reachability_graph(tapn, m, G)
            # tapn, m = reduction.apply_bounded_net_inhibitor_removal_rule(tapn, m)
            # tapn, m = reduction.apply_reset_inhibitor_net_reduction(tapn, m)

        if tapn_path:
            if self.print_steps:
                print(f'[i] export to {tapn_path}')

            pnml_exporter.apply(tapn, m, tapn_path, variant=pn_export_format, parameters={'isTimed': self.timed})

        return tapn, m, master_df


    def arc_pattern_table_to_petri(self, master_df, marking):
        res_pn = PetriNet(name='PetriNetfromDcr')
        res_m = Marking()
        for event, place_type in master_df.columns:
            if place_type != 'No':
                p = PetriNet.Place(name=f'{event}_{place_type}')
                self.p_dict[(event, place_type)] = p
                res_pn.places.add(p)
                if place_type in marking[event]:
                    res_m[p] = marking[event][place_type]
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
        return res_pn, res_m


def apply(dcr, parameters):
    d2p = Dcr2PetriNet(**parameters)
    G = deepcopy(dcr)
    tapn, m = d2p.apply(G, **parameters)
    return tapn, m

# def run_specific_dcr():
#     '''
#     here you can write your own graph and run it
#     '''
#     dcr = {
#         'events': {'Triage', 'RelA', 'Reg', 'RelB','CRP'},
#         'conditionsFor': {'RelA': {'Triage','Reg','RelB'}, 'RelB': {'CRP'}},
#         'milestonesFor': {},
#         'responseTo': {},
#         'noResponseTo': {},
#         'includesTo': {},
#         'excludesTo': {'Reg': {'Reg'},'RelB': {'RelB'}, 'RelA': {'RelA', 'RelB', 'Triage'}},
#         'marking': {'executed': set(),
#                     'included': {'Triage', 'RelA', 'Reg', 'RelB','CRP'},
#                     'pending': set()
#                     }
#     }
#
#     d2p = Dcr2PetriNet(preoptimize=True, postoptimize=True, map_unexecutable_events=False)
#     print('[i] dcr')
#     tapn, m = d2p.dcr2tapn(dcr, tapn_path="/home/vco/Projects/pm4py-dcr/models/one_petri_test.tapn")
#
# def clean_input(dcr, white_space_replacement=None):
#     if white_space_replacement is None:
#         white_space_replacement = ''
#     # remove all space characters and put conditions and milestones in the correct order (according to the actual arrows)
#     for k, v in deepcopy(dcr).items():
#         if k in ['includesTo', 'excludesTo', 'conditionsFor', 'responseTo', 'milestonesFor', 'noResponseTo']:
#             v_new = {}
#             for k2, v2 in v.items():
#                 v_new[k2.strip().replace(' ', white_space_replacement)] = set([v3.strip().replace(' ', white_space_replacement) for v3 in v2])
#             dcr[k] = v_new
#         elif k in ['conditionsForDelays', 'responseToDeadlines']:
#             v_new = {}
#             for k2, v2 in v.items():
#                 v_new[k2.strip().replace(' ', white_space_replacement)] = set([(v3.strip().replace(' ', white_space_replacement),d) for (v3,d) in v2])
#             dcr[k] = v_new
#         elif k == 'marking':
#             for k2 in ['executed', 'included', 'pending']:
#                 new_v = set([v2.strip().replace(' ', white_space_replacement) for v2 in dcr[k][k2]])
#                 dcr[k][k2] = new_v
#         elif k in ['subprocesses', 'nestings', 'labelMapping', 'roleAssignments', 'readRoleAssignments']:
#             v_new = {}
#             for k2, v2 in v.items():
#                 v_new[k2.strip().replace(' ', white_space_replacement)] = set([v3.strip().replace(' ', white_space_replacement) for v3 in v2])
#             dcr[k] = v_new
#         else:
#             new_v = set([v2.strip().replace(' ', white_space_replacement) for v2 in dcr[k]])
#             dcr[k] = new_v
#     return dcr
#
#
# if __name__ == "__main__":
#     # run_specific_dcr()
#     import pm4py
#     from pm4py.algo.discovery.dcr_discover import algorithm as dcr_discover
#     from pm4py.objects.dcr.exporter import exporter as dcr_exporter
#
#     # dcr = {
#     #     'events': {'A', 'B', 'C'},
#     #     'conditionsFor': {'B': {'A'}},
#     #     'milestonesFor': {},
#     #     'responseTo': {},
#     #     'noResponseTo': {},
#     #     'includesTo': {},
#     #     'excludesTo': {'B': {'A', 'B', 'C'}, 'A': {'A', 'B', 'C'}, 'C': {'A','B','C'}},
#     #     'conditionsForDelays': {},
#     #     'responseToDeadlines': {},
#     #     'marking': {'executed': {},
#     #                 'included': {'A', 'B', 'C'},
#     #                 'pending': {},
#     #                 'pendingDeadline': {}
#     #                 }
#     # }
#
#     sepsis_log = pm4py.read_xes('/home/vco/Datasets/Sepsis Cases - Event Log.xes', return_legacy_log_object=True)
#     dcr_sepsis, _ = dcr_discover.apply(sepsis_log)
#     dcr_sepsis = clean_input(dcr_sepsis, '')
#     path = '/home/vco/Projects/pm4py-dcr/models/'
#     dcr_exporter.apply(dcr_sepsis, path+'sepsis.xml')
#     d2p = Dcr2PetriNet(preoptimize=True, postoptimize=True, map_unexecutable_events=False, debug=False)
#     file_name = 'sepsis.tapn'
#     d2p.print_steps = True
#     tapn = d2p.dcr2tapn(dcr_sepsis, path+file_name)
#     # file_name = 'me.tapn'
#     # tapn = d2p.dcr2tapn(dcr, path+file_name)
