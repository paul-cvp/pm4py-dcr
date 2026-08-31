from copy import deepcopy
from itertools import combinations


num_to_sym_tex = {0:'',1:'\oa{}',2:'\ia{}',3:'\\readArc{}',4:'\inhib{}',5:'\inhiboa{}',6:'\\toa{}',7:'\\tia{}',8:'\\ttioa'}

tex_headers = {"rel_includesTo_responseTo_conditionsFor_milestonesFor":"\{\includeRel,\\trespRel,\\topcondRel,\opmilestoneRel\}",
"rel_includesTo_noResponseTo_conditionsFor_milestonesFor":"\{\includeRel,\\noresponseRel,\\topcondRel,\opmilestoneRel\}",
"rel_excludesTo_responseTo_conditionsFor_milestonesFor":"\{\excludeRel,\\trespRel,\\topcondRel,\opmilestoneRel\}",
"rel_excludesTo_noResponseTo_conditionsFor_milestonesFor":"\{\excludeRel,\\noresponseRel,\\topcondRel,\opmilestoneRel\}",
"rel_includesTo_responseTo_conditionsFor":"\{\includeRel,\\trespRel,\\topcondRel\}",
"rel_includesTo_responseTo_milestonesFor":"\{\includeRel,\\trespRel,\opmilestoneRel\}",
"rel_includesTo_noResponseTo_conditionsFor":"\{\includeRel,\\noresponseRel,\\topcondRel\}",
"rel_includesTo_noResponseTo_milestonesFor":"\{\includeRel,\\noresponseRel,\opmilestoneRel\}",
"rel_includesTo_conditionsFor_milestonesFor":"\{\includeRel,\\topcondRel,\opmilestoneRel\}",
"rel_excludesTo_responseTo_conditionsFor":"\{\excludeRel,\\trespRel,\\topcondRel\}",
"rel_excludesTo_responseTo_milestonesFor":"\{\excludeRel,\\trespRel,\opmilestoneRel\}",
"rel_excludesTo_noResponseTo_conditionsFor":"\{\excludeRel,\\noresponseRel,\\topcondRel\}",
"rel_excludesTo_noResponseTo_milestonesFor":"\{\excludeRel,\\noresponseRel,\opmilestoneRel\}",
"rel_excludesTo_conditionsFor_milestonesFor":"\{\excludeRel,\\topcondRel,\opmilestoneRel\}",
"rel_responseTo_conditionsFor_milestonesFor":"\{\\trespRel,\\topcondRel,\opmilestoneRel\}",
"rel_noResponseTo_conditionsFor_milestonesFor":"\{\\noresponseRel,\\topcondRel,\opmilestoneRel\}",
"rel_includesTo_responseTo":"\{\includeRel,\\trespRel\}",
"rel_includesTo_noResponseTo":"\{\includeRel,\\noresponseRel\}",
"rel_includesTo_conditionsFor":"\{\includeRel,\\topcondRel\}",
"rel_includesTo_milestonesFor":"\{\includeRel,\opmilestoneRel\}",
"rel_excludesTo_responseTo":"\{\excludeRel,\\trespRel\}",
"rel_excludesTo_noResponseTo":"\{\excludeRel,\\noresponseRel\}",
"rel_excludesTo_conditionsFor":"\{\excludeRel,\\topcondRel\}",
"rel_excludesTo_milestonesFor":"\{\excludeRel,\opmilestoneRel\}",
"rel_responseTo_conditionsFor":"\{\\trespRel,\\topcondRel\}",
"rel_responseTo_milestonesFor":"\{\\trespRel,\opmilestoneRel\}",
"rel_noResponseTo_conditionsFor":"\{\\noresponseRel,\\topcondRel\}",
"rel_noResponseTo_milestonesFor":"\{\\noresponseRel,\opmilestoneRel\}",
"rel_conditionsFor_milestonesFor":"\{\\topcondRel,\opmilestoneRel\}",
"rel_includesTo":"\{\includeRel\}",
"rel_excludesTo":"\{\excludeRel\}",
"rel_responseTo":"\{\\trespRel\}",
"rel_noResponseTo":"\{\\noresponseRel\}",
"rel_conditionsFor":"\{\\topcondRel\}",
"rel_milestonesFor":"\{\opmilestoneRel\}"}

