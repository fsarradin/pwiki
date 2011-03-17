# parser.py -
#

import article
import manager
import formatter
import re

class ContentObject(object):
    def __init__(self, type_name, pattern, is_open=False):
        self.__typeName = type_name
        self.__pattern = pattern
        self.__isOpen = is_open

    def getTypeName(self):
        return self.__typeName

    def getPattern(self):
        return self.__pattern

    def isOpen(self):
        return self.__isOpen

    def setOpen(self, is_open):
        self.__isOpen = is_open

    def switchOpen(self):
        self.__isOpen = not self.__isOpen

class WikiParser(object):
    # punctuation
    punct_rule = re.escape(u""""'}]|:,.)?!""")
    
    # HTML tags
    htmltag_close = ur"""(?P<_html_close_tag>[a-zA-Z_][a-zA-Z0-9_-]*)"""
    htmltag_open = ur"""(?P<_html_open_tag>[a-zA-Z_][a-zA-Z0-9_-]*)(?P<_html_param>(\s+[a-zA-Z_][a-zA-Z0-9_-]*=("[^"]+"|'[^']+'))+)?(\s*/)?"""
    html_rule = ur"""\<(/%(close_tag)s|%(open_tag)s)\>""" \
                % {'open_tag' : htmltag_open,
                   'close_tag' : htmltag_close}
    html_param_rule = ur"""(?P<html_param>(?P<name>[a-zA-Z_][a-zA-Z0-9_-]*)=(?P<value>"[^"]+"|'[^']+'))"""
    html_block = ('div', 'p', 'table', 'pre', 'hr',)
    
    # internal link
    subject_rule = ur"""(%(category)s\:?%(title)s)""" \
                   % {'category': ur"""[^\:\|\]\}\#]+""",
                      'title': ur"""[^\|\]\}\#]+"""}
    internal_link = ur"""\[\[(?P<_subj>%(subject)s)?(\#%(fragment)s)?(\|%(text)s)?\]\]""" \
                    % {'subject': subject_rule,
                       'fragment': ur"""(?P<_subj_frag>[^\|\]\}]+)""",
                       'text': ur"""(?P<_subj_text>[^\]]+)"""}
    template_rule = ur"""\{\{(?P<_tmpl_title>[^\|\]\}]+)(|?P<_tmpl_param>(\|[^\|\}]+)*)\}\}"""
    
    # url
    url_schema = ur"""http|https|file|ftp|mailto"""
    url_rule = ur"""(%(schema)s)\:(%(content)s)""" \
               % {'schema': url_schema,
                  'content': ur"([^\s\<%(punct)s]|[\.\?][^\s\<%(punct)s])+" \
                  % {'punct': punct_rule}}

    # external link
    external_link = ur"""\[(?P<_url_1>%(url)s)(\|(?P<_url_text>[^\[\]]+))?\]|(^|(?<![\w\[]))(?P<_url_2>%(url)s)""" \
                    % {'url': url_rule}
                    
    # formatting symbol
    cnt_objects = [
#            ContentObject('eol', ur"$"),
            ContentObject('emph', ur"''"),
            ContentObject('strong', ur"\*\*"),
            ContentObject('underline', ur"__"),
            ContentObject('strike', ur"--\(|\)--"),
            ContentObject('intlink', internal_link),
            ContentObject('extlink', external_link),
            ContentObject('email', ur"""[-\w._+]+\@[\w-]+(\.[\w-]+)+"""),
            ContentObject('li', ur"^[-\#]+\s*"),
            ContentObject('heading', ur"^\s*(?P<_hmarker>=+)\s*[^=]+\s*(?P=_hmarker)$"),
            ContentObject('processor', ur"""^%%.*$"""),
            ContentObject('html_mkup', html_rule),
            ContentObject('html_ent', ur"""&(\#\d{1,5}|\#x[0-9a-fA-F]+|\w+);""")
    ]
    
    no_new_p_before = ('heading', 'li', 'html_mkup', 'processor')
    
    def __init__(self, formatter, art_mgr):
        self.__art_mgr = art_mgr
        self.__formatter = formatter
        self.__cntObjects = {}
        rules =  []
        for cnt_object in self.cnt_objects:
            self.__cntObjects[cnt_object.getTypeName()] \
                = ContentObject(cnt_object.getTypeName(), cnt_object.getPattern())
            rules.append(ur"(?P<%s>%s)" % (cnt_object.getTypeName(), cnt_object.getPattern()))
        rules_st = u'|'.join(rules)
        self.__rules_re = re.compile(rules_st, re.MULTILINE | re.UNICODE)
        self.__html_re = re.compile(self.html_rule, re.MULTILINE | re.UNICODE)
        self.__html_param_re = re.compile(self.html_param_rule, re.MULTILINE | re.UNICODE)
        self.__intlink_re = re.compile(self.internal_link, re.UNICODE)
        self.__extlink_re = re.compile(self.external_link, re.UNICODE)
        self.__proc_re = re.compile(ur"%%(?P<command>[^\: ]+)\s*(\:(?P<params>([^\|]+|\|[^\|]+)+))?$")
        
        self.__blockStack = None
        self.__isInList = False
        self.__listPos = u''
        self.__categories = set()
    
    def __closeAll(self, raw):
        while len(self.__blockStack) > 0:
            tag = self.__blockStack.pop()
            self.__formatter.endElement(raw, tag)
        self.__isInList = False
        self.__listPos = u''
    
    def __scan(self, raw, block):
