#!/usr/bin/env python3
"""uTasker application
"""

# === Imports and Globals ====================================================
from pathlib import Path
from types import MappingProxyType

# Database
import database as db

# TUI
from rich.console import RenderableType
from textual import on
from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.containers import Horizontal, Vertical, Container, Grid
from textual.widgets import Header, Footer
from textual.widgets import Rule
from textual.widgets import DataTable
from textual.widgets import Input
from textual.widgets import Button
from textual.widgets import TextArea
from textual.widgets import RadioSet, RadioButton
from textual.widgets import Checkbox
from textual.widgets import Static
from textual.widgets import Label


# Order to display Record fields in DataTable columns
COLUMNS = MappingProxyType(dict(zip(db.RECORD_FIELD_NAMES, range(len(db.RECORD_FIELD_NAMES)))))

# Manually unfold for TUI
COLUMN_WIDTHS = MappingProxyType(dict(
    zip(db.RECORD_FIELD_NAMES,
        [
            5,      # ID
            10,     # State
            8,      # Priority
            8,      # Category
            65,     # Title
            6,      # Points
            10,     # TimeSpent
            0,      # Details
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
    clone_rec.Category = clone[COLUMNS["Category"]]
    clone_rec.Priority = clone[COLUMNS["Priority"]]
    clone_rec.Points = clone[COLUMNS["Points"]]
    clone_rec.Details = clone[COLUMNS["Details"]]
    db.set_record(clone_rec)
    table.add_row(*clone_rec.as_list(), key=clone_rec.ID)

def act_update_row(
        table : DataTable,
        row_idx : int
):
    row = table.get_row_at(row_idx)
    updated = db.get_record(row[COLUMNS["ID"]])
    updated.State       = row[COLUMNS["State"]]
    updated.Category    = row[COLUMNS["Category"]]
    updated.Priority    = row[COLUMNS["Priority"]]
    updated.Title       = row[COLUMNS["Title"]]
    updated.Points      = row[COLUMNS["Points"]]
    updated.TimeSpent   = row[COLUMNS["TimeSpent"]]
    updated.Details     = row[COLUMNS["Details"]]
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
                    yield RadioSet(*sorted(db.get_categories()), classes="HBorder", id="HCategories")
                    yield RadioSet(*db.get_priorities(), classes="HBorder", id="HPriorities")
                    yield Checkbox("UPCOMING", id="HCheck")
                with Vertical(id="TaskDetailsRight"):
                    yield Input(placeholder="Title", classes="HBorder", id="HTitle")
                    yield TextArea(classes="HBorder", id="HDetails")
            with Horizontal(classes="BottomButtons"):
                yield Button("Update", variant="primary", id="Update")
                yield Button("Add", variant="primary", id="Add")
                yield Button("Clone", variant="primary", id="Clone")

    def on_mount(self) -> None:
        table = self.query_one(".TaskList", DataTable)
        table.border_title = "Backlog"
        for label,width in COLUMN_WIDTHS.items():
            table.add_column(label=label,width=width,key=label)
        element = self.query(".HBorder")
        for e,t in zip(element, ["Points", "Category", "Priority", "Title", "Details"]):
            e.border_title = t

    def on_screen_resume(self) -> None:
        table = self.query_one(".TaskList", DataTable)
        table.clear()
        for data in db.view_dataset(["BACKLOG", "UPCOMING"]):
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
        self.query_one("#HCheck").value = (record[COLUMNS["State"]] == "UPCOMING")
        self.query_one("#HTitle").value = record[COLUMNS["Title"]]
        self.query_one("#HDetails").text = record[COLUMNS["Details"]]
        radioset = self.query_one("#HCategories")
        buttons = list(radioset.query(RadioButton))
        idx = sorted(db.get_categories()).index(record[COLUMNS["Category"]])
        buttons[idx].value = True
        radioset = self.query_one("#HPriorities")
        buttons = list(radioset.query(RadioButton))
        idx = db.get_priorities().index(record[COLUMNS["Priority"]])
        buttons[idx].value = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        table = self.query_one(".TaskList", DataTable)
        if event.button.id == 'Update':
            # Update TUI with new state, since tied to concrete elements
            table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Title"]),
                                 value=self.query_one("#HTitle").value)
            table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Points"]),
                                 value=self.query_one("#HPoints").value)
            table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Details"]),
                                 value=self.query_one("#HDetails").text)
            table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["State"]),
                                 value = "UPCOMING" if self.query_one("#HCheck").value else "BACKLOG")
            radioset = self.query_one("#HCategories")
            buttons = list(radioset.query(RadioButton))
            idx = radioset.pressed_index
            table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Category"]),
                                    value = str(buttons[idx].label))
            radioset = self.query_one("#HPriorities")
            buttons = list(radioset.query(RadioButton))
            idx = radioset.pressed_index
            table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Priority"]),
                                    value = str(buttons[idx].label))
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

    @on(DataTable.HeaderSelected, ".TaskList")
    def sort_by_column(
        self,
        message: DataTable.HeaderSelected
    ) -> None:
        message.data_table.sort(message.column_key)


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