copy_rels = {
# "rel_includesTo_excludesTo_responseTo_noResponseTo_conditionsFor_milestonesFor":([],[]),
# "rel_includesTo_excludesTo_responseTo_noResponseTo_conditionsFor":([],[]),
# "rel_includesTo_excludesTo_responseTo_noResponseTo_milestonesFor":([],[]),
# "rel_includesTo_excludesTo_responseTo_conditionsFor_milestonesFor":([],[]),
# "rel_includesTo_excludesTo_noResponseTo_conditionsFor_milestonesFor":([],[]),
# "rel_includesTo_responseTo_noResponseTo_conditionsFor_milestonesFor":([],[]),
# "rel_excludesTo_responseTo_noResponseTo_conditionsFor_milestonesFor":([],[]),
# "rel_includesTo_excludesTo_responseTo_noResponseTo":([],[]),
# "rel_includesTo_excludesTo_responseTo_conditionsFor":([],[]),
# "rel_includesTo_excludesTo_responseTo_milestonesFor":([],[]),
# "rel_includesTo_excludesTo_noResponseTo_conditionsFor":([],[]),
# "rel_includesTo_excludesTo_noResponseTo_milestonesFor":([],[]),
# "rel_includesTo_excludesTo_conditionsFor_milestonesFor":([],[]),
# "rel_includesTo_responseTo_noResponseTo_conditionsFor":([],[]),
# "rel_includesTo_responseTo_noResponseTo_milestonesFor":([],[]),
"rel_includesTo_responseTo_conditionsFor_milestonesFor":([0,1],[3]),
"rel_includesTo_noResponseTo_conditionsFor_milestonesFor":([0,1],[2]),
# "rel_excludesTo_responseTo_noResponseTo_conditionsFor":([],[]),
# "rel_excludesTo_responseTo_noResponseTo_milestonesFor":([],[]),
"rel_excludesTo_responseTo_conditionsFor_milestonesFor":([0,1],[3]),
"rel_excludesTo_noResponseTo_conditionsFor_milestonesFor":([0,1],[2]),
# "rel_responseTo_noResponseTo_conditionsFor_milestonesFor":([],[]),
# "rel_includesTo_excludesTo_responseTo":([],[]),
# "rel_includesTo_excludesTo_noResponseTo":([],[]),
# "rel_includesTo_excludesTo_conditionsFor":([],[]),
# "rel_includesTo_excludesTo_milestonesFor":([],[]),
# "rel_includesTo_responseTo_noResponseTo":([],[]),
"rel_includesTo_responseTo_conditionsFor":([0,5],[2,4]),
"rel_includesTo_responseTo_milestonesFor":([0,3],[2]),
"rel_includesTo_noResponseTo_conditionsFor":([0,2],[1,3]),
"rel_includesTo_noResponseTo_milestonesFor":([0,1],[2]),
"rel_includesTo_conditionsFor_milestonesFor":([0,1],[2]),
# "rel_excludesTo_responseTo_noResponseTo":([],[]),
"rel_excludesTo_responseTo_conditionsFor":([0,3],[2,5]),
"rel_excludesTo_responseTo_milestonesFor":([1,3],[2]),
"rel_excludesTo_noResponseTo_conditionsFor":([0,2],[1,3]),
"rel_excludesTo_noResponseTo_milestonesFor":([0,1],[2]),
"rel_excludesTo_conditionsFor_milestonesFor":([0],[]),
# "rel_responseTo_noResponseTo_conditionsFor":([],[]),
# "rel_responseTo_noResponseTo_milestonesFor":([],[]),
"rel_responseTo_conditionsFor_milestonesFor":([0,1],[3]),
"rel_noResponseTo_conditionsFor_milestonesFor":([0,1],[2]),
# "rel_includesTo_excludesTo":([],[]),
"rel_includesTo_responseTo":([0,3],[2,5]),
"rel_includesTo_noResponseTo":([1,3],[0,2]),
"rel_includesTo_conditionsFor":([2],[1]),
"rel_includesTo_milestonesFor":([1,2],[0]),
"rel_excludesTo_responseTo":([0,3],[2,4]),
"rel_excludesTo_noResponseTo":([1,3],[0,2]),
"rel_excludesTo_conditionsFor":([0],[1]),
"rel_excludesTo_milestonesFor":([1],[]),
# "rel_responseTo_noResponseTo":([],[]),
"rel_responseTo_conditionsFor":([0,3],[2,4]),
"rel_responseTo_milestonesFor":([0,2],[3]),
"rel_noResponseTo_conditionsFor":([0,2],[1,3]),
"rel_noResponseTo_milestonesFor":([0,2],[1]),
"rel_conditionsFor_milestonesFor":([1],[]),
"rel_includesTo":([2],[1]),
"rel_excludesTo":([1],[2]),
"rel_responseTo":([0,3],[1,4]),
"rel_noResponseTo":([0,2],[1,3]),
"rel_conditionsFor":([],[]),
"rel_milestonesFor":([1],[]),
}

