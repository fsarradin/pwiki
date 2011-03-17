# sqldb.py -
#

import article
import re
from manager import CATEGORY_NS

def _regexp(pattern, st):
    return re.match(pattern, st) is not None

def matchRedirect(wiki_article):
    return re.match(r'%%REDIRECT:\s*(?P<link>[^\]]*)',
                    wiki_article.getContent().strip())

class SqlArticleStats(article.ArticleStats):
    def __init__(self, row):
        # row :=: (0:title, 1:ns, 2:ctime, 3:mtime,
        #          4:redir_to_title, 5:redir_to_ns,
        #          6:size)
        self.__row = row
        self.__subject = article.Subject(self.__row[0], self.__row[1])
        self.__rd_subject = None
        if self.__row[4] is not None:
            self.__rd_subject = article.Subject(self.__row[4], self.__row[5])
    
    def getSubject(self):
        return self.__subject
        
    def getCreationTime(self):
        return self.__row[2]
        
    def getModificationTime(self):
        return self.__row[3]
        
    def isRedirect(self):
        return self.__rd_subject is not None
        
    def redirectTo(self):
        return self.__rd_subject
        
    def getSize(self):
        if self.__row[6] is None:
            return 0
        return self.__row[6]

class SqlArticleManager(article.ArticleManager):
    def __init__(self, connection):
        self.__connection = connection
        self.__connection.create_function("regexp", 2, _regexp)

    def __getArticleId(self, subject):
        cursor = self.__connection.cursor()
        cursor.execute("""
SELECT art_id
FROM article
WHERE art_title = ?
  AND art_ns = ?
""", (subject.getTitle(), subject.getNamespace()))
        art_id = cursor.fetchone()[0]
        cursor.close()
        return int(art_id)

    def __isRedirect(self, subject):
        cursor = self.__connection.cursor()
        cursor.execute("""
SELECT COUNT(*)
FROM article, redirect
WHERE article.art_title = ?
  AND article.art_ns = ?
  AND article.art_id = redirect.art_id
""", (subject.getTitle(), subject.getNamespace()))
        result = int(cursor.fetchone()[0]) != 0
        cursor.close()
        return result

    def contains(self, subject):
        cursor = self.__connection.cursor()
        cursor.execute("""
SELECT COUNT(*)
FROM article
WHERE art_title = ?
  AND art_ns = ?
""", (subject.getTitle(), subject.getNamespace(),))
        result = int(cursor.fetchone()[0]) != 0
        cursor.close()
        return result

    def get(self, subject):
        art_id = self.__getArticleId(subject)
        is_redirect = self.__isRedirect(subject)
        cursor = self.__connection.cursor()
        if is_redirect:
            # the article is a redirection
            cursor.execute("""\
SELECT rd_title, rd_ns
FROM redirect
WHERE art_id = %d
""" % art_id)
            title, ns = cursor.fetchone()
            rd_subject = article.Subject(title, ns)
            art = article.RedirectArticle(subject, rd_subject)
        else:
            # get the article content
            cursor.execute("""\
SELECT cont_text
FROM content
WHERE art_id = %d
""" % art_id)
            content = cursor.fetchone()[0]
            # get all the categories the article owned to
            cursor.execute("""\
SELECT cat_art_title
FROM category
WHERE art_id = %d
""" % art_id)
            categories = tuple(row[0] for row in cursor)

            if subject.getNamespace() == CATEGORY_NS:
                # the article is a category article
                # ...get all subjects of a category
                cursor.execute("""
SELECT art_title, art_ns
FROM article, category
WHERE cat_art_title = ?
  AND category.art_id = article.art_id
ORDER BY art_ns, art_title ASC
""", (subject.getTitle(),))
                subjects = {}
                for row in cursor:
                    title, ns = row
                    subjects.setdefault(ns, []).append(article.Subject(title, ns))
                art = article.CategoryArticle(subject, content, subjects, categories)
            else:
                # it is a normal article
                art = article.UserArticle(subject, content, categories)
        
        cursor.close()
        return art

    def subjects(self):
        cursor = self.__connection.cursor()
        cursor.execute(r"""
SELECT art_title, art_ns, art_ctime, art_mtime, rd_title, rd_ns, cont_len
FROM
  article
    LEFT JOIN redirect ON article.art_id = redirect.art_id
    LEFT JOIN content  ON article.art_id = content.art_id
ORDER BY art_ns, art_title ASC

-- SELECT art_title, art_ns
-- FROM article
-- ORDER BY art_ns, art_title ASC
""")
        subjects = {}
        for row in cursor:
            ns = row[1]
            stats = SqlArticleStats(row)
            subjects.setdefault(ns, []).append(stats)
