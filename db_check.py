# db_check.py -
#

import sqldb
import sqlite3
import sys

if len(sys.argv) == 1 or len(sys.argv) > 3 \
   or (len(sys.argv) == 3 and sys.argv[1] != '-f'):
    print "USAGE: db_check.py [-f] db_name"
    sys.exit(0)
    
db_name = sys.argv[-1]
is_forced = (len(sys.argv) == 3)

db_conn = sqlite3.connect(db_name)

cursor = db_conn.cursor()
cursor.execute("""SELECT * FROM sqlite_master""")
print 'sqlite_master'
sqldb.dumpCursor(cursor)
cursor.close()
print ''
print 'article'
sqldb.dumpArticleDb(db_conn)

if not sqldb.containsArticleDb(db_conn):
    print "(**) %s has no article table" % (db_name,)
    if not is_forced:
        db_conn.close()
        sys.exit(0)
else:
    if not sqldb.isArticleDbValid(db_conn):
        print "(**) %s has an invalid article table" % (db_name,)
        if not is_forced:
            db_conn.close()
            sys.exit(0)
if is_forced:
    print "--> format article table in %s" % (db_name,)
    sqldb.formatArticleDb(db_conn)
print "%s database OK" % db_name
db_conn.close()

# End