red_rules ={
"rel_includesTo_excludesTo_responseTo_noResponseTo_conditionsFor_milestonesFor":"rel_includesTo_responseTo_conditionsFor_milestonesFor",
"rel_includesTo_excludesTo_responseTo_conditionsFor_milestonesFor":"rel_includesTo_responseTo_conditionsFor_milestonesFor",
"rel_includesTo_excludesTo_noResponseTo_conditionsFor_milestonesFor":"rel_includesTo_noResponseTo_conditionsFor_milestonesFor",
"rel_includesTo_responseTo_noResponseTo_conditionsFor_milestonesFor":"rel_includesTo_responseTo_conditionsFor_milestonesFor",
"rel_excludesTo_responseTo_noResponseTo_conditionsFor_milestonesFor":"rel_excludesTo_responseTo_conditionsFor_milestonesFor",
"rel_includesTo_excludesTo_responseTo_noResponseTo_conditionsFor":"rel_includesTo_responseTo_conditionsFor",
"rel_includesTo_excludesTo_responseTo_noResponseTo_milestonesFor":"rel_includesTo_responseTo_milestonesFor",
"rel_includesTo_excludesTo_responseTo_conditionsFor":"rel_includesTo_responseTo_conditionsFor",
"rel_includesTo_excludesTo_responseTo_milestonesFor":"rel_includesTo_responseTo_milestonesFor",
"rel_includesTo_excludesTo_noResponseTo_conditionsFor":"rel_includesTo_noResponseTo_conditionsFor",
"rel_includesTo_excludesTo_noResponseTo_milestonesFor":"rel_includesTo_noResponseTo_milestonesFor",
"rel_includesTo_excludesTo_conditionsFor_milestonesFor":"rel_includesTo_conditionsFor_milestonesFor",
"rel_includesTo_responseTo_noResponseTo_conditionsFor":"rel_includesTo_responseTo_conditionsFor",
"rel_includesTo_responseTo_noResponseTo_milestonesFor":"rel_includesTo_responseTo_milestonesFor",
"rel_excludesTo_responseTo_noResponseTo_conditionsFor":"rel_excludesTo_responseTo_conditionsFor",
"rel_excludesTo_responseTo_noResponseTo_milestonesFor":"rel_excludesTo_responseTo_milestonesFor",
"rel_responseTo_noResponseTo_conditionsFor_milestonesFor":"rel_responseTo_conditionsFor_milestonesFor",
"rel_includesTo_excludesTo_responseTo_noResponseTo":"rel_includesTo_responseTo",
"rel_includesTo_excludesTo_responseTo":"rel_includesTo_responseTo",
"rel_includesTo_excludesTo_noResponseTo":"rel_includesTo_noResponseTo",
"rel_includesTo_excludesTo_conditionsFor":"rel_includesTo_conditionsFor",
"rel_includesTo_excludesTo_milestonesFor":"rel_includesTo_milestonesFor",
"rel_includesTo_responseTo_noResponseTo":"rel_includesTo_responseTo",
"rel_excludesTo_responseTo_noResponseTo":"rel_excludesTo_responseTo",
"rel_responseTo_noResponseTo_conditionsFor":"rel_responseTo_conditionsFor",
"rel_responseTo_noResponseTo_milestonesFor":"rel_responseTo_milestonesFor",
"rel_includesTo_excludesTo":"rel_includesTo",
"rel_responseTo_noResponseTo":"rel_responseTo"
}

