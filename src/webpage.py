# webpage.py -
#

_XHTML_DTD = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
_XHTML_NAMESPACE = 'http://www.w3.org/1999/xhtml'

def _xmlHeader(encoding):
    return '<?xml version="1.0" encoding="' + encoding + '"?>'

def _xhtmlHeader(encoding):
    return _xmlHeader(encoding) + '\n' + _XHTML_DTD + '\n\n' \
           + '<html xmlns="' + _XHTML_NAMESPACE + '">'

class WebPageObject(object):
    def getHtml(encoding): pass

class WebPageHeader(WebPageObject):
    def __init__(self, title):
        self.__title = title
        self.__lines = []

    def append(self, line):
        self.__lines.append(line)

    def getHtml(self, encoding):
        out = '<header>'
        out += '\n  <title>' + self.__title + '</title>'
        out += '\n  <meta http-equiv="Content-Type" content="text/html; charset=' \
               + encoding + '" />'
        for line in self.__lines:
            out += '\n  ' + line
        return out + '\n</header>'

class WebPageContent(WebPageObject):
    def __init__(self, content):
        self.__content = content

    def getHtml(self, encoding):
        out = '<body>'
        out += '\n' + self.__content
        return out + '\n</body>'

class WebPage(object):
    def __init__(self, header, content):
        self.__header = header
        self.__content = content

    def getHtml(self, encoding):
        out = _xhtmlHeader(encoding) + '\n'
        out += self.__header.getHtml(encoding) + '\n'
        out += self.__content.getHtml(encoding)
        return (out + '\n</html>\n').encode(encoding)

# End
