from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from HtmlClipboard import put_html
from sm import jiraconf, jira_cum, jira_treemap, extract_jira, analysis_tree
from html import escape, unescape


hostname = 'localhost'
serverPort = 8000


class MyServer(BaseHTTPRequestHandler):

    tampon: str = ''

    def do_GET(self):
        self.send_response(200)
        if self.path in ('/favicon.ico', ):
            return
        print(self.path)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.w('<!DOCTYPE html/>')
        self.w('<meta charset="UTF-8">')
        self.w('<html><head><title>S@M Tools</title></head>')
        self.w('<body>')
        if self.path == '/':
            self.index()
        self.w('</body></html>')

    def w(self, arg: str, append: bool = False):
        if append:
            self.tampon += arg
        self.wfile.write(bytes(arg, 'utf-8'))

    def index(self):
        actions = {'Extract': None, 'Burndown': None, 'Cumulative': None, 'Treemap': None, 'TreemapEpic': None}
        self.w('<form method="post" action="/action"><br/>')
        self.w('<fieldset><legend>Project</legend>')
        dataconf = jiraconf()
        for key, conf in dataconf['projects'].items():
            self.w('<input name="projects" type="checkbox" value="'+key+'">'+key+'</input><br/>')
            self.w("<label for='" + key + "_filter'>Filtre : </label>")
            self.w("<input name='" + key + "_filter' id='" + key + "_filter' type='text' value='" +
                   escape(conf['filter']) + "' size='200'/><br/>")
            self.w("<label for='" + key + "_step'>Step : </label>")
            self.w("<input name='" + key + "_step' id='" + key + "_step' type='text' value='" +
                   '0' + "' size='200'/><br/>")
            self.w('<fieldset><legend>Action</legend>')
            for key_action in actions.keys():
                self.w('<input name="'+key+'_actions" type="checkbox" value="'+key_action+'">' + key_action +
                       '</input><br/>')
            self.w('</fieldset><br/>')
        self.w('</fieldset><br/>')
        self.w('<input id="reset" type="reset"/><input id="submit" type="submit"/>')
        self.w('</form><br/>')

    def parse_post(self):
        content_len = int(self.headers.get('Content-Length'), 0)
        post_body = self.rfile.read(content_len)
        req = parse_qs(post_body, keep_blank_values=1, encoding='utf-8')
        return req

    def do_POST(self):
        print(self.path)
        req = self.parse_post()
        print(req)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.w('<!DOCTYPE html/>')
        self.w('<meta charset="UTF-8">')
        self.w('<html><head><title>S@m Tools</title></head>')
        self.w('<body>')

        sfx = None
        dataconf = jiraconf()['projects']
        if b'projects' in req:
            for project in req[b'projects']:
                actions = project + b'_actions'
                filtre = project + b'_filter'
                step = project + b'_step'
                project = project.decode('utf-8')
                filtre = unescape(req[filtre][0].decode('utf-8'))
                step = int(req[step][0].decode('utf-8'))
                self.w('<details open><summary>' + project + '</summary>')
                if actions in req:
                    for action in req[actions]:
                        if action == b'Extract':
                            self.w(filtre + '<br/>')
                            extract_jira(project=project, start_date=dataconf[project]['start'], filtre=filtre)
                        elif action == b'Cumulative':
                            j = jira_cum(project=project, details=True, date_file=sfx,
                                         weeks=dataconf[project]['weeks'], start_date=dataconf[project]['start'],
                                         step=step,
                                         chart_html=True)
                            self.w(j + '<br/>', append=True)
                        elif action == b'Treemap':
                            j = jira_treemap(title=project, project=project, date_file=sfx, html=True, chart_html=True)
                            self.w(j.split('<body>')[-1].split('</body>')[0] + '<br/>')
                        elif action == b'TreemapEpic':
                            for n, t, a in analysis_tree(project):
                                self.w('<details><summary>' + n + str(a) + '</summary>')
                                self.w('' + t.split('<body>')[-1].split('</body>')[0] + '</details><br/>')
                self.w('</details><br/>')
        if self.path == '/':
            self.index()
        self.w('</body></html>')
        put_html(self.tampon)


if __name__ == '__main__':
    webServer = HTTPServer((hostname, serverPort), MyServer)
    print('Explore htt', 'p://', hostname, ':', serverPort, sep='')
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