#        print "New block: %s" % repr(block)
        lastpos = 0
        for match in self.__rules_re.finditer(block):
#            print match.group(0)
            if lastpos < match.start():
                if len(self.__blockStack) == 0:
                    self.__blockStack.append(u'p')
                    self.__formatter.startElement(raw, u'p', {'class': 'scan-1'})
#                print '''  1 --> %s''' % repr(block[lastpos:match.start()])
                self.__formatter.text(raw, block[lastpos:match.start()])
            
            self.__replace(raw, match)
            lastpos = match.end()
        
        if len(self.__blockStack) == 0 and lastpos < len(block.rstrip()):
            self.__blockStack.append(u'p')
            self.__formatter.startElement(raw, u'p', {'class': 'scan-2'})
#        print '''  2 --> %s''' % repr(block[lastpos:])
        self.__formatter.text(raw, block[lastpos:])
    
    def __replace(self, raw, match):
        for type, content in match.groupdict().items():
            if content is None or type.startswith('_'):
                continue
            
            if len(self.__blockStack) == 0 and type not in self.no_new_p_before:
                self.__blockStack.append(u'p')
                self.__formatter.startElement(raw, u'p', {'class': 'replace-1'})
            
            cnt_object = self.__cntObjects[type]
            replacer_name = '_' + type + '_repl'
            if hasattr(self, replacer_name):
                replacer = getattr(self, replacer_name)
                replacer(raw, content, cnt_object)
            else:
                self.__formatter.text(raw, content, {u'class': (u'untreat', type)})
    
    def _li_repl(self, raw, content, cnt_object):
        def _diffLists(prev, next):
            i = 0
            while (i < len(prev)) and (i < len(next)) and (prev[i] == next[i]):
                i += 1
            to_close = prev[i:]
            to_open = next[i:]
            return to_close, to_open

        def _openLists(raw, st):
            for c in st:
                tag = u'ul'
                if c == '#':
                    tag = u'ol'
                self.__blockStack.append(tag)
                self.__formatter.startElement(raw, tag)
    
        def _closeLists(raw, st):
            for c in reversed(st):
                tag = u'ul'
                if c == '#':
                    tag = u'ol'
                self.__blockStack.pop()
                self.__formatter.endElement(raw, tag)

        st = content.strip()
        if not self.__isInList:
            self.__closeAll(raw)
            self.__isInList = True
        if len(self.__blockStack) > 0 and self.__blockStack[-1] == u'li':
            self.__blockStack.pop()
            self.__formatter.endElement(raw, u'li')
        
        to_close, to_open = _diffLists(self.__listPos, st)
