import os
print(os.getcwd())
os.chdir('/home/vco/Projects/pm4py-dcr2tapn/')
print(os.getcwd())

import numpy as np
import pandas as pd
from copy import deepcopy

from pm4py.objects.dcr.importer import importer as dcr_importer
from pm4py.objects.dcr.obj import TemplateRelations as Relations

from pm4py.objects.conversion.dcr_apt.variants.to_timed_arc_petri_net_submodules import (timed_exceptional_cases,
                                                                                         timed_single_relations,
                                                                                         timed_preoptimizer,
                                                                                         timed_utils)


class Dcr2TimedArcPetri(object):

    def __init__(self, preoptimize=False, postoptimize=False, map_unexecutable_events=False, debug=False, **kwargs) -> None:
        # self.in_t_types = ['event', 'init', 'initpend', 'pend']
        # self.helper_struct = {}
        self.preoptimize = preoptimize
        self.postoptimize = postoptimize
        self.map_unexecutable_events = map_unexecutable_events
        self.preoptimizer = timed_preoptimizer.TimedPreoptimizer()
        self.transitions = {}
        # self.helper_struct['pend_matrix'] = {}
        # self.helper_struct['pend_exc_matrix'] = {}
        self.mapping_exceptions = None
        self.reachability_timeout = None
        self.print_steps = debug
        # self.debug = debug
        self.base_case = pd.DataFrame([[3, 3, 4, 0],
                                       [3, 5, 4, 0],
                                       [3, 5, 2, 0],
                                       [3, 3, 2, 0]], columns=['In', 'Ex', 'Re', 'Rex'])
        self.unique_deadline = {}
        self.event_to_deadline_map = {}

    def initialize_helper_struct(self, G) -> None:
        def do_work(v, event, all_unique_deadlines):
            if v > 0:
                if v not in all_unique_deadlines:
                    all_unique_deadlines[v] = set()
                all_unique_deadlines[v].add(event)
            elif v == 0:
                if np.inf not in all_unique_deadlines:
                    all_unique_deadlines[np.inf] = set()
                all_unique_deadlines[np.inf].add(event)

        for event in G['events']:
            self.unique_deadline[event] = {}
        for event in G['events']:
            if event in G['marking']['pendingDeadline']:
                v = G['marking']['pendingDeadline'][event]
                do_work(v, 'init', self.unique_deadline[event])
            if event in G['responseToDeadlines']:
                for event_prime, v in G['responseToDeadlines'][event].items():
                    do_work(v, event, self.unique_deadline[event_prime])
            elif event in G['responseTo']:
                for event_prime in G['responseTo'][event].items():
                    do_work(0, event, self.unique_deadline[event_prime])

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
                base_case_rows.add([i for i in range(2, n, 2)])
            if default_make_pend:
                base_case_rows.add([i for i in range(3, n, 2)])

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
        if event in G['marking']['pending'] and event in G['marking']['included']:
            m['Re'] = 1
            if event in G['marking']['pendingDeadline']:
                m['Deadline_Re'] = G['marking']['pendingDeadline'][event]
        if event in G['marking']['pending'] and not event in G['marking']['included']:
            m['Rex'] = 1
        if event in G['marking']['executed']:
            m['Ex'] = 1

        return res_base_case, m

    def apply(self, G, tapn_path=None, **kwargs):
        self.initialize_helper_struct(G)
        self.mapping_exceptions = timed_exceptional_cases.TimedExceptionalCases()
        self.preoptimizer = timed_preoptimizer.TimedPreoptimizer()

        events = G['events']
        base_case_dict = {}
        marking = {}
        if self.print_steps:
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
        return master_df


example = 'models/debug.xml'
dcr_dict = dcr_importer.apply(example, parameters={'as_dcr_object': True, 'labels_as_ids': True})
dcr_dict = dcr_dict.obj_to_template()
dcr2tapn = Dcr2TimedArcPetri(debug=False, preoptimize=False, postoptimize=False)
master_df = dcr2tapn.apply(dcr_dict)
master_df