# article.py - article module
#

#########
# SUBJECT
#########

NS_SEPARATOR = u':' # namespace separator

def norm_subj_elem(element):
    """Normalize an element of a subject.
    """
    if len(element) == 0:
        return u''
    if len(element) == 1:
        return element[0].capitalize()
    return element[0].capitalize() + element[1:]

def split_subject(subject):
    """Split a subject according to the namespace separator.
    """
    ns = u''
    s = subject
#    print type(s)
#    print repr(s)
    if isinstance(s, str):
        s = s.decode('utf8')
    if NS_SEPARATOR in s:
        ns, s = s.split(NS_SEPARATOR, 1)
    return ns, s

def norm_subject(subject):
    """Normalize subject of the form ns:title to the tuple (Ns, Title).
    """
    ns = u''
    s = subject
    if NS_SEPARATOR in s:
        ns, s = s.split(NS_SEPARATOR, 1)
        ns = norm_subj_elem(ns)
    s = norm_subj_elem(s)
    return ns, s

class Subject(object):
    """Representation of an article subject.
    
    A subject is composed of a title. Each subject owns to a namespace. The
    default namespace is represent by an empty string.
    """
    def __init__(self, title, ns=''):
        self.__ns = norm_subj_elem(ns)
        self.__title = norm_subj_elem(title)

    def getTitle(self):
        """Get the subject title.
        
        @rtype: unicode
        """
        return self.__title

    def getNamespace(self):
        """Get the subject namespace.
        
        @rtype: unicode
        """
        return self.__ns

    def getCanonicalForm(self):
        """Get the canonical form of the subject (namespace:title).
        
        @rtype: unicode
        """
        st = self.__title
        if self.__ns != u'':
           st = self.__ns + NS_SEPARATOR + st 
        return st

    def __str__(self):
        return self.getCanonicalForm()

    def __eq__(self, subject):
        if isinstance(subject, Subject):
            return (self.__ns == subject.getNamespace()) \
                   and (self.__title == subject.getTitle())
        return False

    def __ne__(self, subject):
        return not self.__eq__(subject)

    @classmethod
    def fromString(cls, value):
        """Convert a string into a subject.
        
        @param value: string to convert
        @type value: string, unicode
        @rtype: L{Subject}
        """
        ns, title = split_subject(value)
        return Subject(title, ns)

#########
# ARTICLE
#########

class Article(object):
    """Base article representation.
    
    An article is composed of a L{subject<Subject>} and a content. In addition,
    a subject might own to one or more L{categories<CategoryArticle>}. At last,
    an article can be a redirection to another article.
    """
    
    def getSubject(self):
        """Get the subject (namespace and title) of this article.
        
        @rtype: L{Subject}
        """
        pass
    
    def getContent(self):
        """Get the content of this article.
        
        @rtype: unicode
        """
        pass
    
    def redirectedTo(self):
        """Get the subject this article is redirected to.

        Get None if no redirection is defined.
        
        @rtype: L{Subject}
        """
        pass

    def getCategories(self):
        """Get all the categories this article of this article.
        
        @return: a tuple of category titles.
        @rtype: tuple
        """
        pass

class UserArticle(Article):
    """A user article is an article a user can read.
    
    @param subject: article subject.
    @type subject: L{Subject}
    @param content: unicode
    @param categories: a list of category titles
    @type categories: list, tuple
    """
    
    def __init__(self, subject, content, categories=()):
        self.__subject = subject
        self.__content = content
        self.__categories = categories

    def getSubject(self):
        return self.__subject
        
    def getContent(self):
        return self.__content

    def redirectTo(self):
        return None

    def getCategories(self):
        return self.__categories

class RedirectArticle(Article):
    """Redirection article.
    
    @param subject: article subject.
    @type subject: L{Subject}
    @param redirect_to: the article subject it is redirected to
    @type redirect_to: L{Subject} 
    """
    def __init__(self, subject, redirect_to):
        self.__subject = subject
        self.__redirect = redirect_to

    def getSubject(self):
        return self.__subject

    def getContent(self):
        """Get the content of this article.
        
        @return: always return a string of the form C{%%REDIRECT: I{[subject]}}
        @rtype: unicode 
        """
        return u"%%%%REDIRECT: %s" % self.__redirect.getCanonicalForm()

    def redirectTo(self):
        """Get the subject this article is redirected to.

        Get None if no redirection is defined.
        
        @rtype: L{Subject}
        """
        return self.__redirect

    def getCategories(self):
        """Always return an empty tuple.
        
        @rtype: tuple
        """
        return ()

class CategoryArticle(UserArticle):
    """A category is a kind of article which help to class other articles.
    
    A category might own zero, one or more articles and other categories. An
    article or a category might be owned by zero, one or more categories.
    Hence, categories define relational classification of articles, but not
    necessarily a hierarchical one.
    
    @param subject: category subject.
    @type subject: L{Subject}
    @param content: category article content.
    @type content: unicode
    @param subjects: list of L{subjects<Subject>} owned by the category.
    @type subjects: list, tuple
    @param categories: a list of category titles
    @type categories: dict
    """
    def __init__(self, subject, content, subjects, categories=()):
        UserArticle.__init__(self, subject, content, categories)
        self.__subjects = subjects

    def getSubjects(self):
        """Get the subjects owned by the category.
        
        @rtype: tuple
        """
        return self.__subjects

