import json
from helpers.prepare_date_sprint import sprint_dates


def presence(team, start_date, weeks, exclude_dates=None):
    with open("teams.json", "r", encoding="utf-8") as fp:
        data = json.load(fp)
    # sd = {i: 0 for i in sprint_dates(start_date, weeks)}
    sd = [
        i
        for i in sprint_dates(start_date, weeks)
        if not (exclude_dates and i in exclude_dates)
    ]
    print(sd)
    # if exclude_dates:
    #     for exclude_date in exclude_dates:
    #         sd.pop(exclude_date)
    nb = 0
    total = 0
    for member in data[team].values():
        if member["Role"] in ("TL", "Dev"):
            nb += len(sd)
            total += len(sd)
            for s in sd:
                if s in member["Absence"]:
                    nb -= member["Absence"][s]
                # else:
                # sum += 1
                # total += 1
    print(nb, total, 100 * nb / total)


if __name__ == "__main__":
    presence("Team", "2025-04-01", 3)
