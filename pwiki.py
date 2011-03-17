# pwiki.py - personal wiki
# -*- encoding: UTF-8 -*-
#

import BaseHTTPServer
import manager
import webpage
import wikipage
import formatter
import wikiparser
import article

import urllib
import sys, os
import shutil
import re

WIKI_NAME = "Pwiki"

__version__ = "1.0"
__copyright__ = "%s %s - Copyright (C) Francois Sarradin, 2011" \
                % (WIKI_NAME, __version__)


#wiki_articledb = articledb.DummyArticleDb()
import sqlite3
import sqldb

wiki_connection = None
wiki_artmgr = None

wiki_manager = None

wiki_stylesheet = None

page_factory = None

class SystemList(manager.SystemCallback):
    def __init__(self, subject, art_mgr):
        self.__art_mgr = art_mgr
        self.__subject = subject

    def __getParagraph(self, ns_name, stat_list):
        content = u''
        nb_articles = 0
        for stats in stat_list:
            title = unicode(stats.getSubject())
            link = unicode(stats.getSubject())
            if title == '':
                title = '(Home)'
            content += """<li class="system-list">"""
            if stats.getSubject().getNamespace() != manager.SYSTEM_NS:
                content += """
  <span style="font-size: x-small;">
    (<a href="/%(link)s?action=edit" title="&Eacute;diter %(title)s">edit</a>)
    (<a href="/%(link)s?action=delete" title="Supprimer %(title)s">suppr</a>)
  </span>
  .&nbsp;.
""" % {'link': link, 'title': title}
            if stats.isRedirect():
                rd_subj_str = unicode(stats.redirectTo())
                style = "undefined"
                if self.__art_mgr.contains(stats.redirectTo()):
                    style = "defined"
                content += """<a
    class="defined"
    style="font-weight: medium;"
    href="/%(link)s" title="%(title)s">%(title)s</a>
    &nbsp;&nbsp;&nbsp;<strong><tt>--&gt;</tt></strong>&nbsp;&nbsp;&nbsp;
    <a class="%(style)s"
      style="font-style: italic;"
      href="/%(redir)s">%(redir)s</a>
""" % {'title': title, 'link': link, 'redir': rd_subj_str, 'style': style}
            else:
                content += """<a
    class="defined"
    style="font-weight: bold;"
    href="/%(link)s" title="%(title)s">%(title)s</a>
"""  % {'title': title, 'link': link}
                if stats.getModificationTime() is not None:
                    content += """.&nbsp;.
  <span style="color: gray; font-size: small;">[%(length)s car.] (%(date)s)</span>
""" % {'length': stats.getSize(), 'date': stats.getModificationTime()}
            content += '</li>\n'
            nb_articles += 1

        content = "<h2>" + ns_name \
                  + ' <span style="font-weight: normal; color: gray; font-size: small;">[' \
                  + unicode(nb_articles) + " article(s)]</span></h2>\n<ul>\n" \
                  + content
        return content + '</ul>\n'

    def __call__(self, subject):
        subjects = self.__art_mgr.subjects()
        content = ""
        if manager.DEFAULT_NS in subjects:
            content += self.__getParagraph("Articles",
                                           subjects[manager.DEFAULT_NS])
        if manager.CATEGORY_NS in subjects:
            content += self.__getParagraph("Categories",
                                           subjects[manager.CATEGORY_NS])
        if manager.TEMPLATE_NS in subjects:
            content += self.__getParagraph("Models",
                                           subjects[manager.TEMPLATE_NS])
        if manager.SYSTEM_NS in subjects:
            content += self.__getParagraph("System",
                                           subjects[manager.SYSTEM_NS])
        return article.SystemArticle(self.__subject, content)

class PwikiHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Pwiki HTTP request handler.
    
    This is an Adapter for MyWikiRequestHandler.
    """
    
    server_version = "PwikiHTTP/" + __version__

    def isAuthorized(self, client_address):
        """Check if a client is authorized to access to the wiki.
        """
        client_host, client_port = client_address
        return client_host == '127.0.0.1'

    def getSubject(self):
        """Get the subject from the path.
        """
        subject_st = urllib.unquote(self.path[1:].split('?', 1)[0]).decode('utf8')
        return article.Subject.fromString(subject_st)

    def getParameters(self):
        """Get all parameters sent by the client.
        """
        
        def getGETParams(path):
            """Get parameters in case of GET and POST methods.
            """
            if '?' in path:
                return path.split('?', 1)[1].split('&')
            return []

        def getPOSTParams(headers, rfile):
            """Get parameters in case of POST method.
            """
            if self.command.upper() == 'POST':
                length = headers.getheader('content-length')
                if length is None:
                    return []
                nb_bytes = int(length)
                if nb_bytes == 0:
                    return []
                return rfile.read(nb_bytes).split('&')
            return []

        # get all HTTP parameters
        encoding = self.headers.getencoding()
        if encoding == '7bit' or encoding is None:
            encoding = 'latin1'
        paramst_list = getGETParams(self.path) \
                       + getPOSTParams(self.headers, self.rfile)
        parameters = {}
        # convert HTTP parameters into a property dict
        for paramst in paramst_list:
            tmp = paramst.split('=', 1)
            name = unicode(tmp[0], encoding)
            value = None
            if len(tmp) == 2:
                value = urllib.unquote_plus(tmp[1])
            parameters[name] = value
        
        return parameters

    def sendError(self, code, title, message):
        webpage = page_factory.buildErrorPage(title, message)
        content = webpage.getHtml('UTF-8')
        content_type = 'text/html'
        content_length = len(content)

        self.send_response(code)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Length", content_length)
        self.end_headers()

        self.wfile.write(content)

    def sendWebPage(self, webpage):
        content = webpage.getHtml('UTF-8')
        content_type = 'text/html'
        content_length = len(content)

        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Length", content_length)
        self.end_headers()

        self.wfile.write(content)

    def sendStylesheet(self):
        f  = open(wiki_stylesheet, 'r')
        content = f.read()
        f.close()
        content_type = 'text/css'
        content_length = len(content)

        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Length", content_length)
        self.end_headers()

        self.wfile.write(content)

    def sendImage(self, filename):
        img_type = 'image/' + filename.rsplit('.', 1)[-1]
        path = 'img/' + filename
        try:
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return
        
        fs = os.fstat(f.fileno())
        self.send_response(200)
        self.send_header("Content-type", img_type)
        self.send_header("Content-Length", str(fs[6]))
        self.end_headers()
        shutil.copyfileobj(f, self.wfile)
        f.close()

    def __getArticle(self, subject, action):
        article_acquire = False
        art = None
        while not article_acquire:
            article_acquire = True
            if wiki_manager.contains(subject):
                # article is in the database
                art = wiki_manager.get(subject)
                if action == 'consult':
                    rd_subject = art.redirectTo()
                    if rd_subject is not None:
                        # the article is a redirection
                        # ... then the article isn't acquire
                        subject = rd_subject
                        article_acquire = False
            else:
                # article doesn't exists in the database
                art = article.UserArticle(subject, '')
                action = 'edit'
        if subject.getNamespace() == manager.SYSTEM_NS:
            action = 'consult'
        return subject, art, action
    
    def buildWebPage(self, subject, action):
        subject, wiki_article, action = self.__getArticle(subject, action)

        # action is only one 'consult' or 'edit'
        if action == 'consult':
            return page_factory.buildConsultPage(wiki_article)
        else:
            return page_factory.buildEditPage(wiki_article)

    def __buildArticle(self, subject, content):
        def matchRedirect(content):
            return re.match(r'\%%REDIRECT\:\s*(?P<link>[^\]]+)',
                            content.strip())
        
        def getCategories(content):
            matchIter = re.finditer(r'%%' \
                                    + manager.CATEGORY_NS.upper() \
                                    + r':\s*(?P<params>([^\|]+|\|[^\|]+)+)$',
                                    content)
            categories = []
            for match in matchIter:
                params = [param.strip() for param in match.group('params').split('|')]
                categories += params
            return tuple(categories)
        
        ns = subject.getNamespace()
        match = matchRedirect(content)
        if ns == manager.DEFAULT_NS and match is not None:
            rd_subject = article.Subject.fromString(match.group('link'))
            return article.RedirectArticle(subject, rd_subject)
        else:
            categories = ()
            if ns != manager.TEMPLATE_NS:
                categories = getCategories(content)
            return article.UserArticle(subject, content, categories)

    def handleWikiRequest(self):
        """Handle a wiki request.
        """
        # check authorisations
        if not self.isAuthorized(self.client_address):
            self.sendError(403, self.response[403][0], self.response[403][1])

        parameters = self.getParameters()
        if 'getcss' in parameters:
            # send the stylesheet
            self.sendStylesheet()
            return
        if 'getimage' in parameters:
            # send a image
            self.sendImage(parameters['getimage'])
            return

        # get subject
        subject = self.getSubject()
        
        # get action
        action = 'consult'
        if 'action' in parameters:
            action = parameters['action']

        if action in ['consult', 'edit']:
            # client wants to consult or edit an article
            webpage = self.buildWebPage(subject, action)
            self.sendWebPage(webpage)
            
        elif action == 'modify':
            # client wants to modify an article
            if 'content' in parameters and subject.getNamespace() != manager.SYSTEM_NS:
                art = self.__buildArticle(subject, parameters['content'])
                wiki_manager.set(art)
            self.send_response(301)
            self.send_header("Location",'/' \
                             + urllib.quote(unicode(subject).encode('utf8')))
            self.end_headers()
            
        elif action == 'delete':
            # client wants to delete an article
            if subject.getNamespace() != manager.SYSTEM_NS:
                wiki_manager.delete(subject)
            # send the client to the system list page
            self.send_response(301)
            self.send_header("Location", '/System:List')
            self.end_headers()
            
        else:
            # unknown action
            self.send_response(301)
            self.send_header("Location",'/' \
                             + urllib.quote(unicode(subject).encode('utf8')))
            self.end_headers()

    def do_GET(self):
        self.handleWikiRequest()

    def do_POST(self):
        self.handleWikiRequest()

if __name__ == '__main__':
    TEST = False
    
    import optparse
    
    DEFAULT_PORT = 8008
    DEFAULT_DB = 'wiki.db'
    if TEST:
        DEFAULT_DB = ':memory:'
    DEFAULT_CSS = 'wiki.css'
    DEFAULT_TEMPLATE = 'wiki.tmpl'
    
    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', dest='port', default=DEFAULT_PORT)
    parser.add_option('-d', '--db', dest='db', default=DEFAULT_DB)
    parser.add_option('-c', '--css', dest='css', default=DEFAULT_CSS)
    parser.add_option('-t', '--tmpl', dest='tmpl', default=DEFAULT_TEMPLATE)
    (options, args) = parser.parse_args()
    
    wiki_stylesheet = options.css

    wiki_connection = sqlite3.connect(options.db, isolation_level="IMMEDIATE")
    if TEST:
        from db_create import createDb
        createDb(wiki_connection)
        
    wiki_artmgr = sqldb.SqlArticleManager(wiki_connection)
    
    wiki_manager = manager.WikiManager(wiki_artmgr)
    userNsMgr = manager.UserNsManager(wiki_artmgr)
    systemNsMgr = manager.SystemNsManager()
    _systemList = SystemList(article.Subject('List', manager.SYSTEM_NS),
                             wiki_manager)
    systemNsMgr.register('List', _systemList)
    wiki_manager.registerNsMgr(manager.DEFAULT_NS, userNsMgr)
    wiki_manager.registerNsMgr(manager.CATEGORY_NS, userNsMgr)
    wiki_manager.registerNsMgr(manager.TEMPLATE_NS, userNsMgr)
    wiki_manager.registerNsMgr(manager.SYSTEM_NS, systemNsMgr)
    
    wiki_formatter = formatter.HtmlBuilder()
    wiki_parser = wikiparser.WikiParser(wiki_formatter, wiki_manager)
    
    page_factory = wikipage.WikiPageFactory(WIKI_NAME, __copyright__,
                                            wiki_parser, wiki_formatter,
                                            wiki_manager, options.tmpl)

    server_address = ('', int(options.port))
    httpd = BaseHTTPServer.HTTPServer(server_address, PwikiHTTPRequestHandler)
    sa = httpd.socket.getsockname()
    print "Serving", PwikiHTTPRequestHandler.server_version, "on", \
          sa[0], "port", sa[1], "..."
    httpd.serve_forever()

# End