#            title, ns = row
#            subjects.setdefault(ns, []).append(article.Subject(title, ns))
        cursor.close()
        return subjects

    def count(self):
        cursor = self.__connection.cursor()
        cursor.execute(r"""
SELECT COUNT(*)
FROM article
""")
        result = int(cursor.fetchone()[0])
        cursor.close()
        return result

    def __setUserArticle(self, art):
        subject = art.getSubject()
        content = art.getContent()
        categories = art.getCategories()
        cursor = self.__connection.cursor()

        if self.contains(art.getSubject()):
            # the article exists in the database
            art_id = self.__getArticleId(subject)
            if self.__isRedirect(subject):
                # if the article was a redirection
                # delete it from the redirect table
                cursor.execute("""
DELETE FROM redirect
WHERE art_id = %d
""" % art_id)
            # delete all references in the category table
            # in a view to replace them later...
            cursor.execute("""
DELETE FROM category
WHERE art_id = %d
""" % art_id)
            # update the modification time
            cursor.execute("""
UPDATE article
SET art_mtime = CURRENT_TIMESTAMP
WHERE art_id = %d
""" % art_id)
            
        else:
            # the article is unknown in the database
            # ... add it
            cursor.execute("""
INSERT INTO article (art_title, art_ns, art_ctime, art_mtime)
    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
""", (subject.getTitle(), subject.getNamespace()))

        # update the article content
        art_id = self.__getArticleId(subject)
        cursor.execute(r"""
INSERT OR REPLACE INTO content
    VALUES (%d, ?, %d)
""" % (art_id, len(content)), (content,))

        # update the category links
        params = []
        for category in categories:
            params.append((category, art_id))
        cursor.executemany(r"""
INSERT INTO category
    VALUES (?, ?)
""", params)
        cursor.close()
        self.__connection.commit()

    def __setRedirectArticle(self, art):
        subject = art.getSubject()
        rd_subject = art.redirectTo()
        cursor = self.__connection.cursor()
        
        if self.contains(subject):
            # the article exists in the database
            art_id = self.__getArticleId(subject)
            if not self.__isRedirect(subject):
                # the article was not a redirection
                # ... delete its content
                cursor.execute("""
DELETE FROM content
WHERE art_id = %d
""" % art_id)
                # ... and all category links
                cursor.execute("""
DELETE FROM category
WHERE art_id = %d
""" % art_id)
            # update the modification time
            cursor.execute("""
UPDATE article
SET art_mtime = CURRENT_TIMESTAMP
WHERE art_id = %d
""" % art_id)
        else:
            # the article is unknown in the database
            # ... create it
            cursor.execute("""
INSERT INTO article (art_title, art_ns, art_ctime, art_mtime)
    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
""", (subject.getTitle(), subject.getNamespace()))

        # set the redirection
        art_id = self.__getArticleId(subject)
        cursor.execute(r"""
INSERT OR REPLACE INTO redirect
    VALUES (%d, ?, ?)
""" % art_id, (rd_subject.getTitle(), rd_subject.getNamespace()))
        cursor.close()
        self.__connection.commit()

    def __setCategoryArticle(self, art):
        # a category article is like a user article
        self.__setUserArticle(art)

    def set(self, art):
        art_cls_name = art.__class__.__name__
        method_name = '_' + self.__class__.__name__ + '__set' + art_cls_name
        self.__getattribute__(method_name)(art)

    def delete(self, subject):
        art_id = self.__getArticleId(subject)
        cursor = self.__connection.cursor()
        # delete the article metadata
        cursor.execute("""
DELETE FROM article
WHERE art_id = %d
""" % art_id)
        # delete its content
        cursor.execute("""
DELETE FROM content
WHERE art_id = %d
""" % art_id)
        # delete its redirection
        cursor.execute("""
DELETE FROM redirect
WHERE art_id = %d
""" % art_id)
        # delete all category links to it
        cursor.execute("""
DELETE FROM category
WHERE art_id = %d
""" % art_id)
        cursor.close()
        self.__connection.commit()

def dumpCursor(cursor):
    fields = tuple(unicode(field[0]) for field in cursor.description)
    rows = tuple(tuple(unicode(cell) for cell in row) for row in cursor)
    
    just_list = [len(field) for field in fields]
    for row in rows:
        for i in range(len(row)):
            just_list[i] = max(len(row[i]), just_list[i])
    
    for i in range(len(fields)):
        print fields[i].ljust(just_list[i]),
    print ''
    for i in range(len(fields)):
        print '-' * just_list[i],
    print ''
    for row in rows:
        for i in range(len(row)):
            print row[i].ljust(just_list[i]),
        print ''

# End
