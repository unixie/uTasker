#!/usr/bin/env python3
"""uTasker application
"""

# === Imports and Globals ====================================================
from pathlib import Path
from types import MappingProxyType

# Database
import database as db
from database import STATES, RECORD_FIELD_NAMES

# TUI
from rich.console import RenderableType
from textual import on
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer
from textual.widgets import Rule
from textual.widgets import DataTable
from textual.widgets import Input
from textual.widgets import Button
from textual.widgets import TextArea
from textual.widgets import RadioSet, RadioButton
from textual.widgets import Checkbox
from textual.widgets import Static

# Order to display Record fields in DataTable columns
COLUMNS = MappingProxyType(dict(zip(RECORD_FIELD_NAMES, range(len(RECORD_FIELD_NAMES)))))

# Manually unfold for TUI
COLUMN_WIDTHS = MappingProxyType(dict(
    zip(RECORD_FIELD_NAMES,
        [
            5,      # ID
            9,      # State
            33,     # Title
            None,   # Points
            None,   # TimeSpent
            60,     # Description
        ]
    )
))

# === Classes and Functions ==================================================
# --- TUI actions ------------------------------------------------------------
# Actions update TUI and database together

def act_add_row(
        table : DataTable
) -> None:
    new_rec = db.new_record()
    table.add_row(*new_rec.as_list(), key=new_rec.ID)

def act_clone_row(
        table : DataTable,
        row_idx : int
) -> None:
    clone = table.get_row_at(row_idx)
    clone_rec = db.new_record()
    clone_rec.Title = "Clone of " + clone[COLUMNS["Title"]]
    clone_rec.Points = clone[COLUMNS["Points"]]
    clone_rec.Description = clone[COLUMNS["Description"]]
    db.set_record(clone_rec)
    table.add_row(*clone_rec.as_list(), key=clone_rec.ID)

def act_update_row(
        table : DataTable,
        row_idx : int
):
    row = table.get_row_at(row_idx)
    updated = db.get_record(row[COLUMNS["ID"]])
    updated.State       = row[COLUMNS["State"]]
    updated.Title       = row[COLUMNS["Title"]]
    updated.Points      = row[COLUMNS["Points"]]
    updated.TimeSpent   = row[COLUMNS["TimeSpent"]]
    updated.Description = row[COLUMNS["Description"]]
    db.set_record(updated)

# === Screens ================================================================

# --- Backlog: Add new tasks here --------------------------------------------
class Backlog(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable(zebra_stripes=True, cursor_type="row", classes="TaskList")
        yield Rule(line_style="heavy")
        with Vertical(classes="TaskDetails"):
            with Horizontal():
                with Vertical(id="TaskDetailsLeft"):
                    yield Input(placeholder="Points", classes="HBorder", id="HPoints")
                    yield Checkbox(STATES.UPCOMING.name, id="HCheck")
                with Vertical(id="TaskDetailsRight"):
                    yield Input(placeholder="Title", classes="HBorder", id="HTitle")
                    yield TextArea(classes="HBorder", id="HDescription")
            with Horizontal(classes="BottomButtons"):
                yield Button("Update", variant="primary", id="Update")
                yield Button("Add", variant="primary", id="Add")
                yield Button("Clone", variant="primary", id="Clone")

    def on_mount(self) -> None:
        table = self.query_one(".TaskList", DataTable)
        table.border_title = "Backlog"
        for label,width in COLUMN_WIDTHS.items():
            table.add_column(label=label,width=width)
        element = self.query(".HBorder")
        for e,t in zip(element, ["Points", "Title", "Description"]):
            e.border_title = t

    def on_screen_resume(self) -> None:
        table = self.query_one(".TaskList", DataTable)
        table.clear()
        for data in db.view_dataset([STATES.BACKLOG, STATES.UPCOMING]):
            table.add_row(*data.as_list(), key=data.ID)

    @on(DataTable.RowHighlighted, ".TaskList")
    def fill_details(
            self,
            message: DataTable.RowHighlighted
    ) -> None:
        message.stop()
        table = message.control
        self.highlighted_row = message.cursor_row
        record = table.get_row_at(self.highlighted_row)
        self.query_one("#HPoints").value = str(record[COLUMNS["Points"]])
        self.query_one("#HCheck").value = (record[COLUMNS["State"]] == STATES.UPCOMING)
        self.query_one("#HTitle").value = record[COLUMNS["Title"]]
        self.query_one("#HDescription").text = record[COLUMNS["Description"]]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        table = self.query_one(".TaskList", DataTable)
        if event.button.id == 'Update':
            # Update TUI with new state, since tied to concrete elements
            table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Title"]),
                                 value=self.query_one("#HTitle").value)
            table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Points"]),
                                 value=self.query_one("#HPoints").value)
            table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Description"]),
                                 value=self.query_one("#HDescription").text)
            table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["State"]),
                                 value = STATES.UPCOMING if self.query_one("#HCheck").value else STATES.BACKLOG)
            # Update underlying database from up to date Datatable
            act_update_row(table=table, row_idx=self.highlighted_row)
        elif event.button.id == 'Add':
            act_add_row(table=table)
            table.move_cursor(row=table.row_count - 1)
        elif event.button.id == 'Clone':
            act_clone_row(table=table, row_idx=self.highlighted_row)
            table.move_cursor(row=table.row_count - 1)
        else:
            raise ValueError("Unknown button id")


