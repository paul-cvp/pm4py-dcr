from copy import deepcopy
from enum import Enum

import pandas as pd
import numpy as np

class ArcType(Enum):
    NoArc = 0  #
    TtoP = 1  # -->
    PtoT = 2  # <--
    Read = 3  # <->
    Both = 3  # <->
    Inhib = 4  # o--
    TtoPandInhib = 5  # o->
    TtP = 6 # --<>
    PtT = 7 # <>--
    TRead = 8 # <>-<>
    TBoth = 8 # <>-<>


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