class SystemArticle(UserArticle):
    def __init__(self, subject, content):
        UserArticle.__init__(self, subject, content)

class _DummyArticle(UserArticle):
    """This a class article for test purpose only.
    """
    
    CONTENT = """\
== Thalassius vero ==

Thalassius vero ea tempestate praefectus praetorio praesens ipse quoque
adrogantis ingenii, considerans incitationem eius ad multorum augeri
discrimina, non maturitate vel consiliis mitigabat, ut aliquotiens celsae
potestates iras principum molliverunt, sed adversando iurgandoque cum parum
congrueret, eum ad rabiem potius evibrabat, Augustum actus eius exaggerando
creberrime docens, idque, incertum qua mente, ne lateret adfectans. quibus mox
Caesar acrius efferatus, velut contumaciae quoddam vexillum altius erigens,
sine respectu salutis alienae vel suae ad vertenda opposita instar rapidi
fluminis irrevocabili impetu ferebatur.

=== Dein Syria ===

Dein Syria per speciosam interpatet diffusa planitiem. hanc nobilitat
Antiochia, mundo cognita civitas, cui non certaverit alia advecticiis ita
adfluere copiis et internis, et Laodicia et Apamia itidemque Seleucia iam inde
a primis auspiciis florentissimae.

Accedebant enim eius asperitati, ubi inminuta vel laesa amplitudo imperii
dicebatur, et iracundae suspicionum quantitati proximorum cruentae blanditiae
exaggerantium incidentia et dolere inpendio simulantium, si principis
periclitetur vita, a cuius salute velut filo pendere statum orbis terrarum
fictis vocibus exclamabant.
"""

    def __init__(self, subject):
        UserArticle.__init__(self, subject, _DummyArticle.CONTENT)

###############
# ARTICLE STATS
###############

class ArticleStats(object):
    """Contain stats on an article.
    """
    def getSubject(self):
        """Get the article subject.
        
        @rtype: L{Subject}
        """
        pass
    
    def getCreationTime(self):
        """Get the creation timestamp.
        
        @rtype: unicode
        """
        pass
    
    def getModificationTime(self):
        """Get the las modification timestamp.
        
        @rtype: unicode
        """
        pass
    
    def isRedirect(self):
        """Check if the article is a redirection.
        
        @rtype: bool
        """
        pass
    
    def redirectTo(self):
        """Get the subject this arrticle redirects to.
        
        @rtype: L{Subject}
        """
        pass
    
    def getSize(self):
        """Get the size of the content of this article in characters.
        
        @rtype: int
        """
        pass

class DefaultArticleStats(ArticleStats):
    def __init__(self, subject, ctime=None, mtime=None, size=0):
        self.subject = subject
        self.ctime = ctime
        self.mtime = mtime
        self.size = size
    
    def getSubject(self):
        return self.subject
    
    def getCreationTime(self):
        return self.ctime
    
    def getModificationTime(self):
        return self.mtime
    
    def isRedirect(self):
        return False
    
    def redirectTo(self):
        return None
    
    def getSize(self):
        return self.size

#################
# ARTICLE MANAGER
#################

class ArticleManager(object):
    """ArticleManager is a generic representation of all kind of article
    manager.
    
    Each article in a manager is identified by a subject.
    
    An article manager can be based on a database or his scope can be reduced
    to a specific namespace. An article manager can be imbricated in an other
    one.
    """
    
    def contains(self, subject):
        """Check if the manager owned a specific article identify by a subject.
        """
        pass
    
    def get(self, subject):
        """Get an article from its subject.
        
        @param subject: subject of the article.
        @type subject: L{Subject}
        @return: L{Article}
        """
        pass
    
    def set(self, article):
        """Create or modify an article.
        
        @param article: article to set.
        @type article: L{Article}
        """
        pass
    
    def delete(self, subject): pass
    def subjects(self): pass
    
    def iterator(self): pass
    def count(self): pass
    
    def __len__(self):
        return self.count()
    
    def __iter__(self):
        return self.iterator()

class ReadOnlyArticleManager(ArticleManager):
    """Get a read-only view of an article manager.
    """
    
    def __init__(self, art_mgr):
        self.__art_mgr = art_mgr

    def contains(self, subject):
        return self.__art_mgr.contains(subject)

    def get(self, subject):
        return self.__art_mgr.get(subject)

    def subjects(self):
        return self.__art_mgr.subjects()

    def iterator(self):
        return self.__art_mgr.iterator()

    def count(self):
        return self.__art_mgr.count()

class DummyArticleManager(ArticleManager):
    def __init__(self, art_cls=_DummyArticle):
        self.__artCls = art_cls
        self.__articles = [self.__artCls('')]
    
    def contains(self, subject):
        return True

    def get(self, subject):
        return self.__artCls(subject)

    def subjects(self):
        return {'': [article.getSubject() for article in self.__articles]}

    def iterator(self):
        return self.__articles.__iter__()

    def count(self):
        return self.__articles.__len__()

# End
