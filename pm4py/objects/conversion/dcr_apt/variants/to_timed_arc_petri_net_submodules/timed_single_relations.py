import numpy as np
import pandas as pd
from pm4py.objects.conversion.dcr_apt.variants.to_timed_arc_petri_net_submodules.timed_utils import copy_event_rows, prepare_timed_case

class TimedSingleRelations(object):

    def __init__(self, event_to_deadline_map) -> None:
        self.event_to_deadline_map = event_to_deadline_map

    def create_include_pattern(self, event, event_prime, master_df):
        case = pd.DataFrame([[3,0,0,0],
                             [1,0,6,7],
                             [5,0,0,4]], columns=['In', 'Ex', 'Re', 'Rex'])
        case_others = pd.DataFrame([[6,7],
                                    [0,4]], index=[1,2], columns=['Re', 'Rex'])
        copy_to_all_index = [2]
        copy_pairwise_index = [1]

        needed_columns = master_df.loc[event][event_prime].columns
        needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
        if 'Re' not in needed_columns and 'Rex' not in needed_columns:
            case = case.drop(index=[1])
        else:
            event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
            event_to_deadline = self.event_to_deadline_map[event_prime]
            case = prepare_timed_case(event_place,case,case_others,copy_to_all_index,copy_pairwise_index,event_to_deadline)
        return copy_event_rows(event, event_prime, master_df, case)

    def create_exclude_pattern(self, event, event_prime, master_df):
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
        else:
            event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
            event_to_deadline = self.event_to_deadline_map[event_prime]
            case = prepare_timed_case(event_place, case,case_others,copy_to_all_index,copy_pairwise_index,event_to_deadline)
        return copy_event_rows(event, event_prime, master_df, case)

    def create_response_pattern(self, event, event_prime, master_df):
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
        event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
        event_to_deadline = self.event_to_deadline_map[event_prime]
        case = prepare_timed_case(event_place, case,case_others,copy_to_all_index,copy_pairwise_index,event_to_deadline)
        return copy_event_rows(event, event_prime, master_df, case)

    def create_no_response_pattern(self, event, event_prime, master_df):
        case = pd.DataFrame([[3,0,4,0],
                             [3,0,2,0],
                             [3,0,0,0],
                             [4,0,0,4],
                             [4,0,0,2],
                             [4,0,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])
        case_others = pd.DataFrame([[4,0],
                                    [2, 0],
                                    [0,4],
                                    [2,0]], index=[0,2,3,5], columns=['Re', 'Rex'])
        copy_to_all_index = [0,3]
        copy_pairwise_index = [2,5]

        needed_columns = master_df.loc[event][event_prime].columns
        needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
        if 'Re' not in needed_columns:
            case = case.drop(index=[0,1,2])
            case_others = case_others.drop(index=[0,2])
            copy_to_all_index.remove(0)
            copy_pairwise_index.remove(2)
        if 'In' not in needed_columns and 'Rex' not in needed_columns:
            case = case.drop(index=[3,4,5])
            case_others = case_others.drop(index=[3,5])
            copy_to_all_index.remove(3)
            copy_pairwise_index.remove(5)

        event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
        event_to_deadline = self.event_to_deadline_map[event_prime]
        case = prepare_timed_case(event_place, case,case_others,copy_to_all_index,copy_pairwise_index,event_to_deadline)
        return copy_event_rows(event, event_prime, master_df, case)

    def create_condition_pattern(self, event, event_prime, master_df):
        case = pd.DataFrame([[4,0,0,0],
                             [3,8,0,0]], columns=['In', 'Ex', 'Re', 'Rex'])

        needed_columns = master_df.loc[event][event_prime].columns
        needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
        if 'In' not in needed_columns:
            case = case.drop(index=[0])

        return copy_event_rows(event, event_prime, master_df, case)

    def create_milestone_pattern(self, event, event_prime, master_df):
        case = pd.DataFrame([[4,0,0,0],
                             [3,0,4,0]], columns=['In', 'Ex', 'Re', 'Rex'])
        case_others = pd.DataFrame([[4,0]], index=[1], columns=['Re', 'Rex'])
        copy_to_all_index = [1]
        copy_pairwise_index = []

        needed_columns = master_df.loc[event][event_prime].columns
        needed_columns = set([c.split('_')[0] if '_' in c else c for c in needed_columns])
        if 'In' not in needed_columns:
            case = case.drop(index=[0])

        event_place = self.event_to_deadline_map[event_prime][event] if event in self.event_to_deadline_map[event_prime] else None
        event_to_deadline = self.event_to_deadline_map[event_prime]
        case = prepare_timed_case(event_place, case,case_others,copy_to_all_index,copy_pairwise_index,event_to_deadline)
        return copy_event_rows(event, event_prime, master_df, case)

