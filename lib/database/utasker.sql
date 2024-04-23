/*

Schema description

*/


-- Runtime settings
PRAGMA foreign_keys=on;


-- States is a reference table
CREATE TABLE IF NOT EXISTS States (
    StateName   TEXT NOT NULL UNIQUE
);
-- Fill
INSERT OR IGNORE INTO States (StateName)
    VALUES
        ('BACKLOG'),
        ('UPCOMING'),
        ('ACTIVE'),
        ('REVIEW'),
        ('DONE'),
        ('CANCELLED')
;

-- Categories is a reference table
CREATE TABLE IF NOT EXISTS Categories (
    Category   TEXT NOT NULL UNIQUE
);
-- Fill
INSERT OR IGNORE INTO Categories (Category)
    VALUES
        ('-'),
        ('Feature'),
        ('Fix'),
        ('Document'),
        ('Test')
;


-- Tasks is the foundation table
CREATE TABLE IF NOT EXISTS Tasks (
    ID          INTEGER PRIMARY KEY,
    State       TEXT NOT NULL DEFAULT 'BACKLOG',
    Category    TEXT NOT NULL DEFAULT '-',
    Title       TEXT NOT NULL DEFAULT 'New Task',
    Points      INTEGER CHECK (Points > 0) DEFAULT 1,
    TimeSpent   REAL DEFAULT 0,
    Details     TEXT DEFAULT 'TBA',
    FOREIGN KEY (State)
    REFERENCES States (StateName)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
    FOREIGN KEY (Category)
    REFERENCES Categories (Category)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);
-- Rules
CREATE TRIGGER IF NOT EXISTS InsertTaskState
    BEFORE INSERT ON Tasks
    BEGIN
        SELECT CASE WHEN NEW.State != 'BACKLOG' THEN
            RAISE (ABORT, 'New Task must have BACKLOG as state')
    END;
END;

CREATE TRIGGER IF NOT EXISTS UpdateTaskState
    BEFORE UPDATE ON Tasks
    BEGIN
        SELECT CASE WHEN OLD.State = 'DONE' THEN
            RAISE (ABORT, 'Can not change state of DONE task')
    END;
END;


-- Workbench is a dynamic view
CREATE VIEW IF NOT EXISTS Active AS
    SELECT
        ID,
        State,
        Category,
        Title,
        Points,
        TimeSpent,
        Details
    FROM
        Tasks
    WHERE
        State IN ('UPCOMING', 'ACTIVE', 'REVIEW')
    ORDER BY
        State
;
-- Propagate updates from within view
CREATE TRIGGER IF NOT EXISTS UpdateActiveState
    INSTEAD OF UPDATE OF State ON Active
    BEGIN
        UPDATE Tasks SET State = NEW.State
        WHERE ID = NEW.ID;
    END
;
CREATE TRIGGER IF NOT EXISTS IncreaseActiveTimeSpent
    INSTEAD OF UPDATE OF TimeSpent ON Active
    BEGIN
        UPDATE Tasks SET TimeSpent = TimeSpent + NEW.TimeSpent
        WHERE TaskID = NEW.ID;
    END
;
