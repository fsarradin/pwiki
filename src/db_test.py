# db_test.py -
#

import sqlite3
import sys

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

def execute(db_conn, query):
    cursor = db_conn.cursor()
    cursor.execute(query)
    dumpCursor(cursor)
    cursor.close()

def executescript(db_conn, query):
    cursor = db_conn.cursor()
    cursor.executescript(query)
    cursor.close()

db_conn = sqlite3.connect('test-wiki.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

cursor = db_conn.cursor()

cursor.execute("""
SELECT art_title, art_ns, art_ctime, art_mtime, rd_title, rd_ns, cont_len
FROM article
  LEFT JOIN redirect ON article.art_id = redirect.art_id
  LEFT JOIN content ON article.art_id = content.art_id
ORDER BY art_ns, art_title ASC
""")
dumpCursor(cursor)

##cursor.execute("SELECT * FROM article")
##dumpCursor(cursor)
##cursor.execute("SELECT * FROM content")
##dumpCursor(cursor)
##cursor.execute("SELECT * FROM redirect")
##dumpCursor(cursor)
##cursor.execute("SELECT * FROM category")
##dumpCursor(cursor)

cursor.close()

db_conn.commit()
db_conn.close()

# End
