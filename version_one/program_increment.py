from v1pysdk import V1Meta
from version_one.versionone import feature, iteration
import json
from datetime import datetime


def stories_pi(
    conf,
    its: iter,
    fields,
    asof: str | None = None,
    append_filters: str = "",
    title: str = "",
) -> iter:
    features = {}
    with V1Meta(
        address=conf["url_server"],
        instance=conf["instance"],
        password=conf["token"],
        use_password_as_token=True,
    ) as v1:
        for it in its:
            present = False
            name_extract = f"{it}_{title}_{asof if asof else ''}"
            with open(conf["path_data"] + "date_export_pi.txt", "r") as date_export:
                lines = date_export.readlines()
            for line in lines:
                line = line.replace("\n", "")
                if asof and line.split(":")[0] == name_extract and line[-19:-9] >= asof:
                    present = True
                    break
            if present:
                with open(
                    f"{conf['path_data']}result_pi_{name_extract}.json",
                    "r",
                    encoding="utf-8",
                ) as fp:
                    ite = json.load(fp)
            else:
                ite = iteration(
                    conf=conf,
                    timebox=it,
                    json=True,
                    ver1=v1,
                    link=False,
                    append_filters=append_filters,
                    fields=fields,
                    asof=asof,
                )
                if asof:
                    with open(
                        f"{conf['path_data']}result_pi_{name_extract}.json",
                        "w",
                        encoding="utf-8",
                    ) as fp:
                        json.dump(ite, fp)
                with open(conf["path_data"] + "date_export_pi.txt", "a") as date_export:
                    date_export.write(
                        f"{name_extract}: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )
        if ite:
            for us in ite.values():
                if us["Super.Number"] in features:
                    features[us["Super.Number"]]["story"][us["Number"]] = us
                else:
                    features[us["Super.Number"]] = {
                        "Name": us["Super.Name"],
                        "story": {us["Number"]: us},
                    }
    return features
