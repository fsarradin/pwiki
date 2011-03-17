# db_show.py -
#

import sqldb
import sqlite3
import sys

if len(sys.argv) != 2:
    print "USAGE: db_show.py db_name"
    sys.exit(0)
    
db_name = sys.argv[-1]
db_conn = sqlite3.connect(db_name)
cursor = db_conn.cursor()
cursor.execute("""
SELECT *
FROM
  category ca,
  article art
WHERE art.art_id = ca.art_id
""")

sqldb.dumpCursor(cursor)

cursor.close()
db_conn.close()

# End
