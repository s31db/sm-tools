from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, quote, unquote
from HtmlClipboard import put_html
from sm import (
    jiraconf,
    jira_cum,
    jira_treemap,
    extract_jira,
    analysis_tree,
    time_nb,
    burndown,
    worklog_plan_html,
)
from html import escape, unescape
from version_one.sprint import read as read_sprint
from version_one.tree_version_one import treemap_pi_portfolio
from datetime import datetime

hostname = "localhost"
serverPort = 8000


class MyServer(BaseHTTPRequestHandler):
    tampon: str = ""

    def do_GET(self) -> None:
        self.send_response(200)

        if self.path.startswith("/treemap"):
            self.send_header("Content-type", "text/html")
            self.end_headers()
            project = self.path.split("project=")[1].split("&")[0]
            asof = (
                self.path.split("asof=")[1].split("&")[0]
                if "asof=" in self.path
                else None
            )
            conf = jiraconf()["projects"][project]
            if "type" in conf and conf["type"] == "version_one":
                append_filters = [self.path.split("filter=")[1]]
                if asof:
                    title = f"{project} Treemap {' or '.join(append_filters)} {asof}"
                else:
                    title = f"{project} Treemap {' or '.join(append_filters)} {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}"
                j = treemap_pi_portfolio(
                    conf=conf,
                    title=title,
                    append_filters=append_filters,
                    asof=asof,
                    sav=False,
                    img=False,
                    show=False,
                )[0]
            else:
                j = jira_treemap(
                    project=self.path.split("project=")[1], date_file=asof, html=False
                )
            self.w(j.chart_html())
        else:
            print(self.path)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.w("<!DOCTYPE html/>")
            self.w('<meta charset="UTF-8">')
            self.w("<html><head><title>S@M Tools</title>")
            self.fav_icon()
            self.w("</head>")
            # <a target="_blank" href="https://icons8.com/icon/i2wM0iCYXY7G/scrum">Scrum</a>
            # icon by <a target="_blank" href="https://icons8.com">Icons8</a>
            self.w("<body>")
            if self.path == "/":
                self.index()
            self.w("</body></html>")

    def fav_icon(self):
        self.w('<link rel="icon" type="image/png" href="')
        self.w("https://img.icons8.com/external-flaticons-flat-flat-icons/64")
        self.w('/000000/external-scrum-agile-flaticons-flat-flat-icons-8.png" />')

    def w(self, arg: str, append: bool = False):
        if append:
            self.tampon += arg
        self.wfile.write(bytes(arg, "utf-8"))

    def wl(self, arg: str, append: bool = False):
        self.w(arg + "<br/>", append=append)

    def index(self) -> None:
        actions = {
            "Extract": None,
            "Burndown": None,
            "Burndown_previous": None,
            "Cumulative": None,
            "Treemap": None,
            "TreemapEpic": None,
            "time_nb": None,
        }
        self.wl('<form method="post" action="/action">')
        self.w("<fieldset><legend>Project</legend>")
        dataconf = jiraconf()
        for key, conf in dataconf["projects"].items():  # type: ignore
            self.wl(
                f'<input name="projects" type="checkbox" value="{key}">{key} - {escape(conf["name"])}</input>'
            )
            self.w(f"<label for='{key}_filter'>Filtre : </label>")
            self.wl(
                f"<input name='{key}_filter' id='{key}_filter' "
                f"type='text' value='{escape(conf['filter'])}' size='200'/>"
            )
            self.w(f"<label for='{key}_asof'>Asof : </label>")
            self.w(f"<input type='date' name='{key}_asof' id='{key}_asof'/>")

            self.w(f"<label for='{key}_start'>From : </label>")
            self.w(
                f"<input name='{key}_start' id='{key}_start' type='text' "
                f"value='{escape(conf['start'])}' size='10'/>"
            )
            self.w(f" <label for='{key}_start'>To : </label>")
            date_end = escape(conf["end"]) if "end" in conf else ""
            self.w(
                f"<input name='{key}_end' id='{key}_end' type='text' value='{date_end}' size='10'/>"
            )
            self.w(f" <label for='{key}_weeks'>Weeks : </label>")
            self.w(
                f"<input name='{key}_weeks' id='{key}_weeks' type='text' value='"
                + str(conf["weeks"])
                + "' size='2'/>"
            )
            self.w(f" <label for='{key}_step'>Step : </label>")
            self.w(
                f"<input name='{key}_step' id='{key}_step' type='text' value='"
                + "0"
                + "' size='2'/>"
            )
            self.w(f" <label for='{key}_now'>Now : </label>")
            self.w(
                f"<input type='checkbox' name='{key}_now' id='{key}_now' type='text' value='True' checked/>"
            )
            self.w("<fieldset><legend>Action</legend>")
            if "actions" in conf:
                for key_action in conf["actions"]:
                    self.wl(
                        f'<input name="{key}_actions" type="checkbox" value="{key_action}">{key_action}</input>'
                    )
            else:
                for key_action in actions.keys():
                    self.wl(
                        f'<input name="{key}_actions" type="checkbox" value="{key_action}">{key_action}</input>'
                    )
            self.wl("</fieldset>")
        self.wl("</fieldset>")
        self.w(
            '<div style="position: fixed; left:50%;top:5px; background-color: rgb(255 255 255 / 0.8);">'
        )
        self.w("<fieldset><legend>Action</legend>")
        self.w(
            '<input id="reset" type="reset" style="background-color: black; color: white;"/> '
        )
        self.w(
            '<input id="submit" type="submit" style="background-color: green; color: white;"/></fieldset></div>'
        )
        self.wl("</form>")

    def parse_post(self) -> dict[bytes, list[bytes]]:
        content_len: int = int(self.headers.get("Content-Length"), 0)  # type: ignore
        post_body = self.rfile.read(content_len)
        req = parse_qs(post_body, keep_blank_values=True, encoding="utf-8")
        return req

    def do_POST(self) -> None:
        if self.path in ("/favicon.ico",):
            return
        # print(self.path)
        if self.path == "/action":
            self.post_action()

    def post_action(self) -> None:
        req = self.parse_post()
        # print(req)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.w("<!DOCTYPE html>")
        self.w('<meta charset="UTF-8">')
        self.w("<html><head><title>S@m Tools</title>")
        self.fav_icon()

        self.w("<script>")
        self.w("document.addEventListener('DOMContentLoaded', () => {")
        self.w(
            "document.querySelectorAll('.cp').forEach((btn)=>{btn.addEventListener('click',()=>{const bnId= btn.id;"
        )
        self.w(
            "const e=document.getElementById('div_'+bnId), r=document.createRange(); r.selectNode(e);"
        )
        self.w("const t=window.getSelection(); t.removeAllRanges(), t.addRange(r), ")
        self.w("document.execCommand('copy'), t.removeAllRanges();")
        self.w(
            "const message= document.getElementById('message'); message.style.display= 'block'; setTimeout(() => {"
        )
        self.w("message.style.display = 'none';}, 1500);")
        self.w("});});});")
        self.w("</script>")

        self.w("</head>")
        self.w("<body>")
        self.w(
            '<div id="message" style="display: none; position: fixed; top: 0; left: 50%; '
        )
        self.w("transform: translateX(-50%); ")
        self.w(
            'background-color: #92ecc3; color: #03a9f4; padding: 8px; text-align: center;">'
        )
        self.w("La copie dans le presse-papiers est faite !")
        self.w("</div>")
        dataconf = jiraconf()
        projects = dataconf["projects"]
        if b"projects" in req:
            for b_project in req[b"projects"]:
                actions = b_project + b"_actions"
                b_filtre = b_project + b"_filter"
                b_start = b_project + b"_start"
                b_end = b_project + b"_end"
                b_now = b_project + b"_now"
                b_weeks = b_project + b"_weeks"
                b_step = b_project + b"_step"
                b_asof = b_project + b"_asof"

                project = b_project.decode("utf-8")
                filtre = unescape(req[b_filtre][0].decode("utf-8"))
                start = unescape(req[b_start][0].decode("utf-8"))
                end = unescape(req[b_end][0].decode("utf-8"))
                now = b_now in req
                weeks = int(req[b_weeks][0].decode("utf-8"))
                step = int(req[b_step][0].decode("utf-8"))
                conf = projects[project]
                if req[b_asof][0] == b"":
                    asof = None
                else:
                    asof = unescape(req[b_asof][0].decode("utf-8"))

                self.w(
                    f"<details open><summary>{project} - {escape(conf['name'])}</summary>"
                )
                if "type" in conf and conf["type"] == "version_one":
                    self.w(
                        f'<a href="https://{conf["url_server"]}/{conf["instance"]}/TeamRoom.mvc/Show/{conf["teamRoom"]}">Team Room</a>'
                    )
                    link_treemap = f"/treemap?project={project}"
                    if asof:
                        link_treemap += f"&asof={asof}"
                    link_treemap += f"&filter={quote(filtre)}"
                    self.w(f'<a href="{link_treemap}"')
                else:
                    self.w(f'<a href="/treemap?project={project}"')
                self.wl(f' download="{project}_treemap.html">Treemap file</a>')
                if actions in req:
                    for action in req[actions]:
                        if action == b"Extract":
                            self.wl(filtre)
                            if "type" in conf and conf["type"] == "version_one":
                                read_sprint(
                                    extr=True,
                                    table=False,
                                    graph=False,
                                    append_filters=[filtre],
                                    conf=conf,
                                    timebox=conf["timebox"]["name"],
                                    asof=asof,
                                    start_date=start,
                                    end_date=end,
                                    weeks=weeks,
                                    now=now,
                                )
                            else:
                                extract_jira(
                                    project=project,
                                    start_date=start,
                                    filtre=filtre,
                                    asof=asof,
                                )
                        elif action == b"Cumulative":
                            if "type" in conf and conf["type"] == "version_one":
                                j = read_sprint(
                                    extr=False,
                                    table=False,
                                    graph=True,
                                    append_filters=[filtre],
                                    conf=conf,
                                    timebox=conf["timebox"]["name"],
                                    asof=asof,
                                    start_date=start,
                                    end_date=end,
                                    weeks=weeks,
                                    now=now,
                                )
                            else:
                                j = jira_cum(
                                    project=project,
                                    details=True,
                                    date_file=asof,
                                    weeks=weeks,
                                    start_date=start,
                                    step=step,
                                    chart_html=True,
                                    now=now,
                                )
                            self.wl(j, append=True)
                        elif action == b"Treemap":
                            if "type" in conf and conf["type"] == "version_one":
                                j = treemap_pi_portfolio(
                                    conf=conf,
                                    title=project + " Treemap",
                                    sav=False,
                                    img=False,
                                    show=False,
                                    asof=asof,
                                    append_filters=[filtre],
                                )[0]
                            else:
                                j = jira_treemap(
                                    project=project, date_file=asof, html=False
                                )
                            self.wl(
                                # j.chart_html().split("<body>")[-1].split("</body>")[0]
                                j.chart_html(full_html=False)
                            )
                        elif action == b"TreemapEpic":
                            for n, t, a in analysis_tree(project):
                                self.w("<details><summary>" + n + str(a) + "</summary>")
                                self.wl(
                                    ""
                                    + t.split("<body>")[-1].split("</body>")[0]
                                    + "</details>"
                                )
                        elif action == b"Suivi":
                            j = read_sprint(
                                extr=False,
                                table=True,
                                graph=False,
                                append_filters=[filtre],
                                conf=conf,
                                timebox=conf["timebox"]["name"],
                                asof=asof,
                                start_date=start,
                                end_date=end,
                                weeks=weeks,
                                now=now,
                            )
                            self.wl(j, append=True)
                        elif action == b"time_nb":
                            self.wl(time_nb(project))
                        elif action == b"Burndown":
                            self.wl(burndown(project, suffix="sprint"))
                        elif action == b"Burndown_previous":
                            self.wl(
                                burndown(
                                    project, suffix="sprint_previous", previous=True
                                )
                            )
                        elif action == b"Worklog":
                            for line in worklog_plan_html(
                                project=project,
                                start_date=start,
                                date_to=end,
                                limit_today=now,
                            ):
                                self.w(line)
                self.wl("</details>")
        if self.path == "/":
            self.index()
        self.w("</body></html>")
        put_html(self.tampon)


if __name__ == "__main__":
    webServer = HTTPServer((hostname, serverPort), MyServer)
    print("Explore htt", "p://", hostname, ":", serverPort, sep="")
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
