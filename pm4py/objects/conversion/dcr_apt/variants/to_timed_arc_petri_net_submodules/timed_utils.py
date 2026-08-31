from pm4py.objects.petri_net.timed_arc_net.obj import *
from pm4py.objects.petri_net.utils import petri_utils as pn_utils
from pm4py.objects.dcr.obj import TemplateRelations as Relations
import pandas as pd
import numpy as np

from copy import deepcopy

# Function to copy rows of a specified event key n times
def copy_event_rows(src, trg, master_df, relation_table):
    needed_columns = master_df.loc[src][trg].columns
    needed_cases = relation_table[needed_columns]
    n = len(needed_cases)
    m = len(master_df.loc[src])
    repeated_df = pd.DataFrame(np.tile(master_df.loc[src], (n, 1)), columns=master_df.columns, index=pd.MultiIndex.from_product([[src], [i for i in range(n * m)]]))
    repeated_relation_df = pd.DataFrame(np.repeat(needed_cases, m, axis=0), columns=needed_cases.columns,
                                        index=pd.MultiIndex.from_product([[src], [i for i in range(n * m)]]))

    repeated_df.iloc[:, repeated_df.columns.get_level_values(0) == trg] = repeated_relation_df
    master_df = master_df.drop(src, level=0)
    master_df = pd.concat([master_df, repeated_df])
    return master_df


def prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline):
    pend_others = [f'Re_{v}' for k, v in event_to_deadline.items()]
    pend_excl_others = [f'Rex_{v}' for k, v in event_to_deadline.items()]
    if event_place:
        pend_place = f'Re_{event_place}'
        # pend_others.remove(pend_place)
        pend_others = list(filter((pend_place).__ne__, pend_others))
        pend_excl_place = f'Rex_{event_place}'
        # pend_excl_others.remove(pend_excl_place)
        pend_excl_others = list(filter((pend_excl_place).__ne__, pend_excl_others))
        case = case.rename({'Re': pend_place, 'Rex': pend_excl_place}, axis='columns')
    else:
        if 'Re' in case.columns:
            case = case.drop(['Re'], axis='columns')
        if 'Rex' in case.columns:
            case = case.drop(['Rex'], axis='columns')
    pend_others = list(set(pend_others))
    pend_excl_others = list(set(pend_excl_others))
    x = len(pend_others)
    if x == 0:
        case = case.drop(copy_pairwise_index,axis='rows')
        return case
    else:
        cols = pend_others
        cols.extend(pend_excl_others)
        case_all = pd.DataFrame(np.repeat(case_others.loc[copy_to_all_index], x, axis=1), index=copy_to_all_index, columns=cols)
        mat = case_others.loc[copy_pairwise_index].to_numpy()
        idx = np.repeat(copy_pairwise_index,x)
        ar = np.zeros([s * x for s in mat.shape], mat.dtype)
        for i in range(x):
            ar[i::x, i::x] = mat
        case_pairwise = pd.DataFrame(ar, columns=cols, index=idx)
        case = pd.concat([case, case_all], axis=1).fillna(0)
        case = case.astype(int)
        case = pd.concat([case, case.loc[copy_pairwise_index * (x - 1)]])
        case_pairwise = case_pairwise.sort_index()
        case.loc[copy_pairwise_index, cols] = case_pairwise
        # case = replace_submatrix(case, case_pairwise)
        return case

# def prepare_timed_case_broken(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline):
#     pend_others = [f'Re_{v}' for k, v in event_to_deadline.items()]
#     pend_excl_others = [f'Rex_{v}' for k, v in event_to_deadline.items()]
#     if event_place:
#         pend_place = f'Re_{event_place}'
#         pend_others.remove(pend_place)
#         pend_excl_place = f'Rex_{event_place}'
#         pend_excl_others.remove(pend_excl_place)
#         case = case.rename({'Re': pend_place, 'Rex': pend_excl_place}, axis='columns')
#     else:
#         if 'Re' in case.columns:
#             case = case.drop(['Re'], axis='columns')
#         if 'Rex' in case.columns:
#             case = case.drop(['Rex'], axis='columns')
#
#     x = len(pend_others)
#     cols = pend_others
#     cols = cols.extend(pend_excl_others)
#     case_all = pd.DataFrame(np.repeat(case_others.loc[copy_to_all_index], x, axis=1), index=copy_to_all_index, columns=cols)
#     case = pd.concat([case, case_all], axis=1).fillna(0)
#     case = case.astype(int)
#
#     if x > 0:
#         mat = case_others.loc[copy_pairwise_index].to_numpy()
#         idx = np.repeat(copy_pairwise_index,x)
#         ar = np.zeros([s * x for s in mat.shape], mat.dtype)
#         for i in range(x):
#             ar[i::x, i::x] = mat
#         case_pairwise = pd.DataFrame(ar, columns=cols, index=idx)
#         case = pd.concat([case, case.loc[copy_pairwise_index * (x - 1)]])
#         case_pairwise = case_pairwise.sort_index()
#         case.loc[copy_pairwise_index, cols] = case_pairwise
#         # case = replace_submatrix(case, case_pairwise)
#     else:
#         case = case.drop(copy_pairwise_index,axis='rows')
#     # print(case)
#     return case