# --- Workbench: Tasks receiving attention -----------------------------------
class TimeSpent(Static):
    already_spent: float = 0.0

    def update(self, renderable: RenderableType = "") -> bool:
        if float(str(renderable)) >= self.already_spent:
            super().update(renderable)
            return True
        else:
            return False

    def set_already_spent(self, initial):
        self.already_spent = initial
        self.update(str(self.already_spent))


class Workbench(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable(zebra_stripes=True, cursor_type="row", classes="TaskList")
        yield Rule(line_style="heavy")
        with Vertical(classes="TaskDetails"):
            with Horizontal():
                with Container(id="TaskDetailsLeft"):
                    with Vertical(id="TimeSpentBox", classes="HBorder"):
                        yield TimeSpent(markup=False, id="TimeSpent")
                        yield Button("-0.5", id="dec")
                        yield Button("+0.5", id="inc")
                    yield RadioSet(*STATES.as_list(), id="TaskStates")
                with Vertical(id="TaskDetailsRight"):
                    yield Input(placeholder="Title", classes="HBorder", id="HTitle")
                    yield TextArea(classes="HBorder", id="HDescription")
            with Horizontal(classes="BottomButtons"):
                yield Button("Update", variant="primary", id="Update")
                yield Button("Tidy", variant="primary", id="Tidy")

    def on_mount(self) -> None:
        table = self.query_one(".TaskList", DataTable)
        table.border_title = "Workbench"
        for label,width in COLUMN_WIDTHS.items():
            table.add_column(label=label,width=width)
        element = self.query(".HBorder")
        for e,t in zip(element, ["Time Spent", "Title", "Description"]):
            e.border_title = t

    def on_screen_resume(self) -> None:
        table = self.query_one(".TaskList", DataTable)
        table.clear()
        for data in db.view_dataset([STATES.ACTIVE, STATES.REVIEW, STATES.UPCOMING]):
            table.add_row(*data.as_list(), key=data.ID)

    @on(DataTable.RowHighlighted, ".TaskList")
    def fill_details(
            self,
            message: DataTable.RowHighlighted
    ) -> None:
        message.stop()
        table = message.control
        self.highlighted_row = message.cursor_row
        record = table.get_row_at(self.highlighted_row)
        self.query_one("#TimeSpent").set_already_spent(record[COLUMNS["TimeSpent"]])
        self.query_one("#HTitle").value = record[COLUMNS["Title"]]
        self.query_one("#HDescription").text = record[COLUMNS["Description"]]

        radioset = self.query_one("#TaskStates")
        buttons = list(radioset.query(RadioButton))
        idx = STATES.index(record[COLUMNS["State"]])
        buttons[idx].value = True

    @on(Button.Pressed, "#Update")
    def update_button_pressed(
        self,
        message: Button.Pressed
    ) -> None:
        message.stop()
        table = self.query_one(".TaskList", DataTable)
        # Update TUI with new state, since tied to concrete elements
        spent = float(str(self.query_one("#TimeSpent").renderable))
        self.query_one("#TimeSpent").set_already_spent(spent)
        table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["TimeSpent"]),
                                value=spent)
        table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Title"]),
                                value=self.query_one("#HTitle").value)
        table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Description"]),
                                value=self.query_one("#HDescription").text)
        radioset = self.query_one("#TaskStates")
        buttons = list(radioset.query(RadioButton))
        idx = radioset.pressed_index
        table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["State"]),
                                value = STATES(str(buttons[idx].label)))
        # Update underlying database from up to date Datatable
        act_update_row(table=table, row_idx=self.highlighted_row)

    @on(Button.Pressed, "#inc")
    def inc(self):
        points = self.query_one("#TimeSpent")
        value = float(str(points.render())) + 0.5
        points.update(str(value))

    @on(Button.Pressed, "#dec")
    def dec(self):
        points = self.query_one("#TimeSpent")
        value = float(str(points.render())) - 0.5
        if not points.update(str(value)): self.app.bell()

    @on(Button.Pressed, "#Tidy")
    def tidy_button_pressed(
        self,
        message: Button.Pressed
    ) -> None:
        message.stop()
        table = self.query_one(".TaskList", DataTable)
        table.clear()
        for data in db.view_dataset([STATES.ACTIVE, STATES.REVIEW, STATES.UPCOMING]):
            table.add_row(*data.as_list(), key=data.ID)


