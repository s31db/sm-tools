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

    def wl(self, arg: str, append: bool = False):
        self.w(arg + '<br/>', append=append)

    def index(self):
        actions = {'Extract': None, 'Burndown': None, 'Cumulative': None, 'Treemap': None, 'TreemapEpic': None}
        self.wl('<form method="post" action="/action">')
        self.w('<fieldset><legend>Project</legend>')
        dataconf = jiraconf()
        for key, conf in dataconf['projects'].items():
            self.wl('<input name="projects" type="checkbox" value="'+key+'">'+key+'</input>')
            self.w("<label for='" + key + "_filter'>Filtre : </label>")
            self.wl("<input name='" + key + "_filter' id='" + key + "_filter' type='text' value='" +
                    escape(conf['filter']) + "' size='200'/>")
            self.w("<label for='" + key + "_now'>Now : </label>")
            self.wl("<input type='checkbox' name='" + key + "_now' id='" + key + "_now' type='text' value='True'/>")
            self.w("<label for='" + key + "_step'>Step : </label>")
            self.wl("<input name='" + key + "_step' id='" + key + "_step' type='text' value='" + '0' + "' size='200'/>")
            self.w('<fieldset><legend>Action</legend>')
            for key_action in actions.keys():
                self.wl('<input name="'+key+'_actions" type="checkbox" value="'+key_action+'">' + key_action +
                        '</input>')
            self.wl('</fieldset>')
        self.wl('</fieldset>')
        self.w('<input id="reset" type="reset"/><input id="submit" type="submit"/>')
        self.wl('</form>')

    def parse_post(self):
        content_len = int(self.headers.get('Content-Length'), 0)
        post_body = self.rfile.read(content_len)
        req = parse_qs(post_body, keep_blank_values=True, encoding='utf-8')
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
                            self.wl(filtre)
                            extract_jira(project=project, start_date=dataconf[project]['start'], filtre=filtre)
                        elif action == b'Cumulative':
                            j = jira_cum(project=project, details=True, date_file=sfx,
                                         weeks=dataconf[project]['weeks'], start_date=dataconf[project]['start'],
                                         step=step,
                                         chart_html=True)
                            self.wl(j, append=True)
                        elif action == b'Treemap':
                            j = jira_treemap(project=project, date_file=sfx, html=True, chart_html=True)
                            self.wl(j.split('<body>')[-1].split('</body>')[0] )
                        elif action == b'TreemapEpic':
                            for n, t, a in analysis_tree(project):
                                self.w('<details><summary>' + n + str(a) + '</summary>')
                                self.wl('' + t.split('<body>')[-1].split('</body>')[0] + '</details>')
                self.wl('</details>')
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
