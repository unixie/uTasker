#!/usr/bin/env python3
"""uTasker database interface
"""

# === Imports and Globals ====================================================
from dataclasses import dataclass, asdict
import os.path
from pathlib import Path
import sqlite3

_SCHEMA_FILE = Path(Path(__file__).parent, "utasker.sql")


# === Classes and Functions ==================================================

# --- Schema Data Structures -------------------------------------------------
@dataclass(eq=False)
class Record:
    """Record of a task"""
    ID : int
    State : str = "BACKLOG"
    Priority : str = "Low"
    Category : str = "-"
    Title : str = "New Task"
    Points : int = 1
    TimeSpent : float = 0.0
    Details : str = "TBA"

    def as_list(self):
        return list(self.__dict__.values())

    def as_dict(self):
        return asdict(self)

def _get_field_names_of_Record() -> list[str]:
    obj = Record(0)
    return(list(asdict(obj).keys()))
RECORD_FIELD_NAMES = _get_field_names_of_Record()

def record_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return Record(**{k: v for k, v in zip(fields, row)})


# === Database API ===========================================================
# --- sqlite3 backend --------------------------------------------------------
_CON = None
_DCUR = None

def new_record() -> Record:
    _DCUR.execute("INSERT INTO Tasks DEFAULT VALUES;")
    res = _DCUR.execute("SELECT * FROM Tasks WHERE ID=last_insert_rowid();")
    _CON.commit()
    return res.fetchall()[0]

def get_record(
        id : int
) -> Record:
    res = _DCUR.execute("SELECT * FROM Tasks WHERE ID=?;", (id,))
    return res.fetchall()[0]

def set_record(
        rec : Record
) -> None:
    reclist = rec.as_list()
    _DCUR.execute(
    """
    UPDATE Tasks
    SET
        State = ?,
        Priority = ?,
        Category = ?,
        Title = ?,
        Points = ?,
        TimeSpent = ?,
        Details = ?
    WHERE
        ID = ?
    ;""",
    (*reclist[1:], reclist[0]))  # TODO: nicer to have all in order?
    _CON.commit()

def view_dataset(
        filter : list[str] = []
) -> list[Record]:
    if len(filter) > 0:
        filter = str([s for s in filter])[1:-1]
        filter = "(" + filter + ")"
        cmd = "SELECT * FROM TASKS WHERE State IN {}".format(filter)
    else:
        cmd = "SELECT * FROM Tasks;"
    res = _DCUR.execute(cmd)
    return res.fetchall()

def load(
        dbfile : str
) -> None:
    global _CON
    global _DCUR
    if dbfile is None:
        _CON = sqlite3.connect(":memory:")
    else:
        _CON = sqlite3.connect(dbfile)

    # specialized data record cursor
    _DCUR = _CON.cursor()
    _DCUR.row_factory = record_factory

    def _prepare_db(add_examples : bool = False) -> None:
        with open(_SCHEMA_FILE, "rt") as file:
            schema_str = file.read()
        cur = _CON.cursor()  # default cursor for general operations
        cur.executescript(schema_str)
        if add_examples:
            for i in range(3):
                res = _DCUR.execute("""INSERT INTO Tasks DEFAULT VALUES;""")

    # One time preparation
    if dbfile is None:
        _prepare_db(add_examples = True)
    elif os.path.getsize(dbfile) == 0:  # file already exists
        _prepare_db()
    else:
        pass

def store():
    _CON.close()

def get_categories() -> set[str]:
    cur = _CON.cursor()
    res = cur.execute("SELECT * FROM Categories;")
    row = res.fetchall()
    return {x[0] for x in row}

def update_categories(
        live : set[str]
) -> None:
    stored = get_categories()
    assert stored <= live
    additions = live - stored
    if len(additions) > 0:
        cur = _CON.cursor()
        cmd = "INSERT INTO Categories (Category) VALUES (?)"
        cur.executemany(cmd, [(s,) for s in additions])

def get_states() -> tuple[str]:
    cur = _CON.cursor()
    res = cur.execute("SELECT * FROM States;")
    row = res.fetchall()
    return tuple([x[0] for x in row])

def get_priorities() -> tuple[str]:
    cur = _CON.cursor()
    res = cur.execute("SELECT * FROM Priorities;")
    row = res.fetchall()
    return tuple([x[0] for x in row])
