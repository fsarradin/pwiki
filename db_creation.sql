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