class WarningScreen(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Can't change state of DONE or CANCELLED Task", disabled=True),
            Button.warning("Got It"),
            id="WarningScreenContent",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


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
                    yield RadioSet(*db.get_states(), id="TaskStates")
                with Vertical(id="TaskDetailsRight"):
                    yield Input(placeholder="Title", classes="HBorder", id="HTitle")
                    yield TextArea(classes="HBorder", id="HDetails")
            with Horizontal(classes="BottomButtons"):
                yield Button("Update", variant="primary", id="Update")
                yield Button("Tidy", variant="primary", id="Tidy")

    def on_mount(self) -> None:
        # Now that DOM is ready, cache the widgets for easier access later on
        # Per screen, since each one may exhibit different widgets
        widget_ids = [
            "TimeSpent", "dec", "inc",
            "TaskStates",
            "HTitle",
            "HDetails",
            "Update",
            "Tidy",
        ]
        self.widgets = {w: self.query_one("#"+w) for w in widget_ids}
        self.table = self.query_one(".TaskList", DataTable)
        # Design touches
        self.table.border_title = "Workbench"
        for label,width in COLUMN_WIDTHS.items():
            self.table.add_column(label=label,width=width,key=label)
        element = self.query(".HBorder")
        for e,t in zip(element, ["Time Spent", "Title", "Details"]):
            e.border_title = t

    def refresh_details(self) -> None:
        # In case of an empty or refilled table
        for w in self.widgets.values():
            w.disabled = (self.table.row_count == 0)
        if self.table.row_count == 0:
            self.widgets["HTitle"].value = "Title"
            self.widgets["TimeSpent"].set_already_spent(0)
            self.widgets["HDetails"].text = "Details"

    def on_screen_resume(self) -> None:
        self.table.clear()
        for data in db.view_dataset(["ACTIVE", "REVIEW", "UPCOMING"]):
            self.table.add_row(*data.as_list(), key=data.ID)
        self.refresh_details()

    @on(DataTable.RowHighlighted, ".TaskList")
    def fill_details(
            self,
            message: DataTable.RowHighlighted
    ) -> None:
        message.stop()
        table = message.control
        self.highlighted_row = message.cursor_row
        record = table.get_row_at(self.highlighted_row)
        self.widgets["TimeSpent"].set_already_spent(record[COLUMNS["TimeSpent"]])
        self.widgets["HTitle"].value = record[COLUMNS["Title"]]
        self.widgets["HDetails"].text = record[COLUMNS["Details"]]

        radioset = self.widgets["TaskStates"]
        buttons = list(radioset.query(RadioButton))
        idx = db.get_states().index(record[COLUMNS["State"]])
        buttons[idx].value = True

    @on(Button.Pressed, "#Update")
    def update_button_pressed(
        self,
        message: Button.Pressed
    ) -> None:
        message.stop()
        # Update TUI with new state, since tied to concrete elements
        spent = float(str(self.widgets["TimeSpent"].renderable))
        self.widgets["TimeSpent"].set_already_spent(spent)
        self.table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["TimeSpent"]),
                                value=spent)
        self.table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Title"]),
                                value=self.widgets["HTitle"].value)
        self.table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["Details"]),
                                value=self.widgets["HDetails"].text)
        radioset = self.widgets["TaskStates"]
        buttons = list(radioset.query(RadioButton))
        idx = radioset.pressed_index
        self.table.update_cell_at(coordinate=Coordinate(row=self.highlighted_row, column=COLUMNS["State"]),
                                value = str(buttons[idx].label))
        # Update underlying database from up to date Datatable
        try:
            act_update_row(table=self.table, row_idx=self.highlighted_row)
        except db.sqlite3.IntegrityError:
            self.app.push_screen(WarningScreen())

    @on(Button.Pressed, "#inc")
    def inc(self):
        points = self.widgets["TimeSpent"]
        value = float(str(points.render())) + 0.5
        points.update(str(value))

    @on(Button.Pressed, "#dec")
    def dec(self):
        points = self.widgets["TimeSpent"]
        value = float(str(points.render())) - 0.5
        if not points.update(str(value)): self.app.bell()

    @on(Button.Pressed, "#Tidy")
    def tidy_button_pressed(
        self,
        message: Button.Pressed
    ) -> None:
        message.stop()
        self.table.clear()
        for data in db.view_dataset(["ACTIVE", "REVIEW", "UPCOMING"]):
            self.table.add_row(*data.as_list(), key=data.ID)
        # Has the potential to clear the entire table
        self.refresh_details()

    @on(DataTable.HeaderSelected, ".TaskList")
    def sort_by_column(
        self,
        message: DataTable.HeaderSelected
    ) -> None:
        message.data_table.sort(message.column_key)


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
                    yield TextArea(classes="HBorder", id="HDetails", disabled=True)
            with Horizontal(classes="BottomButtons"):
                yield Button("Clone to Backlog", variant="primary", id="Clone")

    def on_mount(self) -> None:
        table = self.query_one(".TaskList", DataTable)
        table.border_title = "Archive"
        for label,width in COLUMN_WIDTHS.items():
            table.add_column(label=label,width=width,key=label)
        element = self.query(".HBorder")
        for e,t in zip(element, ["Title", "Details"]):
            e.border_title = t

    def on_screen_resume(self) -> None:
        table = self.query_one(".TaskList", DataTable)
        table.clear()
        for data in db.view_dataset(["CANCELLED", "DONE"]):
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
        self.query_one("#HDetails").text = record[COLUMNS["Details"]]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        table = self.query_one(".TaskList", DataTable)
        act_clone_row(table=table, row_idx=self.highlighted_row)
        table.move_cursor(row=table.row_count - 1)

    @on(DataTable.HeaderSelected, ".TaskList")
    def sort_by_column(
        self,
        message: DataTable.HeaderSelected
    ) -> None:
        message.data_table.sort(message.column_key)


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
    import os.path

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

    # --- Argument validation ------------------------------------------------
    args = parser.parse_args()
    if args.file is not None:
        args.file = os.path.expanduser(args.file)

    # --- Application --------------------------------------------------------
    db.load(args.file)
    app = uTaskerApp()
    app.run()
