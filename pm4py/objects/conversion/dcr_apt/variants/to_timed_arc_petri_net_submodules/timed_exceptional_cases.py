from copy import deepcopy
from collections import Counter
import pandas as pd
import numpy as np

from pm4py.objects.conversion.dcr_apt.variants.to_timed_arc_petri_net_submodules.timed_utils import copy_event_rows, prepare_timed_case
from pm4py.objects.dcr.obj import TemplateRelations as Relations
from itertools import combinations

I = Relations.I.value
E = Relations.E.value
R = Relations.R.value
N = Relations.N.value
C = Relations.C.value
M = Relations.M.value


class TimedExceptionalCases(object):

    def __init__(self, event_to_deadline_map, debug) -> None:
        self.event_to_deadline_map = event_to_deadline_map
        self.effect_relations = [I, E, R, N]
        self.constrain_relations = [C, M]
        self.debug = debug
        if debug:
            self.aprs = {}
        self.all_relations = self.effect_relations + self.constrain_relations

        self.self_exceptions = {}
        for r in self.all_relations:
            self.self_exceptions[r] = set()
        self.self_exceptions[frozenset([E, R])] = set()
        self.self_exceptions[frozenset([C, M])] = set()
        self.exceptions = {}
        self.apply_exceptions = {}
        for i in range(6, 0, -1):
            for comb in combinations(self.all_relations, i):
                self.exceptions[frozenset(comb)] = set()
                apply_comb = set(comb)
                if I in apply_comb and E in apply_comb:
                    apply_comb.remove(E)
                if R in apply_comb and N in apply_comb:
                    apply_comb.remove(N)
                self.apply_exceptions[frozenset(apply_comb)] = None

        # 2 constrain + 4 effect relations (permutations 1 - 1 [because {CMIERN}=={CMIR}]) = 0
        # 2 constrain + 3 effect relations (permutations 4 - 4 [all reduce to 2 constrain 2 effects]) = 0
        # 2 constrain + 2 effect relations (permutations 6 - 2 [{CMIE}=={CMI} and {CMRN}=={CMR}]) = 4
        self.apply_exceptions[
            frozenset([C, M, E, R])] = self.create_exception_condition_milestone_exclude_response_pattern
        self.apply_exceptions[
            frozenset([C, M, E, N])] = self.create_exception_condition_milestone_exclude_no_response_pattern
        self.apply_exceptions[
            frozenset([C, M, I, R])] = self.create_exception_condition_milestone_include_response_pattern
        self.apply_exceptions[
            frozenset([C, M, I, N])] = self.create_exception_condition_milestone_include_no_response_pattern
        # 1 constrain + 4 effect relations (permutations 2 - 2 [all reduce to 1 constrain 2 effects]) = 0
        # 1 constrain + 3 effect relations (permutations 8 - 8 [all reduce to 1 constrain 2 effects]) = 0
        # 0 constrain + 4 effect relations (1-1 [because {I,E,R,N}=={I,R}]) = 0
        # 2 constrain + 1 effect (4)
        self.apply_exceptions[frozenset([C, M, R])] = self.create_exception_condition_milestone_response_pattern
        self.apply_exceptions[frozenset([C, M, N])] = self.create_exception_condition_milestone_no_response_pattern
        self.apply_exceptions[frozenset([C, M, I])] = self.create_exception_condition_milestone_include_pattern
        self.apply_exceptions[frozenset([C, M, E])] = self.create_exception_condition_milestone_exclude_pattern
        # 1 constrain + 2 effect relations (12 - 4 [{C,R,N},{C,I,E},{M,R,N},{M,I,E}]) = 8
        self.apply_exceptions[frozenset([M, N, I])] = self.create_exception_milestone_no_response_include_pattern
        self.apply_exceptions[frozenset([M, N, E])] = self.create_exception_milestone_no_response_exclude_pattern
        self.apply_exceptions[frozenset([M, R, I])] = self.create_exception_milestone_response_include_pattern
        self.apply_exceptions[frozenset([M, R, E])] = self.create_exception_milestone_response_exclude_pattern
        self.apply_exceptions[frozenset([C, N, I])] = self.create_exception_condition_no_response_include_pattern
        self.apply_exceptions[frozenset([C, N, E])] = self.create_exception_condition_no_response_exclude_pattern
        self.apply_exceptions[frozenset([C, R, I])] = self.create_exception_condition_response_include_pattern
        self.apply_exceptions[frozenset([C, R, E])] = self.create_exception_condition_response_exclude_pattern
        # 0 constrain + 3 effect relations (4 - 4 [all reduce to 2 effects]) = 0
        # 1 constrain + 1 effect relation (8) = 8
        self.apply_exceptions[frozenset([I, C])] = self.create_exception_condition_include_pattern
        self.apply_exceptions[frozenset([E, C])] = self.create_exception_condition_exclude_pattern
        self.apply_exceptions[frozenset([R, C])] = self.create_exception_condition_response_pattern
        self.apply_exceptions[frozenset([C, N])] = self.create_exception_condition_no_response_pattern
        self.apply_exceptions[frozenset([M, N])] = self.create_exception_milestone_no_response_pattern
        self.apply_exceptions[frozenset([M, E])] = self.create_exception_milestone_exclude_pattern
        self.apply_exceptions[frozenset([M, I])] = self.create_exception_milestone_include_pattern
        self.apply_exceptions[frozenset([M, R])] = self.create_exception_milestone_response_pattern
        # 0 constrain + 2 effect relations (6 - 2 [{R,N},{I,E}]) = 4
        self.apply_exceptions[frozenset([I, R])] = self.create_exception_response_include_pattern
        self.apply_exceptions[frozenset([E, R])] = self.create_exception_response_exclude_pattern
        self.apply_exceptions[frozenset([N, E])] = self.create_exception_no_response_exclude_pattern
        self.apply_exceptions[frozenset([N, I])] = self.create_exception_no_response_include_pattern
        # 2 constrain + 0 effect relations (1) = 1
        self.apply_exceptions[frozenset([C, M])] = self.create_exception_condition_milestone_pattern
        # 1 relation = 6
        self.apply_exceptions[frozenset([I])] = self.create_include_pattern
        self.apply_exceptions[frozenset([E])] = self.create_exclude_pattern
        self.apply_exceptions[frozenset([R])] = self.create_response_pattern
        self.apply_exceptions[frozenset([N])] = self.create_no_response_pattern
        self.apply_exceptions[frozenset([C])] = self.create_condition_pattern
        self.apply_exceptions[frozenset([M])] = self.create_milestone_pattern

    def filter_exceptional_cases(self, G):
        transition_types = {}
        for e in G['events']:
            for e_prime in G['events']:
                if e == e_prime:
                    # same event multiple self relations
                    if (e in G['responseTo'] and e_prime in G['responseTo'][e]) and (
                            e in G['excludesTo'] and e_prime in G['excludesTo'][e]) and \
                            (e in G['conditionsFor'] and e_prime in G['conditionsFor'][e]) and (
                            e in G['milestonesFor'] and e_prime in G['milestonesFor'][e]) and \
                            (e in G['includesTo'] and e_prime in G['includesTo'][e]) and (
                            e in G['noResponseTo'] and e_prime in G['noResponseTo'][e]):
                        G['conditionsFor'][e].remove(e_prime)
                        G['milestonesFor'][e].remove(e_prime)
                        G['responseTo'][e].remove(e_prime)
                        G['excludesTo'][e].remove(e_prime)
                        G['includesTo'][e].remove(e_prime)
                        G['noResponseTo'][e].remove(e_prime)
                        transition_types[e] = ['event']
                        self.self_exceptions['responseTo'].add(e)
                        self.self_exceptions[frozenset(['conditionsFor', 'milestonesFor'])].add(e)

                    if (e in G['responseTo'] and e_prime in G['responseTo'][e]) and (
                            e in G['excludesTo'] and e_prime in G['excludesTo'][e]):
                        G['responseTo'][e].remove(e_prime)
                        G['excludesTo'][e].remove(e_prime)
                        self.self_exceptions[frozenset(['excludesTo', 'responseTo'])].add(e)
                    if (e in G['conditionsFor'] and e_prime in G['conditionsFor'][e]) and (
                            e in G['milestonesFor'] and e_prime in G['milestonesFor'][e]):
                        G['conditionsFor'][e].remove(e_prime)
                        G['milestonesFor'][e].remove(e_prime)
                        transition_types[e] = ['event']
                        self.self_exceptions[frozenset(['conditionsFor', 'milestonesFor'])].add(e)
                    if (e in G['includesTo'] and e_prime in G['includesTo'][e]) and (
                            e in G['excludesTo'] and e_prime in G['excludesTo'][e]):
                        G['excludesTo'][e].remove(e_prime)
                    # same event one self relation
                    for rel in self.all_relations:
                        if e in G[rel] and e_prime in G[rel][e]:
                            G[rel][e].remove(e_prime)
                            self.self_exceptions[rel].add(e)
                            match rel:
                                case 'conditionsFor':
                                    # removes the creation of the init and initpend transitions
                                    transition_types[e] = ['event', 'pend']
                                case 'milestonesFor':
                                    # removes the creation of the initpend and pend transitions
                                    transition_types[e] = ['event', 'init']
                else:
                    # distinct events
                    for exception in self.exceptions.keys():
                        if len(exception)>1:
                            has_multiple_rel = True
                            for rel in exception:
                                has_multiple_rel = has_multiple_rel and (e in G[rel] and e_prime in G[rel][e])
                            if has_multiple_rel:
                                remove_from_g = True
                                if I in exception and E in exception:
                                    G[E][e].remove(e_prime)
                                    remove_from_g = False
                                if R in exception and N in exception:
                                    G[N][e].remove(e_prime)
                                    remove_from_g = False
                                if remove_from_g:
                                    self.exceptions[exception].add((e, e_prime))
                                    for rel in exception:
                                        G[rel][e].remove(e_prime)
                        else:
                            rel = list(exception)[0]
                            if e in G[rel] and e_prime in G[rel][e]:
                                self.exceptions[exception].add((e, e_prime))

        return G, transition_types

    def map_exceptional_cases_between_events(self, master_df):
        if self.debug:
            exceptions_copy = deepcopy(self.exceptions)
            for exception, pairs in exceptions_copy.items():
                key = ''.join(str(item) for item in exception)
                for pair in pairs:
                    self.exceptions[exception] = set([pair])
                    print(f'[i] Step {exception} {pair}')
                    master_df = self.apply_exceptions[exception](master_df)
                    self.aprs[(key,pair)] = deepcopy(master_df)
            return master_df
        else:
            for exception, pairs in self.exceptions.items():
                if len(pairs) > 0:
                    master_df = self.apply_exceptions[exception](master_df)
            return master_df

    def create_exception_condition_milestone_exclude_response_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([E, R, C, M])]:
            case = pd.DataFrame([[2,8,4,1],
                                 [4,0,0,5],
                                 [4,0,0,3],
                                 [4,0,0,1]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [0,4],
                                        [0,2]], index=[0,1,3], columns=['Re', 'Rex'])
            copy_to_all_index = [0,1]
            copy_pairwise_index = [3]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Rex' not in needed_columns:
                case = case.drop(index=[2,3])
                case_others = case_others.drop(index=[3])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(3)
            if 'In' not in needed_columns:
                case = case.drop(index=[1])
                case_others = case_others.drop(index=[1])
                copy_to_all_index.remove(1)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_milestone_exclude_no_response_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([E, N, C, M])]:
            case = pd.DataFrame([[2,8,4,0],
                                 [4,0,0,4],
                                 # [4,0,0,2],
                                 [4,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [0,4],
                                        [0,2]], index=[0,1,2], columns=['Re', 'Rex'])
            copy_to_all_index = [0,1]
            copy_pairwise_index = [2]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Rex' not in needed_columns:
                case = case.drop(index=[2,3])
                case_others = case_others.drop(index=[3])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(3)
            if 'In' not in needed_columns:
                case = case.drop(index=[1])
                case_others = case_others.drop(index=[1])
                copy_to_all_index.remove(1)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_milestone_include_response_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([I, R, C, M])]:
            case = pd.DataFrame([[3,8,5,0],
                                 [5,0,1,4],
                                 [5,0,1,2],
                                 [5,0,1,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [0,4],
                                        [0,2]], index=[0,1,3], columns=['Re', 'Rex'])
            copy_to_all_index = [0,1]
            copy_pairwise_index = [3]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Rex' not in needed_columns:
                case = case.drop(index=[2,3])
                case_others = case_others.drop(index=[3])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(3)
            if 'In' not in needed_columns:
                case = case.drop(index=[1])
                case_others = case_others.drop(index=[1])
                copy_to_all_index.remove(1)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_milestone_include_no_response_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([I, N, C, M])]:
            case = pd.DataFrame([[3,8,4,0],
                                 [5,0,0,4],
                                 # [5,0,0,2],
                                 [5,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [0,4],
                                        [0,2]], index=[0,1,2], columns=['Re', 'Rex'])
            copy_to_all_index = [0,1]
            copy_pairwise_index = [2]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Rex' not in needed_columns:
                case = case.drop(index=[2,3])
                case_others = case_others.drop(index=[3])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(3)
            if 'In' not in needed_columns:
                case = case.drop(index=[1])
                case_others = case_others.drop(index=[1])
                copy_to_all_index.remove(1)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_milestone_response_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([R, C, M])]:
            case = pd.DataFrame([[3,8,5,0],
                                 [4,0,0,5],
                                 [4,0,0,3],
                                 [4,0,0,1]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [0,4],
                                        [0,2]], index=[0,1,3], columns=['Re', 'Rex'])
            copy_to_all_index = [0,1]
            copy_pairwise_index = [3]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Rex' not in needed_columns:
                case = case.drop(index=[2,3])
                case_others = case_others.drop(index=[3])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(3)
            if 'In' not in needed_columns:
                case = case.drop(index=[1])
                case_others = case_others.drop(index=[1])
                copy_to_all_index.remove(1)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_milestone_no_response_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([N, C, M])]:
            case = pd.DataFrame([[3,8,4,0],
                                 [4,0,0,4],
                                 # [4,0,0,2],
                                 [4,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [0,4],
                                        [0,2]], index=[0,1,2], columns=['Re', 'Rex'])
            copy_to_all_index = [0,1]
            copy_pairwise_index = [2]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Rex' not in needed_columns:
                case = case.drop(index=[2,3])
                case_others = case_others.drop(index=[3])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(3)
            if 'In' not in needed_columns:
                case = case.drop(index=[1])
                case_others = case_others.drop(index=[1])
                copy_to_all_index.remove(1)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_milestone_include_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([I, C, M])]:
            case = pd.DataFrame([[3,8,4,0],
                                 [5,0,0,4],
                                 # [5,0,6,7],
                                 [5,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [0,4],
                                        [6,7]], index=[0,1,2], columns=['Re', 'Rex'])
            copy_to_all_index = [0,1]
            copy_pairwise_index = [2]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Rex' not in needed_columns:
                case = case.drop(index=[2,3])
                case_others = case_others.drop(index=[3])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(3)
            if 'In' not in needed_columns:
                case = case.drop(index=[1])
                case_others = case_others.drop(index=[1])
                copy_to_all_index.remove(1)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_milestone_exclude_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([E, C, M])]:
            case = pd.DataFrame([[2,8,4,0],
                                 [4,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0]], index=[0], columns=['Re', 'Rex'])
            copy_to_all_index = [0]
            copy_pairwise_index = []

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns:
                case = case.drop(index=[1])
                # case_others = case_others.drop(index=[])
                # copy_to_all_index.remove()
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_milestone_no_response_include_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([I, N, M])]:
            case = pd.DataFrame([[3,0,4,0],
                                 [5,0,0,4],
                                 # [5,0,0,2],
                                 [5,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [0,4],
                                        [0,2]], index=[0,1,2], columns=['Re', 'Rex'])
            copy_to_all_index = [0,1]
            copy_pairwise_index = [2]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[1,2,3])
                case_others = case_others.drop(index=[1,3])
                copy_to_all_index.remove(1)
                copy_pairwise_index.remove(3)
            if 'Re' not in needed_columns:
                case = case.drop(index=[0])
                case_others = case_others.drop(index=[0])
                copy_to_all_index.remove(0)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_milestone_no_response_exclude_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([E, N, M])]:
            case = pd.DataFrame([[2,0,4,0],
                                 [4,0,0,4],
                                 # [4,0,0,2],
                                 [4,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [0,4],
                                        [0,2]], index=[0,1,2], columns=['Re', 'Rex'])
            copy_to_all_index = [0,1]
            copy_pairwise_index = [2]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[1,2,3])
                case_others = case_others.drop(index=[1,3])
                copy_to_all_index.remove(1)
                copy_pairwise_index.remove(3)
            if 'Re' not in needed_columns:
                case = case.drop(index=[0])
                case_others = case_others.drop(index=[0])
                copy_to_all_index.remove(0)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_milestone_response_include_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([I, R, M])]:
            case = pd.DataFrame([[5,0,5,4],
                                 [5,0,1,2],
                                 [5,0,1,0],
                                 [3,0,5,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[0,4],
                                        [0,2],
                                        [4,0]], index=[0,2,3], columns=['Re', 'Rex'])
            copy_to_all_index = [0,3]
            copy_pairwise_index = [2]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[1,2])
                case_others = case_others.drop(index=[2])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(2)
            if 'In' not in needed_columns and 'Re' not in needed_columns:
                case = case.drop(index=[3])
                case_others = case_others.drop(index=[3])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(3)
            if 'Rex' not in needed_columns:
                case = case.drop(index=[0])
                case_others = case_others.drop(index=[0])
                copy_to_all_index.remove(0)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_milestone_response_exclude_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([E, R, M])]:
            case = pd.DataFrame([[4,0,0,3],
                                 [4,0,0,5],
                                 [4,0,0,1],
                                 [2,0,4,5]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[0,4],
                                        [0,2],
                                        [4,0]], index=[1,2,3], columns=['Re', 'Rex'])
            copy_to_all_index = [1,3]
            copy_pairwise_index = [2]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[1,2])
                case_others = case_others.drop(index=[1,2])
                copy_to_all_index.remove(1)
                copy_pairwise_index.remove(2)
            if 'In' not in needed_columns and 'Re' not in needed_columns:
                case = case.drop(index=[3])
                case_others = case_others.drop(index=[3])
                copy_to_all_index.remove(3)
                # copy_pairwise_index.remove()
            if 'Rex' not in needed_columns:
                case = case.drop(index=[0])
                # case_others = case_others.drop(index=[])
                # copy_to_all_index.remove()
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_no_response_include_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([N, C, I])]:
            case = pd.DataFrame([[3,8,4,0],
                                 # [3,8,2,0],
                                 [3,8,0,0],
                                 [5,0,0,4],
                                 # [5,0,0,2],
                                 [5,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [2,0],
                                        [0,4],
                                        [0,2]], index=[0,1,2,3], columns=['Re', 'Rex'])
            copy_to_all_index = [0,2]
            copy_pairwise_index = [1,3]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Re' not in needed_columns:
                case = case.drop(index=[1,2])
                case_others = case_others.drop(index=[2])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(2)
            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[3,4,5])
                case_others = case_others.drop(index=[3,5])
                copy_to_all_index.remove(3)
                copy_pairwise_index.remove(5)
            if 'Re' not in needed_columns:
                case = case.drop(index=[0])
                case_others = case_others.drop(index=[0])
                copy_to_all_index.remove(0)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_no_response_exclude_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([N, C, E])]:
            case = pd.DataFrame([[2,8,4,0],
                                 # [2,8,2,0],
                                 [2,8,0,0],
                                 [4,0,0,4],
                                 # [4,0,0,2],
                                 [4,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [2,0],
                                        [0,4],
                                        [0,2]], index=[0,1,2,3], columns=['Re', 'Rex'])
            copy_to_all_index = [0,2]
            copy_pairwise_index = [1,3]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Re' not in needed_columns:
                case = case.drop(index=[1,2])
                case_others = case_others.drop(index=[2])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(2)
            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[3,4,5])
                case_others = case_others.drop(index=[3,5])
                copy_to_all_index.remove(3)
                copy_pairwise_index.remove(5)
            if 'Re' not in needed_columns:
                case = case.drop(index=[0])
                case_others = case_others.drop(index=[0])
                copy_to_all_index.remove(0)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_response_include_pattern(self, master_df):
        """
        :return:
        """
        for (event, event_prime) in self.exceptions[frozenset([I, R, C])]:
            case = pd.DataFrame([[3, 8, 5, 0],
                                    [3, 8, 3, 0],
                                    [3, 8, 1, 0],
                                    [5, 0, 1, 2],
                                    [5, 0, 1, 0],
                                    [5, 0, 5, 4]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [2,0],
                                        [0,2],
                                        [0,4]], index=[0,2,4,5], columns=['Re', 'Rex'])
            copy_to_all_index = [0,5]
            copy_pairwise_index = [2,4]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            # if '' not in needed_columns:
            #     case = case.drop(index=[])

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_response_exclude_pattern(self, master_df):
        """
        :return:
        """
        for (event, event_prime) in self.exceptions[frozenset([E, R, C])]:
            case = pd.DataFrame([[2, 8, 4, 1],
                                    [2, 8, 2, 1],
                                    [2, 8, 0, 1],
                                    [4, 0, 0, 5],
                                    [4, 0, 0, 3],
                                    [4, 0, 0, 1]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [2,0],
                                        [0,4],
                                        [0,2]], index=[0,2,3,5], columns=['Re', 'Rex'])
            copy_to_all_index = [0,3]
            copy_pairwise_index = [2,5]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            # if '' not in needed_columns:
            #     case = case.drop(index=[])

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_include_pattern(self, master_df):
        """
        :return:
        """
        for (event, event_prime) in self.exceptions[frozenset([I, C])]:
            case = pd.DataFrame([[3, 8, 0, 0],
                                       # [5, 0, 6, 7],
                                       [5, 0, 0, 0],
                                       [5, 0, 0, 4]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[6,7],
                                             [0,4]], index=[1,2], columns=['Re', 'Rex'])
            copy_to_all_index = [2]
            copy_pairwise_index = [1]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns and 'Re' not in needed_columns:
                case = case.drop(index=[1,2])
                case_others = case_others.drop(index=[2])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(2)
            if 'In' not in needed_columns:
                case = case.drop(index=[3])
                case_others = case_others.drop(index=[3])
                copy_to_all_index.remove(3)
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_exclude_pattern(self, master_df):
        """
        :return:
        """
        for (event, event_prime) in self.exceptions[frozenset([E, C])]:
            case = pd.DataFrame([[2, 8, 4, 0],
                                   # [2, 8, 7, 6],
                                   [2, 8, 0, 0],
                                   [4, 0, 0, 0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [7,6]], index=[0,1], columns=['Re', 'Rex'])
            copy_to_all_index = [0]
            copy_pairwise_index = [1]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Re' not in needed_columns:
                case = case.drop(index=[1,2])
                case_others = case_others.drop(index=[2])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(2)

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_response_pattern(self, master_df):
        """
        Done
        :return:
        """
        for (event, event_prime) in self.exceptions[frozenset([R, C])]:
            case = pd.DataFrame([[3, 8, 5, 0],
                                    [3, 8, 3, 0],
                                    [3, 8, 1, 0],
                                    [4, 0, 0, 5],
                                    [4, 0, 0, 1],
                                    [4, 0, 0, 3]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                             [2,0],
                                             [0,4],
                                             [0,2]], index=[0,2,3,4], columns=['Re', 'Rex'])
            copy_to_all_index = [0,3]
            copy_pairwise_index = [2,4]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns or 'Re' not in needed_columns:
                case = case.drop(index=[1,2])
                case_others = case_others.drop(index=[2])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(2)
            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[3,4])
                case_others = case_others.drop(index=[3,4])
                copy_to_all_index.remove(3)
                copy_pairwise_index.remove(4)
            if  'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[5])
                # case_others = case_others.drop(index=[])
                # copy_to_all_index.remove()
                # copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_response_include_pattern(self, master_df):
        """
        DONE
        :return:
        """
        for (event, event_prime) in self.exceptions[frozenset([I, R])]:
            case = pd.DataFrame([[3, 0, 5, 0],
                                      [3, 0, 3, 0],
                                      [3, 0, 1, 0],
                                      [5, 0, 5, 4],
                                      [5, 0, 1, 2],
                                      [5, 0, 1, 0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [2,0],
                                        [0,4],
                                        [0,2]], index=[0,2,3,5], columns=['Re', 'Rex'])
            copy_to_all_index = [0,3]
            copy_pairwise_index = [2,5]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Re' not in needed_columns:
                case = case.drop(index=[1,2])
                case_others = case_others.drop(index=[2])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(2)
            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[3])
                case_others = case_others.drop(index=[3])
                copy_to_all_index.remove(3)
                # copy_pairwise_index.remove()
            if 'Rex' not in needed_columns:
                case = case.drop(index=[4,5])
                case_others = case_others.drop(index=[5])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(5)

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_response_exclude_pattern(self, master_df):
        """
        DONE
        :return:
        """
        for (event, event_prime) in self.exceptions[frozenset([E, R])]:
            case = pd.DataFrame([[2, 0, 4, 1],
                                      [2, 0, 2, 1],
                                      [2, 0, 0, 1],
                                      [4, 0, 0, 5],
                                      [4, 0, 0, 1],
                                      [4, 0, 0, 3]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [2,0],
                                        [0,4],
                                        [0,2]], index=[0,2,3,4], columns=['Re', 'Rex'])
            copy_to_all_index = [0,3]
            copy_pairwise_index = [2,4]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Re' not in needed_columns:
                case = case.drop(index=[1,2])
                case_others = case_others.drop(index=[2])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(2)
            if 'Rex' not in needed_columns:
                case = case.drop(index=[3,4,5])
                case_others = case_others.drop(index=[3,4])
                copy_to_all_index.remove(3)
                copy_pairwise_index.remove(4)

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_no_response_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([N, C])]:
            case = pd.DataFrame([[3,8,4,0],
                                 # [3,8,2,0],
                                 [3,8,0,0],
                                 [4,0,0,4],
                                 # [4,0,0,2],
                                 [4,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [2,0],
                                        [0,4],
                                        [0,2]], index=[0,1,2,3], columns=['Re', 'Rex'])
            copy_to_all_index = [0,2]
            copy_pairwise_index = [1,3]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Re' not in needed_columns:
                case = case.drop(index=[1,2])
                case_others = case_others.drop(index=[2])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(2)
            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[3,4,5])
                case_others = case_others.drop(index=[3,5])
                copy_to_all_index.remove(3)
                copy_pairwise_index.remove(5)

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_no_response_exclude_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([E, N])]:
            case = pd.DataFrame([#[2,0,2,0],
                                 [2,0,0,0],
                                 [4,0,0,4],
                                 [4,0,0,2],
                                 # [4,0,0,0],
                                 [2,0,4,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[2,0],
                                        [0,4],
                                        [0,2],
                                        [4,0]], index=[0,1,2,3], columns=['Re', 'Rex'])
            copy_to_all_index = [1,3]
            copy_pairwise_index = [0,2]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'Re' not in needed_columns:
                case = case.drop(index=[0,1])
                case_others = case_others.drop(index=[1])
                # copy_to_all_index.remove()
                copy_pairwise_index.remove(1)
            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[2,3,4])
                case_others = case_others.drop(index=[2,3])
                copy_to_all_index.remove(2)
                copy_pairwise_index.remove(3)

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_no_response_include_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([I, N])]:
            case = pd.DataFrame([#[3,0,2,0],
                                 [3, 0, 0, 0],
                                 [5,0,0,4],
                                 # [5,0,0,2],
                                 [5,0,0,0],
                                 [3,0,4,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[2,0],
                                        [0,4],
                                        [0,2],
                                        [4,0]], index=[0,1,2,3], columns=['Re', 'Rex'])
            copy_to_all_index = [1,3]
            copy_pairwise_index = [0,2]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns and 'Re' not in needed_columns:
                case = case.drop(index=[0,1])
                case_others = case_others.drop(index=[1])
                copy_pairwise_index.remove(1)
            if 'In' not in needed_columns:
                case = case.drop(index=[2])
                case_others = case_others.drop(index=[2])
                copy_to_all_index.remove(2)
            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[3,4])
                case_others = case_others.drop(index=[4])
                copy_pairwise_index.remove(4)
            if 'In' not in needed_columns or 'Re' not in needed_columns:
                case = case.drop(index=[5])
                case_others = case_others.drop(index=[5])
                copy_to_all_index.remove(5)
            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_milestone_no_response_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([N, M])]:
            case = pd.DataFrame([[4,0,0,4],
                                 # [4,0,0,2],
                                 [4,0,0,0],
                                 [3,0,4,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[0,4],
                                        [0, 2],
                                        [4,0]], index=[0,1,2], columns=['Re', 'Rex'])
            copy_to_all_index = [0,2]
            copy_pairwise_index = [1]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[0])
                case_others = case_others.drop(index=[0])
                copy_to_all_index.remove(0)
            if 'In' not in needed_columns:
                case = case.drop(index=[1,2])
                case_others = case_others.drop(index=[2])
                copy_pairwise_index.remove(2)
            if 'In' not in needed_columns or 'Re' not in needed_columns:
                case = case.drop(index=[3])
                case_others = case_others.drop(index=[3])
                copy_to_all_index.remove(3)
            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_condition_milestone_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([C, M])]:
            case = pd.DataFrame([[4,0,0,0],
                                 [3,8,4,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0]], index=[1], columns=['Re', 'Rex'])
            copy_to_all_index = [1]
            copy_pairwise_index = []

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns:
                case = case.drop(index=[0])
            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_milestone_exclude_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([E, M])]:
            case = pd.DataFrame([[4,0,0,0],
                                 [2,0,4,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0]], index=[1], columns=['Re', 'Rex'])
            copy_to_all_index = [1]
            copy_pairwise_index = []

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns:
                case = case.drop(index=[0])
            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_milestone_include_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([I, M])]:
            case = pd.DataFrame([#[5,0,6,7],
                                 [5,0,0,0],
                                 [5,0,0,4],
                                 [3,0,4,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[6,7],
                                        [0,4],
                                        [4,0]], index=[0,1,2], columns=['Re', 'Rex'])
            copy_to_all_index = [1,2]
            copy_pairwise_index = [0]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
            if 'In' not in needed_columns:
                case = case.drop(index=[3])
                case_others = case_others.drop(index=[3])
                copy_to_all_index.remove(3)
            if 'Re' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[0,1,2])
                case_others = case_others.drop(index=[1,2])
                copy_to_all_index.remove(2)
                copy_pairwise_index.remove(1)
            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns!={'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exception_milestone_response_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([R, M])]:
            case = pd.DataFrame([[3,0,5,0],
                                 [4,0,0,3],
                                 [4,0,0,5],
                                 [4,0,0,1]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [0,4],
                                        [0,2]], index=[0,2,3], columns=['Re', 'Rex'])
            copy_to_all_index = [0,2]
            copy_pairwise_index = [3]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])

            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[1,2,3])
                case_others = case_others.drop(index=[2,3])
                copy_to_all_index.remove(2)
                copy_pairwise_index.remove(3)
            if 'Re' not in needed_columns:
                case = case.drop(index=[0])
                case_others = case_others.drop(index=[0])
                copy_to_all_index.remove(0)

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_include_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([I])]:
            case = pd.DataFrame([[3, 0, 0, 0],
                                 [1, 0, 6, 7],
                                 [5, 0, 0, 4]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[6, 7],
                                        [0, 4]], index=[1, 2], columns=['Re', 'Rex'])
            copy_to_all_index = [2]
            copy_pairwise_index = [1]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
            if 'Re' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[1])

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_exclude_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([E])]:
            case = pd.DataFrame([[4,0,0,0],
                                 [2,0,4,0],
                                 [2,0,7,6]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [7,6]], index=[1,2], columns=['Re', 'Rex'])
            copy_to_all_index = [1]
            copy_pairwise_index = [2]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
            if 'Re' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[2])
                case_others = case_others.drop(index=[2])
                copy_pairwise_index.remove(2)

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_response_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([R])]:
            case = pd.DataFrame([[3, 0, 5, 0],
                                 [3, 0, 1, 0],
                                 [3, 0, 3, 0],
                                 [4, 0, 0, 5],
                                 [4, 0, 0, 1],
                                 [4, 0, 0, 3]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4, 0],
                                        [2, 0],
                                        [0, 4],
                                        [0, 2]], index=[0, 1, 3, 4], columns=['Re', 'Rex'])
            copy_to_all_index = [0, 3]
            copy_pairwise_index = [1, 4]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
            # needed_columns = list([c.split('_')[0] if '_' in c else c for c in needed_columns])
            # col_counter = dict(Counter(needed_columns))
            # if 'Re' in col_counter and col_counter['Re']<=1:
            #     case = case.drop(index=[1])
            #     case_others = case_others.drop(index=[1])
            #     copy_pairwise_index.remove(1)
            # if 'Rex' in col_counter and col_counter['Rex']<=1:
            #     case = case.drop(index=[4])
            #     case_others = case_others.drop(index=[4])
            #     copy_pairwise_index.remove(4)
            # needed_columns = set(needed_columns)
            if 'Re' not in needed_columns:
                case = case.drop(index=[0, 1, 2])
                case_others = case_others.drop(index=[0, 1])
                copy_to_all_index.remove(0)
                copy_pairwise_index.remove(1)
            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[3, 4, 5])
                case_others = case_others.drop(index=[3, 4])
                copy_to_all_index.remove(3)
                copy_pairwise_index.remove(4)

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_no_response_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([N])]:
            case = pd.DataFrame([[3,0,4,0],
                                 # [3,0,2,0],
                                 [3,0,0,0],
                                 [4,0,0,4],
                                 # [4,0,0,2],
                                 [4,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0],
                                        [2, 0],
                                        [0,4],
                                        [0,2]], index=[0,1,2,3], columns=['Re', 'Rex'])
            copy_to_all_index = [0,2]
            copy_pairwise_index = [1,3]

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
            if 'Re' not in needed_columns:
                case = case.drop(index=[0,1,2])
                case_others = case_others.drop(index=[0,2])
                copy_to_all_index.remove(0)
                copy_pairwise_index.remove(2)
            if 'In' not in needed_columns and 'Rex' not in needed_columns:
                case = case.drop(index=[2,3])
                case_others = case_others.drop(index=[2,3])
                copy_to_all_index.remove(2)
                copy_pairwise_index.remove(3)
                # case = case.drop(index=[3,4,5])
                # case_others = case_others.drop(index=[3,5])
                # copy_to_all_index.remove(3)
                # copy_pairwise_index.remove(5)

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_condition_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([C])]:
            case = pd.DataFrame([[4,0,0,0],
                                 [3,8,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
            if 'In' not in needed_columns:
                case = case.drop(index=[0])
            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, pd.DataFrame([[0,0],[0,0]]), [], [], event_to_deadline)
            master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_milestone_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([M])]:
            case = pd.DataFrame([[4,0,0,0],
                                 [3,0,4,0]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[4,0]], index=[1], columns=['Re', 'Rex'])
            copy_to_all_index = [1]
            copy_pairwise_index = []

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
            if 'In' not in needed_columns:
                case = case.drop(index=[0])

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df

    def create_generic_template_pattern(self, master_df):
        for (event, event_prime) in self.exceptions[frozenset([])]:
            case = pd.DataFrame([[]], columns=['In', 'Ex', 'Re', 'Rex'])
            case_others = pd.DataFrame([[]], index=[], columns=['Re', 'Rex'])
            copy_to_all_index = []
            copy_pairwise_index = []

            needed_columns = master_df.loc[event][event_prime].columns
            needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
            if '' not in needed_columns:
                case = case.drop(index=[])
                case_others = case_others.drop(index=[])
                copy_to_all_index.remove()
                copy_pairwise_index.remove()

            if 'Re' in needed_columns:
                event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
                event_to_deadline = self.event_to_deadline_map[event_prime]
                case = prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline)
            if needed_columns != {'No'}:
                master_df = copy_event_rows(event, event_prime, master_df, case)
        return master_df