#        print "(_li_repl) close=%s, open=%s" % (to_close, to_open)
        
        if to_open != to_close:
            _closeLists(raw, to_close)
            _openLists(raw, to_open)
            self.__listPos = st
        self.__blockStack.append(u'li')
        self.__formatter.startElement(raw, u'li')

    def _processor_repl(self, raw, content, cnt_object):
        match = self.__proc_re.match(content)
        if match is not None:
            cmd = match.group('command')
            params = [param.strip() for param in match.group('params').split('|')]
#            print "%s - %s" % (cmd, params)
            if cmd == 'CATEGORY':
                for param in params:
                    self.__categories.add(param)
        return u''

    def _html_ent_repl(self, raw, content, cnt_object):
        raw.append(content)
        
    def _html_mkup_repl(self, raw, content, cnt_object):
        isOpen = True
        isMarker = content.strip().endswith('/>')
        match = self.__html_re.match(content)
        tag = match.group('_html_open_tag')
        param = match.group('_html_param')
        if param is None:
            param = ''
        if tag is None:
            isOpen = False
            tag = match.group('_html_close_tag')
        isBlock = tag in self.html_block
        
        if isOpen:
            if not isBlock and len(self.__blockStack) == 0:
                self.__blockStack.append(u'p')
                self.__formatter.startElement(raw, u'p', {'class': '_html_mkup_repl-1'})
            if isBlock:
                self.__closeAll(raw)
                if not isMarker:
                    self.__blockStack.append(tag)
            attrs = {}
            for match in self.__html_param_re.finditer(param):
                name = match.group('name')
                value = match.group('value')[1:-1]
                attrs[name] = value
            self.__formatter.startElement(raw, tag, attrs)
            if isMarker:
                self.__formatter.endElement(raw, tag)
        else:
            if isBlock:
                self.__blockStack.pop()
            self.__formatter.endElement(raw, tag)
    
    def _intlink_repl(self, raw, content, cnt_object):
        match = self.__intlink_re.match(content)
        
        subj_st = match.group('_subj')
        text = match.group('_subj_text')
        fragment = match.group('_subj_frag')
        if subj_st is None:
            subj_st = u''
        if text is None:
            text = subj_st
            if fragment is not None:
                text += u'#' + fragment
                
        
        subject = article.Subject.fromString(subj_st)
        link_cls = "wiki-undefined"
        if self.__art_mgr.contains(subject):
            link_cls = "wiki-defined"
        href = u'/' + unicode(subject)
        if fragment is not None:
            href += u'#' + formatter.getId(fragment)
            subj_st += u'#' + fragment
        
        self.__formatter.startElement(raw, u'a', {'href': href,
                                                  'title': subj_st,
                                                  'class': link_cls})
        self.__formatter.text(raw, text)
        self.__formatter.endElement(raw, u'a')

    def _extlink_repl(self, raw, content, cnt_object):
        match = self.__extlink_re.match(content)
        url = match.group('_url_1')
        text = match.group('_url_text')
        if url is None:
            url = match.group('_url_2')
            text = url
        link_cls = "wiki-url"
        if url.startswith("mailto:"):
            link_cls = "wiki-mail"

        self.__formatter.startElement(raw, u'a', {'href': url,
                                                  'title': url,
                                                  'class': link_cls})
        self.__formatter.text(raw, text)
        self.__formatter.endElement(raw, u'a')

    def _email_repl(self, raw, content, cnt_object):
        self.__formatter.startElement(raw, u'a', {'href': u"mailto:" + content,
                                                  'title': content,
                                                  'class': "wiki-mail"})
        self.__formatter.text(raw, content)
        self.__formatter.endElement(raw, u'a')

    def _heading_repl(self, raw, content, cnt_object):
        heading = content.strip()
        depth = 1
        while heading[depth] == '=':
            depth += 1
        depth = min(6, depth)

        title = heading[depth:-depth].strip()
        heading_id = formatter.getId(title)
        self.__closeAll(raw)
        self.__formatter.startElement(raw, u'h%d' % depth, {'id': heading_id})
        #self.__formatter.text(raw, title)
        self.__blockStack.append(u'h%d' % depth)
        self.__scan(raw, title)
        self.__blockStack.pop()
        self.__formatter.endElement(raw, u'h%d' % depth)
    
    def _emph_repl(self, raw, content, cnt_object):
        cnt_object.switchOpen()
        if cnt_object.isOpen():
            self.__formatter.startElement(raw, u'em')
        else:
            self.__formatter.endElement(raw, u'em')
    
    def _strong_repl(self, raw, content, cnt_object):
        cnt_object.switchOpen()
        if cnt_object.isOpen():
            self.__formatter.startElement(raw, u'strong')
        else:
            self.__formatter.endElement(raw, u'strong')
    
    def _underline_repl(self, raw, content, cnt_object):
        cnt_object.switchOpen()
        if cnt_object.isOpen():
            self.__formatter.startElement(raw, u'span', {'class': 'wiki-underline'})
        else:
            self.__formatter.endElement(raw, u'span')
    
    def _strike_repl(self, raw, content, cnt_object):
        cnt_object.switchOpen()
        assert (cnt_object.isOpen() and content == '--(') or (not cnt_object.isOpen() and content == ')--')
        if cnt_object.isOpen():
            self.__formatter.startElement(raw, u'span', {'class': 'wiki-strike'})
        else:
            self.__formatter.endElement(raw, u'span')
    
    def __doCategories(self, raw, categories):
        def cat2ref(cat_st):
            title = article.norm_subj_elem(cat_st)
            subject = article.Subject(title, manager.CATEGORY_NS)
            link_cls = "wiki-undefined"
            if self.__art_mgr.contains(subject):
                link_cls = "wiki-defined"
            href = u'/' + unicode(subject)
            return title, subject, link_cls, href
        
        self.__formatter.startElement(raw, u'div', {'id': 'wiki-categories'})
        raw.append(u'Category: ')
        cat_r = []
        cat_list = sorted(categories)
        for i in range(len(cat_list)-1):
            cat_st = cat_list[i]
            title, subject, link_cls, href = cat2ref(cat_st)
            self.__formatter.startElement(raw, u'a', {'href': href,
                                                      'title': unicode(subject),
                                                      'class': link_cls})
            self.__formatter.text(raw, title)
            self.__formatter.endElement(raw, u'a')
            self.__formatter.text(raw, u' | ')
        if len(cat_list) > 0:
            title, subject, link_cls, href = cat2ref(cat_list[-1])
            self.__formatter.startElement(raw, u'a', {'href': href,
                                                      'title': unicode(subject),
                                                      'class': link_cls})
            self.__formatter.text(raw, title)
            self.__formatter.endElement(raw, u'a')
            
        self.__formatter.endElement(raw, u'div')

    def format(self, art):
        self.__blockStack = []
        self.__isInList = False
        self.__listPos = u''
        self.__categories = set()
        
        subject, content = art.getSubject(), art.getContent()
        raw = formatter.RawOutput()
        blocks = re.split('\r?\n(?:[ \t]*\r?\n)+', content.strip())