def table_to_latex(pd_table, all_i, pairwise_i):
    res = ''
    k = 0
    for i, (idx, row) in enumerate(pd_table.iterrows()):
        pin = num_to_sym_tex[int(row['In'])]
        pex = num_to_sym_tex[int(row['Ex'])]
        pre = num_to_sym_tex[int(row['Re_10'])] if 'Re_10' in row else ''
        prex = num_to_sym_tex[int(row['Rex_10'])] if 'Re_10' in row else ''
        pre_others = num_to_sym_tex[int(row['Re_5'])] if 'Re_5' in row else ''
        prex_others = num_to_sym_tex[int(row['Rex_5'])] if 'Rex_5' in row else ''
        if i in all_i:
            pre1, pre2, pre3 = pre_others, pre_others, pre_others
            prex1, prex2, prex3 = prex_others, prex_others, prex_others
            latex_row = f"& $t_{i + k}$ & {pin} & {pex} & {pre}  & {pre1}  & {pre2}  & {pre3} & {prex} & {prex1}  & {prex2} & {prex3} " + "\\\\ \cline{2-12} \n"
            res += latex_row
        elif i in pairwise_i:
            for k in [0, 1, 2]:
                if k == 0:
                    pre1, pre2, pre3 = pre_others, '', ''
                    prex1, prex2, prex3 = prex_others, '', ''
                elif k == 1:
                    middle = ''
                    if pre_others != '':
                        middle = '\ddots'
                    pre1, pre2, pre3 = '', middle, ''
                    middle = ''
                    if prex_others != '':
                        middle = '\ddots'
                    prex1, prex2, prex3 = '', middle, ''
                else:  # k == 2
                    pre1, pre2, pre3 = '', '', pre_others
                    prex1, prex2, prex3 = '', '', prex_others

                latex_row = f"& $t_{i + k}$ & {pin} & {pex} & {pre}  & {pre1}  & {pre2}  & {pre3} & {prex} & {prex1}  & {prex2} & {prex3} " + "\\\\ \cline{2-12} \n"
                res += latex_row
        else:
            pre1, pre2, pre3 = '', '', ''
            prex1, prex2, prex3 = '', '', ''
            latex_row = f"& $t_{i + k}$ & {pin} & {pex} & {pre}  & {pre1}  & {pre2}  & {pre3} & {prex} & {prex1}  & {prex2} & {prex3} " + "\\\\ \cline{2-12} \n"
            res += latex_row
    return res


rel_to_tex_sym = {
    'includesTo': '\includeRel',
    'excludesTo': '\excludeRel',
    'responseTo': '\\trespRel',
    'noResponseTo': '\\noresponseRel',
    'conditionsFor': '\\topcondRel',
    'milestonesFor': '\opmilestoneRel',
    'responseToexcludesTo': '\}\\trespRel,\excludeRel\}'
}


def rel_to_tex(k):
    rels = k.split('_')
    if rels[0] == 'rel':
        rels = rels[1:]
    tex = [rel_to_tex_sym[k] for k in rels]
    tex_list = '\{'
    for t in tex:
        tex_list += t + ','
    tex_list = tex_list[:-1] + '\}'
    return tex_list