# --- Archive: Retired tasks -------------------------------------------------
class Archive(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable(zebra_stripes=True, cursor_type="row", classes="TaskList")
        yield Rule(line_style="heavy")
        with Vertical(classes="TaskDetails"):
            with Horizontal():
                with Vertical(id="TaskDetailsLeft"):
                    yield Static()
                with Vertical(id="TaskDetailsRight"):
                    yield Input(placeholder="Title", classes="HBorder", id="HTitle", disabled=True)
                    yield TextArea(classes="HBorder", id="HDescription", disabled=True)
            with Horizontal(classes="BottomButtons"):
                yield Button("Clone to Backlog", variant="primary", id="Clone")

    def on_mount(self) -> None:
        table = self.query_one(".TaskList", DataTable)
        table.border_title = "Archive"
        for label,width in COLUMN_WIDTHS.items():
            table.add_column(label=label,width=width)
        element = self.query(".HBorder")
        for e,t in zip(element, ["Title", "Description"]):
            e.border_title = t

    def on_screen_resume(self) -> None:
        table = self.query_one(".TaskList", DataTable)
        table.clear()
        for data in db.view_dataset([STATES.CANCELLED, STATES.DONE]):
            table.add_row(*data.as_list(), key=data.ID)

    @on(DataTable.RowHighlighted, ".TaskList")
    def fill_details(
            self,
            message: DataTable.RowHighlighted
    ) -> None:
        message.stop()
        table = message.control
        self.highlighted_row = message.cursor_row
        record = table.get_row_at(self.highlighted_row)
        self.query_one("#HTitle").value = record[COLUMNS["Title"]]
        self.query_one("#HDescription").text = record[COLUMNS["Description"]]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        table = self.query_one(".TaskList", DataTable)
        act_clone_row(table=table, row_idx=self.highlighted_row)
        table.move_cursor(row=table.row_count - 1)


# === TUI App ================================================================
class uTaskerApp(App):

    CSS_PATH = "utasker.tcss"
    TITLE = "uTasker"
    SUB_TITLE = "Micro Task Manager"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the app"),
        Binding(key="b", action="switch_mode('Backlog')", description="Backlog"),
        Binding(key="w", action="switch_mode('Workbench')", description="Workbench"),
        Binding(key="a", action="switch_mode('Archive')", description="Archive"),
    ]
    MODES = {
        "Backlog" : Backlog,
        "Workbench" : Workbench,
        "Archive" : Archive,
    }

    def on_mount(self) -> None:
        self.switch_mode("Backlog")


# === Command Line Interface =================================================
if __name__ == "__main__":
    import argparse

    desc = __doc__ + '''\n
    '''
    epi = '''
    '''
    # Merge several help formatters
    class MyFormatter(argparse.RawDescriptionHelpFormatter,
                      argparse.ArgumentDefaultsHelpFormatter):
        pass

    parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                     formatter_class=MyFormatter)


    # --- Options ------------------------------------------------------------
    options = parser.add_argument_group("Options")
    options.add_argument(
        "--file",
        "-f",
        type = str,
        default = None,
        help = "Path to database file. None for in-memory, '' for temp file, both without persistence"
    )

#    debugs = parser.add_argument_group("Debug options")
#    debugs.add_argument(
#        "--simple",
#        "-s",
#        default = False,
#        action="store_true",
#        help = "Use a simple in-memory list based database instead of SQLite"
#    )

    # --- Argument validation ------------------------------------------------
    args = parser.parse_args()
    # TODO: figure out how to update the function pointers in runtime
#    if args.simple:
#        db.select_api(True)

    # --- Application --------------------------------------------------------
    db.load(args.file)
    app = uTaskerApp()
    app.run()