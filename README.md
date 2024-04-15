# uTasker

Micro task manager: command line, cross-platform, local storage.

_Still work-in-progress_

## Installation

Dependencies:

- Python v3.9 onwards
- The fantastic [Textual](https://textual.textualize.io/)

One time setup of .venv:
```
# Windows Powershell
$ .\setup.ps1

# Unix-like
$ ./setup.sh
```

## Usage

Activate .venv:
```
# Windows Powershell
$ .\activate.ps1

# Unix-like
$ source activate
```

Then execute `apps/utasker.py --help` for more instructions.

## Micro Manual

Manages a table of tasks in a sqlite file that can be located anywhere you wish (**Tip**: place in a Dropbox directory for secure sharing and backup).

### Workflow

- Backlog screen
  - Add new tasks
  - Select UPCOMING which adds to Workbench screen
- Workbench screen
  - Track the progress of tasks, change their state
  - Move back to Backlog or send to Archive by DONE or CANCELLED
- Archive screen
  - See list of completed tasks

### Mental Model

- Press **Update** for any change to take place
- Super-simple Agile, retaining only the concept of Points and sort of Sprint (Workbench)
- Once done, a Task cannot be revived, only cloned
- Use database with external tools for analysis (Points to time, etc)

## TODO

- [ ] Search for task
- [ ] Epics
- [ ] Milestones