def prepare_all_permutations():
    effect_relations = ['includesTo', 'excludesTo', 'responseTo', 'noResponseTo']
    constrain_relations = ['conditionsFor', 'milestonesFor']
    all_relations = effect_relations + constrain_relations
    e1 = 'A'
    e2 = 'B'
    dcrs_to_test = {}
    for i in range(1, 0, -1):
        for comb in combinations(all_relations, i):
            dcr = {
                'events': {'A','B'},
                'conditionsFor': {},
                'milestonesFor': {},
                'responseTo': {},
                'noResponseTo': {},
                'includesTo': {},
                'excludesTo': {},
                'marking': {'executed': set(),
                            'included': {'A','B'},
                            'pending': {},
                            'pendingDeadline': {'B':5},
                            },
                'conditionsForDelays': {},
                'responseToDeadlines': {},
            }
            for rel in comb:
                if not e1 in dcr[rel]:
                    dcr[rel][e1] = set()
                dcr[rel][e1].add(e2)
                if rel == 'responseTo':
                   dcr['responseToDeadlines'] = {'A':{'B':10}}
            key = f'rel_{repr(comb)}'
            key = key.replace("'", "").replace("(", "").replace(")", "").replace(",", "").replace(" ", "_")
            dcrs_to_test[key] = dcr
    return dcrs_to_test

def table_to_latex_general(pd_table, k, dcr, delay_dict):
    multicolumn_dict = {}
    for a in pd_table.columns:
        if a[0] not in multicolumn_dict:
            multicolumn_dict[a[0]] = []
        multicolumn_dict[a[0]].append(a[1])

    prev_row = None
    prev_count = None
    idx_line = {}
    multi_row = {}
    row_len = 0
    for i, (idx, row) in enumerate(pd_table.iterrows()):
        if prev_row and prev_row != idx[0]:
            idx_line[i] = idx[0]
            multi_row[prev_row] = prev_count
            row_len = len(row)
        prev_row = idx[0]
        prev_count = idx[1]
        if i == len(pd_table) - 1:
            multi_row[idx[0]] = idx[1]
    res = '\\begin{tabular}{cr' + ''.join('|c' for x in range(row_len)) + '}\n'
    delay = ''
    e = ''
    e_prime = ''
    if not isinstance(k, str):
        rel = rel_to_tex_sym[k[0]]
        e = k[1][0]
        e_prime = k[1][1]
        delay = '[' + str(delay_dict[frozenset({e, e_prime})]) + ']' if frozenset({e, e_prime}) in delay_dict else ''
        deadline = '[' + str(dcr['responseToDeadlines'][e][e_prime]) + ']' if e in dcr['responseToDeadlines'] and e_prime in dcr['responseToDeadlines'][e] else ''
        key = f'{e} {rel}{delay}{deadline} {e_prime}'
    elif k == 'events':
        key = ', '.join(e for e in dcr['events'])
    else:
        key = k
    multicolumns = ''
    places = '& & '
    for i, (a, b) in enumerate(multicolumn_dict.items()):
        a = a.replace('_','\\_')
        if a == e_prime:
            a = '\\textbf{' + a + '}'
        multicolumns += '\multicolumn{' + str(len(b)) + '}{c' + ('|' if i != len(multicolumn_dict) - 1 else '') + '}{' + a + '} & '
        for bb in b:
            if '_' in bb:
                bb = bb.split('_')[0] + '(' + bb.split('_')[1] + ')'
            places += f' {bb} &'
    places = places[:-1] + "\\\\ \cline{2-" + str(row_len + 2) + "} \n"
    res += f'$ {key} $ & & ' + multicolumns[:-3] + ' \\\\ \n'
    res += places
    for i, (idx, row) in enumerate(pd_table.iterrows()):
        rstr = ''
        if i + 1 in idx_line:
            row_end = " \hline \n"
        else:
            linelen = f'2-{row_len + 2}'
            row_end = " \cline{" + linelen + "} \n"
        for item in row:
            appd = delay if int(item) == 8 else ''
            rstr += f'{num_to_sym_tex[int(item)]}{appd} & '
        row_start = ''
        if i in idx_line:
            tmp = '\\textbf{' + idx_line[i] + '}' if idx_line[i] == e else idx_line[i]
            tmp = tmp.replace('_','\\_')
            row_start = '\multirow{' + str(multi_row[idx_line[i]]) + '}{*}{' + tmp + '}'
        elif i == 0:
            tmp = '\\textbf{' + idx[0] + '}' if idx[0] == e else idx[0]
            tmp = tmp.replace('_','\\_')
            row_start = '\multirow{' + str(multi_row[idx[0]]) + '}{*}{' + tmp + '}'
        latex_row = f"{row_start} & $t_{{{idx[1]}}}$ & " + rstr[:-2] + "\\\\" + (row_end if i != len(pd_table) - 1 else "\n")
        res += latex_row
    res += '\\end{tabular}'
    return res

