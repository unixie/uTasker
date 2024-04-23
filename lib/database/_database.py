#!/usr/bin/env python3
"""uTasker database interface
"""

# === Imports and Globals ====================================================
from dataclasses import dataclass, asdict
from enum import Enum
import itertools
import os.path
from pathlib import Path
import sqlite3

_SCHEMA_FILE = Path(Path(__file__).parent, "utasker.sql")


# === Classes and Functions ==================================================

# --- Schema Data Structures -------------------------------------------------
class STATES(Enum):
    """Possible states of a task"""
    BACKLOG     = "BACKLOG"
    UPCOMING    = "UPCOMING"
    ACTIVE      = "ACTIVE"
    REVIEW      = "REVIEW"
    DONE        = "DONE"
    CANCELLED   = "CANCELLED"

    def __str__(self):
        return self.name

    @classmethod
    def as_list(cls):
        return [v.value for v in cls]

    @classmethod
    def index(cls, name):
        _name = str(name) if isinstance(name, STATES) else name
        return cls.as_list().index(_name)

    @classmethod
    def default(cls):
        return cls.BACKLOG

@dataclass(eq=False)
class Record:
    """Record of a task"""
    ID : int
    State : STATES = STATES.default()
    Category : str = "-"
    Title : str = "New Task"
    Points : int = 1
    TimeSpent : float = 0.0
    Details : str = "TBA"

    def as_list(self):
        return list(self.__dict__.values())

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

def _new_record() -> Record:
    _DCUR.execute("INSERT INTO Tasks DEFAULT VALUES;")
    res = _DCUR.execute("SELECT * FROM Tasks WHERE ID=last_insert_rowid();")
    _CON.commit()
    return res.fetchall()[0]

def _get_record(
        id : int
) -> Record:
    res = _DCUR.execute("SELECT * FROM Tasks WHERE ID=?;", (id,))
    return res.fetchall()[0]

def _set_record(
        rec : Record
) -> None:
    reclist = rec.as_list()
    if type(reclist[1]) != str:  # FIXME: ugly kludge
        reclist[1] = reclist[1].value
    _DCUR.execute(
    """
    UPDATE Tasks
    SET
        State = ?,
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

def _view_dataset(
        filter : list[STATES] = []
) -> list[Record]:
    if len(filter) > 0:
        filter = str([s.value for s in filter])[1:-1]
        filter = "(" + filter + ")"
        cmd = "SELECT * FROM TASKS WHERE State IN {}".format(filter)
    else:
        cmd = "SELECT * FROM Tasks;"
    res = _DCUR.execute(cmd)
    return res.fetchall()

def _load(
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

    def _prepare_db() -> None:
        with open(_SCHEMA_FILE, "rt") as file:
            schema_str = file.read()
        cur = _CON.cursor()  # default cursor for general operations
        cur.executescript(schema_str)
        for i in range(3):  # TODO: remove eventually
            res = _DCUR.execute("""INSERT INTO Tasks DEFAULT VALUES;""")

    # One time preparation
    if dbfile is None:
        _prepare_db()
    elif os.path.getsize(dbfile) == 0:  # file already exists
        _prepare_db()
    else:
        pass

def _store():
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


# --- Simple backend for development instead of proper DB --------------------
_DATASET = []
_gen_ID = itertools.count(start=1)

def _new_record_simple() -> Record:
    rec = Record(next(_gen_ID))
    _DATASET.append(rec)
    return rec

def _get_record_simple(
        id : int
) -> Record:
    rec = [r for r in _DATASET if r.ID == id]
    assert(len(rec) == 1)
    return rec[0]

def _set_record_simple(
        rec : Record
) -> None:
    _dest = _get_record_simple(rec.ID)
    _DATASET[_DATASET.index(_dest)] = rec

def _view_dataset_simple(
        filter : list[STATES] = []
) -> list[Record]:
    if len(filter) > 0:
        view = [r for r in _DATASET if r.State in filter]
    else:
        view = _DATASET
    return view

def _load_simple(
        dbfile : str
) -> None:
    global _DATASET
    _DATASET = [
        Record(next(_gen_ID), Title="Tasker1", Points=3, Description="First one"),
        Record(next(_gen_ID), Title="Tasker2", Points=2, Description="Second one"),
        Record(next(_gen_ID), Title="Tasker3", Points=1, Description="Third one"),
    ]

def _store_simple():
    pass


# === Database API ===========================================================
def select_api(use_simple=False):
    global new_record, get_record, set_record, view_dataset
    global load, store
    if use_simple:
        new_record      = _new_record_simple
        get_record      = _get_record_simple
        set_record      = _set_record_simple
        view_dataset    = _view_dataset_simple
        load            = _load_simple
        store           = _store_simple
        print("simple")
    else:
        new_record      = _new_record
        get_record      = _get_record
        set_record      = _set_record
        view_dataset    = _view_dataset
        load            = _load
        store           = _store

select_api()
