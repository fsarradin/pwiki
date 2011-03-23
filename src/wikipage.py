# -*- encoding: UTF-8 -*-
# wikipage.py -
#

import webpage
import article
import manager

import urllib
import os

_WIKI_MENU = article.Subject.fromString(u'%s:Menu' % manager.TEMPLATE_NS)
_DEFAULT_MENU_CONTENT = u"""\
- [[|Home]]
- [[System:List|Liste des articles]]
"""

class WikiPageFactory(object):
    DEFAULT_TEMPLATE = """\
<div id="wiki-header">
  <span id="wiki-product">%(wiki_name)s</span>
  <span id="wiki-title">%(title)s</span>
</div>

<div id="wiki-body">
<!-- menu -->
  <div id="wiki-menu">
%(menu)s
  </div>
  <div id="wiki-content-wrapper">
<!-- tabs -->
%(tabs)s
<!-- content -->
%(content)s
  </div>
</div>

<!-- footer -->
<div id="wiki-footer">
%(copy)s
</div>
"""
    
    def __init__(self, wiki_name, copyright, parser, formatter, manager, template):
        self.__wiki_name = wiki_name
        self.__copyright = copyright
        self.__parser = parser
        self.__formatter = formatter
        self.__manager = manager
        self.__template = template

    def buildMenu(self):
        if not self.__manager.contains(_WIKI_MENU):
            wiki_article = article.UserArticle(_WIKI_MENU, _DEFAULT_MENU_CONTENT)
            self.__manager.set(wiki_article)
        else:
            wiki_article = self.__manager.get(_WIKI_MENU)
            
        content = self.__parser.format(wiki_article)
        return """\
<h1>Menu</h1>
<div>
%s
</div>""" % content

    def buildTabs(self, tabs):
        tabs_html = '<div id="wiki-tabs">'
        for name, url, title in tabs:
            tabs_html += '<a href="%s" title="%s">%s</a>\n' % (url, title, name)
        return tabs_html + '</div>\n'

    def _buildPage(self, title, tabs, content):
        title = unicode(title)
        subject = title
        if subject == '':
            title = '(Home)'
        web_header = webpage.WebPageHeader(self.__wiki_name + ' >>> ' + title)
        web_header.append('<link rel="stylesheet" type="text/css" href="/?getcss" />')
        
        tabs_content = self.buildTabs(tabs)
        menu_content = self.buildMenu()

        template = self.DEFAULT_TEMPLATE
        if self.__template is not None:
            if os.path.isfile(self.__template):
                f = file(self.__template, 'r')
                try:
                    template = f.read()
                finally:
                    f.close()
            
        html_content = template % {'wiki_name': self.__wiki_name,
                                   'title': title,
                                   'tabs': tabs_content,
                                   'content': content,
                                   'copy': self.__copyright,
                                   'menu': menu_content}
        
        web_content = webpage.WebPageContent(html_content)
        return webpage.WebPage(web_header, web_content)

    def __getParagraph(self, ns_name, subjects):
        content = "<h2>" + ns_name + "</h2>\n<ul>\n"
        for subject in subjects:
            title = unicode(subject)
            link = unicode(subject)
            if title == '':
                title = '(Home)'
            content += """<li>
  <a class="defined" href="/%(link)s" title="%(title)s">%(title)s</a>
</li>\n
"""  % {'title': title, 'link': link}
        return content + '</ul>\n'

    def __buildSubjectList(self, subjects):
        content = ""
#        print subjects
        if manager.DEFAULT_NS in subjects:
            content += self.__getParagraph("Articles",
                                           subjects[manager.DEFAULT_NS])
        if manager.CATEGORY_NS in subjects:
            content += self.__getParagraph("Sub-categories",
                                           subjects[manager.CATEGORY_NS])
        if manager.TEMPLATE_NS in subjects:
            content += self.__getParagraph("Models",
                                           subjects[manager.TEMPLATE_NS])
        if manager.SYSTEM_NS in subjects:
            content += self.__getParagraph("System",
                                           subjects[manager.SYSTEM_NS])
        return content

    def buildConsultPage(self, art):
        subject = art.getSubject()
        article_content = u''
        
        if subject.getNamespace() == manager.SYSTEM_NS:
            tabs = [
                ('home', '/', 'go to the main page'),
                ('list', '/System:List', 'list of articles'),
                ]
            article_content = art.getContent()
        else:
            tabs = [
                ('edit', '/%s?action=edit' % subject, 'edit %s' % subject),
                ('home', '/', 'go to the main page'),
                ('list', '/System:List', 'list of articles'),
                ]
            article_content = self.__parser.format(art)
            
#        if subject == '':
#            subject = '(Home)'

        if subject.getNamespace() == manager.CATEGORY_NS:
            subj_list = self.__buildSubjectList(art.getSubjects())
            article_content += '\n<div id="wiki-subjects">\n' + subj_list \
                               + '\n</div>'
        
        tabs_content = self.buildTabs(tabs)
        ns = u''
        if subject.getNamespace() != '':
            ns = u' class="' + subject.getNamespace().lower() + u'"'
        html_content = u'<div id="wiki-content"%s>\n%s\n</div>\n' % (ns, article_content)
        return self._buildPage(subject, tabs, html_content)

    def buildEditPage(self, art):
        subject = art.getSubject()
        
        article_content = art.getContent().replace('&', '&amp;')
        tabs = [
            ('article', '/%s' % subject, 'see %s' % subject),
            ('home', '/', 'go to the main page'),
            ('list', '/System:List', 'list of articles'),
            ]

#        if subject == '':
#            subject = '(Home)'
        
        html_content = """\
<div id="wiki-content" class="wiki-edit">
<form name="wiki-edit" action="/%s" method="POST">
<input type="hidden" name="action" value="modify" />
<textarea name="content" cols="80" rows="40">%s</textarea><br />
<input type="submit" value="modify" />
</form>
</div>
""" % (subject, article_content)
        subj_str = unicode(subject)
        
        return self._buildPage(subj_str, tabs, html_content)

    def buildErrorPage(self, title, message):
        header = webpage.WebPageHeader(title)
        content = webpage.WebPageContent("<pre>%s</pre>" % message)
        return webpage.WebPage(header, content)

# End