#        pprint.pprint(blocks)
        for block in blocks:
            self.__scan(raw, block)
            self.__closeAll(raw)
        
        if len(self.__categories) > 0:
            self.__doCategories(raw, self.__categories)
            
        return raw.getRaw()

if __name__ == '__main__':
    class Article(object):
        def __init__(self, subject, content):
            self.__subject = subject
            self.__content = content
            
        def getSubject(self):
            return self.__subject
        
        def getContent(self):
            return self.__content
    
    class ArticleManager(object):
        def contains(self, *args):
            return False

    content = u"""
== Test ==


Text text text [[text]]
http://google.fr/ untel.name@company.com

**Test test**
**Test --(test)--**

- **UUID nul**&nbsp;: <tt>urn:uuid:00000000-0000-0000-0000-000000000000</tt>,
- Espace de noms DNS (noms de domaine pleinement qualifi&eacute;s) : <tt>urn:uuid:6ba7b810-9dad-11d1-80b4-00c04fd430c8</tt>,
- Espace de noms URL : <tt>urn:uuid:6ba7b811-9dad-11d1-80b4-00c04fd430c8</tt>,

<pre class="aa">**Test test**
**Test test**</pre>

%%CATEGORY: Test

"""
    import formatter
    
    art = Article('Test', content)
    parser = WikiParser(formatter.HtmlBuilder(), ArticleManager())
    print parser.format(art)

# End
