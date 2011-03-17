# formatter.py -
#

import urllib
import re

def escape(st, quote=False):
    if not isinstance(st, (str, unicode)):
        st = str(st)
    st = st.replace('&', '&amp;')
    st = st.replace('<', '&lt;')
    st = st.replace('>', '&gt;')
    if quote:
        st = st.replace('"', '&quote;')
    return st

def getId(st):
    out = st[0].upper() + st[1:]
    out = out.replace(' ', '_')
#    out = urllib.quote(out)
    out = out.replace('%A3', ':')
    out = out.replace('%', '.')
    return out

def expandTabs(st, width=4):
    return st.replace('\t', u' ' * width)

class RawOutput(object):
    def __init__(self, newline=u'\n', tablen=2):
        # output of the current context
        self.__output = u""
        # preceding contexts
        self.__context = []
        self.__newline = newline
        # tabulation length
        self.__tablen = tablen
        self.__indentSize = 0
    
    def newline(self):
        self.append(self.__newline)
    
    def indent(self):
        self.append(u' ' * (self.__indentSize * self.__tablen))
    
    def incrIndent(self):
        self.__indentSize += 1
    
    def decrIndent(self):
        self.__indentSize = self.__indentSize - 1
        assert self.__indentSize >= 0, "Bad indentation size"
    
    def append(self, st):
        self.__output += st
    
    def newContext(self, name):
        self.__context.append((name, self.__output))
        self.__output = u""
#        print 'newContext():', self.__context, self.__output
    
    def popContext(self):
#        print 'popContext():', self.__context, self.__output
        name, tmp = self.__context.pop()
        out = self.__output
        self.__output = tmp
        return name, out
    
    def getRaw(self):
        assert len(self.__context) == 0, "Context not empty"
        return self.__output

class HtmlBuilder(object):
    pre_tag = u'pre'
    block_tags = (u'div', u'p',
                  u'ul', u'ol', u'li',
                  u'table', u'tr',
                  u'h1', u'h2', u'h3', u'h4', u'h5', u'h6',
                  pre_tag)
    
    def __init__(self):
        self.__isInPre = False
    
    def text(self, raw, content, attrs=None):
        if self.__isInPre:
            raw.append(escape(content))
            return
        if len(content) == 0:
            return
        
        lines = content.splitlines()
        if len(lines) == 1 and len(lines[0]) == 0:
            raw.newline()
            raw.indent()
            return
        if attrs is not None:
            self.startElement(raw, u'span', attrs)
        for line in lines[:-1]:
            raw.append(escape(line))
            raw.newline()
            raw.indent()
        raw.append(escape(lines[-1]))
        if attrs is not None:
            self.endElement(raw, u'span')
    
    def comment(self, raw, content):
        raw.indent()
        raw.append(u'<!--')
        raw.newline()
        raw.incrIndent()
        for line in content.splitlines():
            raw.indent()
            raw.append(escape(line))
            raw.newline()
        raw.decrIndent()
        raw.indent()
        raw.append(u'-->')
        raw.newline()
    
    def startElement(self, raw, name, attrs={}):
        self.__isInPre = self.__isInPre or (name == self.pre_tag)
        if name in self.block_tags and self.__isInPre:
            raw.indent()
        raw.append(u"<" + name)
        if len(attrs) > 0:
            attr_list = []
            for attr, value in attrs.items():
                if type(value) in [list, tuple]:
                    value = u' '.join(value)
                attr_list.append(attr.strip() + u'="' \
                                 + escape(value, quote=True) \
                                 + u'"')
            raw.append(u' ' + u' '.join(attr_list))
        raw.newContext(name)
        if name in self.block_tags:
            raw.incrIndent()
    
    def endElement(self, raw, name):
        ctxt_name, out = raw.popContext()
        assert name == ctxt_name, "Context error: get '%s', must be '%s'" % (name, ctxt_name)
        if len(out) > 0:
            raw.append(u">")
            if name in self.block_tags:
                raw.newline()
                if not self.__isInPre:
                    raw.indent()
            raw.append(out)
            if name in self.block_tags:
                raw.decrIndent()
            if name in self.block_tags and not self.__isInPre:
                raw.indent()
            if name in self.block_tags:
                raw.newline()
            raw.append(u"</" + name + u">")
            if name in self.block_tags:
                raw.newline()
        else:
            raw.append(u" />")
            if name in self.block_tags:
                raw.newline()
                raw.decrIndent()
        if name == self.pre_tag:
            self.__isInPre = False

if __name__ == '__main__':
    raw = RawOutput()
    builder = HtmlBuilder()
    
    builder.startElement(raw, 'pre')
    builder.startElement(raw, 'strong')
    builder.text(raw, 'Hello hello')
    builder.endElement(raw, 'strong')
    builder.text(raw, '\n')
    builder.startElement(raw, 'strong')
    builder.text(raw, 'Hello hello')
    builder.endElement(raw, 'strong')
    builder.text(raw, '\nHello hello\nHello hello')
    builder.endElement(raw, 'pre')
    
    print raw.getRaw()

# End
