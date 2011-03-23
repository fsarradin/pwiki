# manager.py -
#

import article
from wikiexc import WikiException

DEFAULT_NS  = u""         # Default namespace
CATEGORY_NS = u"Category" # Category namespace
IMAGE_NS    = u"Image"    # Image namespace
#MODEL_NS    = u"Model"    # Model namespace
TEMPLATE_NS = u"Template" # Template namespace
SYSTEM_NS   = u"System"   # System namespace

class NamespaceManager(article.ArticleManager): pass

class UserNsManager(NamespaceManager):
    def __init__(self, art_mgr):
        self.__art_mgr = art_mgr

    def contains(self, subject):
        return self.__art_mgr.contains(subject)

    def get(self, subject):
        return self.__art_mgr.get(subject)

    def set(self, art):
        self.__art_mgr.set(art)

    def delete(self, subject):
        self.__art_mgr.delete(subject)

    def subjects(self):
        return self.__art_mgr.subjects()

    def count(self):
        return self.__art_mgr.count()

class SystemCallback(object):
    def __call__(self, subject):
        pass

class _DefaultCallback(SystemCallback):
    def getStats(self):
        None
    
    def __call__(self, subject):
        raise WikiException, 'Subject unknown: ' + str(subject)
_defaultCallback = _DefaultCallback()

class SystemNsManager(NamespaceManager):
    def __init__(self, default_cb=_defaultCallback):
        self.__callbacks = {}
        self.__defaultcb = default_cb
    
    def register(self, cb_name, cb):
        self.__callbacks[cb_name] = cb

    def contains(self, subject):
        return subject.getNamespace() == SYSTEM_NS \
               and subject.getTitle() in self.__callbacks

    def get(self, subject):
        title = subject.getTitle()
        if subject.getNamespace() == SYSTEM_NS:
            return self.__callbacks.get(title, self.__defaultcb)(subject)
        else:
            raise WikiException, 'Bad system namespace ' + ns

    def set(self, art):
        raise WikiException, 'The system namespace is read-only'

    def delete(self, subject):
        raise WikiException, 'The system namespace is read-only'

    def subjects(self):
        subjects = []
        for title in self.__callbacks.keys():
            subjects.append(
                article.DefaultArticleStats(article.Subject(title, SYSTEM_NS)))
        return {SYSTEM_NS: subjects}

    def count(self):
        return len(self.__callbacks)

class WikiManager(object):
    def __init__(self, art_mgr):
        self.__ns_mgr = {} # for System subjects
        self.__art_mgr = art_mgr

    def registerNsMgr(self, ns, ns_mgr):
        self.__ns_mgr[ns] = ns_mgr

    def recognizeNs(self, ns):
        return ns in self.__ns_mgr

    def getArticleManager(self):
        """Get an access-only copy of the article DB.
        """
        return article.ReadOnlyArticleManager(self.__art_mgr)

    def contains(self, subject):
        ns = subject.getNamespace()
        if ns in self.__ns_mgr:
            ns_mgr = self.__ns_mgr[ns]
            return ns_mgr.contains(subject)
        #raise WikiException, 'No manager namespace ' + ns
        return False

    def get(self, subject):
        ns = subject.getNamespace()
        if ns in self.__ns_mgr:
            ns_mgr = self.__ns_mgr[ns]
            return ns_mgr.get(subject)
        raise WikiException, 'No manager namespace ' + ns

    def set(self, art):
        subject = art.getSubject()
        ns = subject.getNamespace()
        if ns in self.__ns_mgr:
            ns_mgr = self.__ns_mgr[ns]
            ns_mgr.set(art)
        else:
            raise WikiException, 'No manager namespace ' + ns

    def delete(self, subject):
        ns = subject.getNamespace()
        if ns in self.__ns_mgr:
            ns_mgr = self.__ns_mgr[ns]
            ns_mgr.delete(subject)
        else:
            raise WikiException, 'No manager namespace ' + ns

    def subjects(self):
        subjects = {}
        for ns in self.__ns_mgr:
            subjects.update(self.__ns_mgr[ns].subjects())
        return subjects

    def count(self):
        count = 0
        for ns_mgr in self.__ns_mgr:
            count += ns_mgr.count()
        return count

# End
