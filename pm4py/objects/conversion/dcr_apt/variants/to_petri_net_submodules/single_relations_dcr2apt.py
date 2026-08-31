import pandas as pd
from pm4py.objects.conversion.dcr_apt.variants.to_petri_net_submodules.utils import copy_event_rows

class SingleRelations(object):

    def create_include_pattern(self, event, event_prime, master_df):
        include_case = pd.DataFrame([[3, 0, 0, 0],
                                      [5, 0, 1, 2],
                                      [5, 0, 0, 4]], columns=['In', 'Ex', 'Re', 'Rex'])
        needed_columns = master_df.loc[event][event_prime].columns
        if 'Re' in needed_columns and 'Rex' in needed_columns:
            include_case = include_case.drop(index=[2])
        return copy_event_rows(event, event_prime, master_df, include_case)

    def create_exclude_pattern(self, event, event_prime, master_df):
        exclude_case = pd.DataFrame([[4, 0, 0, 0],
                                      [2, 0, 4, 0],
                                      [2, 0, 2, 1]], columns=['In', 'Ex', 'Re', 'Rex'])
        needed_columns = master_df.loc[event][event_prime].columns
        if 'Re' in needed_columns and 'Rex' in needed_columns:
            exclude_case = exclude_case.drop(index=[2])
        return copy_event_rows(event, event_prime, master_df, exclude_case)

    def create_response_pattern(self, event, event_prime, master_df):
        response_case = pd.DataFrame([[3, 0, 5, 0],
                                       [3, 0, 3, 2],
                                       [4, 0, 0, 5],
                                       [4, 0, 0, 3]], columns=['In', 'Ex', 'Re', 'Rex'])
        needed_columns = master_df.loc[event][event_prime].columns
        if 'Rex' not in needed_columns:
            response_case = response_case.drop(index=[2,3])
        return copy_event_rows(event, event_prime, master_df, response_case)

    def create_no_response_pattern(self, event, event_prime, master_df):
        noresponse_case = pd.DataFrame([[3,0,2,0],
                                        [4,0,0,4],
                                        [4,0,0,2],
                                        [3,0,4,0]], columns=['In', 'Ex', 'Re', 'Rex'])
        needed_columns = master_df.loc[event][event_prime].columns
        if 'Rex' not in needed_columns:
            noresponse_case = noresponse_case.drop(index=[2,3])
        return copy_event_rows(event, event_prime, master_df, noresponse_case)

    def create_condition_pattern(self, event, event_prime, master_df):
        condition_case = pd.DataFrame([[3, 3, 0, 0],
                                       [4, 0, 0, 0]], columns=['In', 'Ex', 'Re', 'Rex'])
        needed_columns = master_df.loc[event][event_prime].columns
        if 'In' not in needed_columns:
            condition_case = condition_case.drop(index=[1])
        return copy_event_rows(event, event_prime, master_df, condition_case)

    def create_milestone_pattern(self, event, event_prime, master_df):
        milestone_case = pd.DataFrame([[4, 0, 0, 0],
                                       [3, 0, 4, 0]], columns=['In', 'Ex', 'Re', 'Rex'])
        needed_columns = master_df.loc[event][event_prime].columns
        if 'In' not in needed_columns:
            milestone_case = milestone_case.drop(index=[1])
        return copy_event_rows(event, event_prime, master_df, milestone_case)
