# uTasker

Micro task manager: command line, cross-platform, local storage.


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

Manages a table of tasks in a sqlite file that can be located anywhere you wish.

### Mental Model

- Press **Update** for any change to take place
- Super-simple Agile, retaining only the concept of Points and sort of Sprint (Workbench)
- Once completed, a Task cannot be revived, only cloned
- Use database with external tools for analysis (Points to time, etc)


### Workflow

- Backlog screen
  - Add new tasks
  - Select UPCOMING to add to Workbench screen
- Workbench screen
  - Track the progress of tasks
    - Time spent can be in whichever unit you want: hours, work-days, etc
  - Move back to Backlog if expectations change (i.e. Points)
  - Send to Archive by DONE or CANCELLED
- Archive screen
  - See list of completed tasks

### Usage Notes

- Click task table columns for simple sort
- Run without file to play around with the application; don't forget changes are not saved!
- TIP: place database file in a Dropbox directory for secure sharing and backup
- Copy/Paste carefully, see [Textual FAQ](https://textual.textualize.io/FAQ/#how-can-i-select-and-copy-text-in-a-textual-app) for more details
