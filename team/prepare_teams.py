from helpers.prepare_date_sprint import sprint_dates
import json


def dates():
    # a = [*sprint_dates("2025-01-02", 3)]
    # b = {}
    # for i in a:
    #     b[i] = 1
    # print(b)
    a = {i: 1 for i in sprint_dates("2025-01-02", 3)}
    print(a)


def build_mail(teams=("teamA", "teamB", "teamC"), roles=("DevOPS", "Dev", "PO")):
    with open("teams.json", "r", encoding="utf-8") as fp:
        data = json.load(fp)

    mails = []
    for team in teams:
        for person, values in data[team].items():
            if values["Role"] in roles:
                if "mail" in values:
                    mails.append(values["mail"])
                else:
                    mails.append(person.lower().replace(" ", ".") + data["mail"])
    return mails


if __name__ == "__main__":
    print(";".join(build_mail()))
#     Exemple

#     {
#   "mail": "@toto.com",
#   "TeamA": {
#     "po": {
#       "Absence": {
#         "2025-01-02": 1,
#         "2025-01-03": 1
#       },
#       "Role": "PO",
#       "mail": "po@toto.com"
#     },
#     "dev1": {
#       "Absence": {
#         "2025-02-11": 1,
#         "2025-02-25": 1,
#       },
#       "Role": "DevOps"
#     },
#     "dev2": {
#       "Absence": {},
#       "Role": "Dev"
#     },
#     "sm": {
#       "Absence": {},
#       "Role": "SM"
#     }
#   },
