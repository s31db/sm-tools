from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
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


hostname = "localhost"
serverPort = 8000


class MyServer(BaseHTTPRequestHandler):
    tampon: str = ""

    def do_GET(self) -> None:
        self.send_response(200)

        if self.path.startswith("/treemap"):
            sfx = None
            self.send_header("Content-type", "text/html")
            self.end_headers()
            j = jira_treemap(
                project=self.path.split("project=")[1], date_file=sfx, html=False
            ).chart_html()
            self.w(j)
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
                f'<input name="projects" type="checkbox" value="{key}">{key}</input>'
            )
            self.w(f"<label for='{key}_filter'>Filtre : </label>")
            self.wl(
                f"<input name='{key}_filter' id='{key}_filter' "
                f"type='text' value='{escape(conf['filter'])}' size='200'/>"
            )
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
        sfx = None
        if b"projects" in req:
            for b_project in req[b"projects"]:
                actions = b_project + b"_actions"
                b_filtre = b_project + b"_filter"
                b_start = b_project + b"_start"
                b_end = b_project + b"_end"
                b_now = b_project + b"_now"
                b_weeks = b_project + b"_weeks"
                b_step = b_project + b"_step"

                project = b_project.decode("utf-8")
                filtre = unescape(req[b_filtre][0].decode("utf-8"))
                start = unescape(req[b_start][0].decode("utf-8"))
                end = unescape(req[b_end][0].decode("utf-8"))
                now = b_now in req
                weeks = int(req[b_weeks][0].decode("utf-8"))
                step = int(req[b_step][0].decode("utf-8"))

                self.w("<details open><summary>" + project + "</summary>")
                self.w(
                    '<a href="/treemap?project='
                    + project
                    + '" download="'
                    + project
                    + '_treemap.html">'
                )
                self.wl("Treemap file</a>")
                if actions in req:
                    for action in req[actions]:
                        if action == b"Extract":
                            self.wl(filtre)
                            extract_jira(
                                project=project, start_date=start, filtre=filtre
                            )
                        elif action == b"Cumulative":
                            j = jira_cum(
                                project=project,
                                details=True,
                                date_file=sfx,
                                weeks=weeks,
                                start_date=start,
                                step=step,
                                chart_html=True,
                                now=now,
                            )
                            self.wl(j, append=True)
                        elif action == b"Treemap":
                            j = jira_treemap(project=project, date_file=sfx, html=False)
                            self.wl(
                                j.chart_html().split("<body>")[-1].split("</body>")[0]
                            )
                        elif action == b"TreemapEpic":
                            for n, t, a in analysis_tree(project):
                                self.w("<details><summary>" + n + str(a) + "</summary>")
                                self.wl(
                                    ""
                                    + t.split("<body>")[-1].split("</body>")[0]
                                    + "</details>"
                                )
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
