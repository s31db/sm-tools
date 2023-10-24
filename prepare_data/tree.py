from typing import Tuple


def father(
    node: dict, lvl: int
) -> Tuple[str | None, str | None, str | None, str | None]:
    sup = "super" + (".super" * (lvl - 1))
    if sup in node:
        return (
            node[sup],
            node[sup + ".status"],
            node[sup + ".name"] if sup + ".name" in node else None,
            node[sup + ".type"] if sup + ".type" in node else None,
        )
    return None, None, None, None


def build_tree(datas: dict) -> Tuple[dict, dict]:
    ids = {}
    for story, values in datas.items():
        ids[story] = {
            "lvl": 0,
            "status": values["status"],
            "estimate": values["estimate"] if "estimate" in values else 1,
            "aggregatetimeoriginalestimate": values["aggregatetimeoriginalestimate"]
            if "aggregatetimeoriginalestimate" in values
            else 0,
            "aggregatetimeestimate": values["aggregatetimeestimate"]
            if "aggregatetimeestimate" in values
            else 0,
            "aggregatetimespent": values["aggregatetimespent"]
            if "aggregatetimespent" in values
            else 0,
            "name": values["name"] if "name" in values else None,
            "type": values["type"] if "type" in values else None,
            "done": 0
            if values["status"] != "Done"
            else values["estimate"]
            if "estimate" in values
            else 1,
        }
        child_key = story
        for i in range(1, 10):
            f, s, n, typ = father(values, i)
            if f:
                ids[child_key]["father"] = f
                ids[child_key]["father.name"] = n
                estimate = ids[child_key]["estimate"]
                if estimate is None:
                    estimate = 1
                ti = {}
                for tim in [
                    "aggregatetimeoriginalestimate",
                    "aggregatetimeestimate",
                    "aggregatetimespent",
                ]:
                    ti[tim] = 0 if ids[child_key][tim] is None else ids[child_key][tim]
                if f in ids:
                    ids[f]["children"][child_key] = ids[child_key]
                    ids[f]["estimate"] += estimate
                    for t in [
                        "aggregatetimeoriginalestimate",
                        "aggregatetimeestimate",
                        "aggregatetimespent",
                    ]:
                        ids[f][t] += ti[t]
                    if ids[f]["done"] is None:
                        ids[f]["done"] = 0
                    if ids[child_key]["done"] is not None:
                        ids[f]["done"] += ids[child_key]["done"]
                    if i > ids[f]["lvl"]:
                        ids[f]["lvl"] = i
                else:
                    ids[f] = {
                        "lvl": i,
                        "children": {child_key: ids[child_key]},
                        "estimate": estimate,
                        "done": ids[child_key]["done"],
                        "status": s,
                        "name": n,
                        "type": typ,
                    }
                    for tim in [
                        "aggregatetimeoriginalestimate",
                        "aggregatetimeestimate",
                        "aggregatetimespent",
                    ]:
                        ids[f][tim] = ti[tim]
                child_key = f
            else:
                break
    tree = {}
    for key, values in ids.items():
        if "father" not in values:
            tree[key] = values
    return tree, ids


def test_tree() -> Tuple[dict, dict]:
    example = {
        "us1": {
            "super": "fe1",
            "estimate": 2,
            "status": "To Do",
            "super.status": "In Progress",
        },
        "us2": {
            "super": "fe1",
            "estimate": 4,
            "status": "Done",
            "super.status": "In Progress",
        },
        "us3": {
            "super": "fe2",
            "super.super": "fe1",
            "estimate": 3,
            "status": "Done",
            "super.status": "Done",
            "super.super.status": "In Progress",
        },
        "us4": {
            "super": "fe1",
            "estimate": 1,
            "status": "Done",
            "super.status": "In Progress",
        },
        "us5": {
            "super": "fe1",
            "estimate": 0,
            "status": "Not Done",
            "super.status": "In Progress",
        },
    }
    tree, ids = build_tree(example)
    assert ids["fe1"]["done"] == 8
    assert ids["fe1"]["estimate"] == 10
    assert len(tree) == 1
    assert tree["fe1"]["lvl"] == 2
    assert tree["fe1"]["status"] == "In Progress"
    assert ids["fe2"]["status"] == "Done"
    return tree, ids
