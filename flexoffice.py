import json
from sm import jiraconf


if __name__ == '__main__':
    c = jiraconf()
    with open(c['projects']['Common']['path_data'] + 'teams.json', 'r', encoding='utf-8') as fp:
        datas_sm = json.load(fp)
    p = {}
    for v in datas_sm['Presence'].values():
        for member in v['member']:
            if member in p:
                for j in v['jours']:
                    if j not in p[member]:
                        p[member].append(j)
            else:
                p[member] = [a for a in v['jours']]
    # print(p)
    js = {"lundi": [], "mardi": [], "mercredi": [], "jeudi": [], "vendredi": []}
    for j in ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]:
        # print(j, end=' : ')
        for m, jours in p.items():
            if j in jours:
                js[j].append(m)
        # print(', '.join(js[j]), len(js[j]))
        print(j, len(js[j]), ', '.join(js[j]))

    inc = []
    for m, jo in p.items():
        for mm, jj in p.items():
            lien = False
            for j in jo:
                if j in jj:
                    lien = True
            if not lien:
                if [m, mm] not in inc:
                    print('Pas lien', m, mm)
                    inc.append([m, mm])
                    inc.append([mm, m])

# {
# 	"Presence": {
# 		"T1": {"jours": ["jeudi", "vendredi"], "member": ["S@M", "Mike", "Branda", "Tom", "Sylvestre"]},
#

