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


-- Tasks is the foundation table
CREATE TABLE IF NOT EXISTS Tasks (
    ID          INTEGER PRIMARY KEY,
    State       TEXT NOT NULL DEFAULT 'BACKLOG',
    Title       TEXT NOT NULL DEFAULT 'New Task',
    Points      INTEGER CHECK (Points > 0) DEFAULT 1,
    TimeSpent   REAL DEFAULT 0,
    Description TEXT DEFAULT 'TBA',
    Notes       TEXT DEFAULT 'None',
    FOREIGN KEY (State)
    REFERENCES States (StateName)
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
CREATE VIEW IF NOT EXISTS Sprint AS
    SELECT
        TaskID,
        Title,
        Description,
        StoryPoints,
        TimeSpent,
        State
    FROM
        Tasks
    WHERE
        State IN ('UPCOMING', 'IN PROGRESS', 'REVIEW')
    ORDER BY
        State
;
-- Propagate updates from within view
CREATE TRIGGER IF NOT EXISTS UpdateSprintState
    INSTEAD OF UPDATE OF State ON Sprint
    BEGIN
        UPDATE Tasks SET State = NEW.State
        WHERE ID = NEW.ID;
    END
;

CREATE TRIGGER IF NOT EXISTS IncreaseSprintTimeSpent
    INSTEAD OF UPDATE OF TimeSpent ON Sprint
    BEGIN
        UPDATE Tasks SET TimeSpent = TimeSpent + NEW.TimeSpent
        WHERE TaskID = NEW.ID;
    END
;