def table_to_latex_matrix(pd_table, k, dcr, delay_dict):
    multicolumn_dict = {}
    for a in pd_table.columns:
        if a[0] not in multicolumn_dict:
            multicolumn_dict[a[0]] = []
        multicolumn_dict[a[0]].append(a[1])

    prev_row = None
    prev_count = None
    idx_line = {}
    multi_row = {}
    row_len = 0
    for i, (idx, row) in enumerate(pd_table.iterrows()):
        if prev_row and prev_row != idx[0]:
            idx_line[i] = idx[0]
            multi_row[prev_row] = prev_count
            row_len = len(row)
        prev_row = idx[0]
        prev_count = idx[1]
        if i == len(pd_table) - 1:
            multi_row[idx[0]] = idx[1]
    res = '\\begin{tabular}{cr' + ''.join('|c' for x in range(row_len)) + '}\n'
    delay = ''
    e = ''
    e_prime = ''
    if not isinstance(k, str):
        rel = rel_to_tex_sym[k[0]]
        e = k[1][0]
        e_prime = k[1][1]
        delay = '[' + str(delay_dict[frozenset({e, e_prime})]) + ']' if frozenset({e, e_prime}) in delay_dict else ''
        deadline = '[' + str(dcr['responseToDeadlines'][e][e_prime]) + ']' if e in dcr['responseToDeadlines'] and e_prime in dcr['responseToDeadlines'][e] else ''
        key = f'{e} {rel}{delay}{deadline} {e_prime}'
    elif k == 'events':
        key = ', '.join(e for e in dcr['events'])
    else:
        key = k
    multicolumns = ''
    places = '& & '
    for i, (a, b) in enumerate(multicolumn_dict.items()):
        a = a.replace('_','\\_')
        if a == e_prime:
            a = '\\textbf{' + a + '}'
        multicolumns += '\multicolumn{' + str(len(b)) + '}{c' + ('|' if i != len(multicolumn_dict) - 1 else '') + '}{' + a + '} & '
        for bb in b:
            if '_' in bb:
                bb = bb.split('_')[0] + '(' + bb.split('_')[1] + ')'
            places += f' {bb} &'
    places = places[:-1] + "\\\\ \cline{2-" + str(row_len + 2) + "} \n"
    res += f'$ {key} $ & & ' + multicolumns[:-3] + ' \\\\ \n'
    res += places
    for i, (idx, row) in enumerate(pd_table.iterrows()):
        rstr = ''
        if i + 1 in idx_line:
            row_end = " \hline \n"
        else:
            linelen = f'2-{row_len + 2}'
            row_end = " \cline{" + linelen + "} \n"
        for item in row:
            appd = delay if int(item) == 8 else ''
            if int(item) == 0:
                rstr += f'$0$ & '
            else:
                rstr += f'${num_to_sym_tex[int(item)][:-2]}{appd}$ & '
        row_start = ''
        if i in idx_line:
            tmp = '\\textbf{' + idx_line[i] + '}' if idx_line[i] == e else idx_line[i]
            tmp = tmp.replace('_','\\_')
            row_start = '\multirow{' + str(multi_row[idx_line[i]]) + '}{*}{' + tmp + '}'
        elif i == 0:
            tmp = '\\textbf{' + idx[0] + '}' if idx[0] == e else idx[0]
            tmp = tmp.replace('_','\\_')
            row_start = '\multirow{' + str(multi_row[idx[0]]) + '}{*}{' + tmp + '}'
        latex_row = rstr[:-2] + "\\\\ \n"
        res += latex_row
    res += '\\end{tabular}'
    return res