# db_create.py -
#

import sqlite3
import os, sys

def createDb(db_conn):
    cursor = db_conn.cursor()
    cursor.executescript("""
CREATE TABLE article (
    art_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    art_title       TEXT,
    art_ns          TEXT DEFAULT '',
    art_ctime       TIMESTAMP,
    art_mtime       TIMESTAMP
);

CREATE TABLE content (
    art_id    INTEGER PRIMARY KEY,
    cont_text BLOB,
    cont_len  INTEGER DEFAULT 0
);

CREATE TABLE redirect (
    art_id   INTEGER PRIMARY KEY,
    rd_title TEXT,
    rd_ns    TEXT
);

CREATE TABLE category (
    cat_art_title TEXT,
    art_id        INTEGER,
    PRIMARY KEY (cat_art_title, art_id)
);
""")
    cursor.close()
    db_conn.commit()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "USAGE: db_create.py db_name"
        sys.exit(0)

    db_name = sys.argv[-1]

    if os.path.exists(db_name):
        os.remove(db_name)

    db_conn = sqlite3.connect(db_name)
    createDb(db_conn)
    db_conn.close()

# End
