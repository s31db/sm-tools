import json
from sm import jiraconf


def presence(datas_sm: dict) -> dict:
    pres = {}
    for v in datas_sm['Presence'].values():
        for member in v['member']:
            if member in pres:
                for j in v['jours']:
                    if j not in pres[member]:
                        pres[member].append(j)
            else:
                pres[member] = [a for a in v['jours']]
    return pres


def jours_presence(pres: dict) -> None:
    js = {"lundi": [], "mardi": [], "mercredi": [], "jeudi": [], "vendredi": []}
    for j in ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]:
        for m, jours in pres.items():
            if j in jours:
                js[j].append(m)
        print(j, len(js[j]), ', '.join(js[j]))


def no_link(pres: dict) -> None:
    inc = []
    for m, jo in pres.items():
        for mm, jj in pres.items():
            lien = False
            for j in jo:
                if j in jj:
                    lien = True
            if not lien:
                if [m, mm] not in inc:
                    print('Pas lien', m, mm)
                    inc.append([m, mm])
                    inc.append([mm, m])


def flexoffice() -> None:
    c = jiraconf()
    with open(c['Common']['path_data'] + 'teams.json', 'r', encoding='utf-8') as fp:
        datas_sm = json.load(fp)
    pres = presence(datas_sm)
    jours_presence(pres)
    no_link(pres)


if __name__ == '__main__':
    flexoffice()

# {
# 	"Presence": {
# 		"T1": {"jours": ["jeudi", "vendredi"], "member": ["S@M", "Mike", "Branda", "Tom", "Sylvestre"]},
#

