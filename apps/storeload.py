#!/usr/bin/env python3
"""Store and load Tasks table from uTasker database
"""

# === Imports and Globals ====================================================
import csv
import dataclasses
import os.path
from pathlib import Path

# Database
import database as db


# === Classes and Functions ==================================================

def store_to_csv(dbfile, csvfile):
    with open(os.path.expanduser(Path(csvfile)), "w", newline="") as f:
        db.load(os.path.expanduser(Path(dbfile)))
        writer = csv.DictWriter(f, fieldnames = db.RECORD_FIELD_NAMES)
        writer.writeheader()
        for record in db.view_dataset():
            writer.writerow(record.as_dict())


def load_from_csv(dbfile, csvfile):
    with open(os.path.expanduser(Path(csvfile)), "r", newline="") as f:
        db.load(os.path.expanduser(Path(dbfile)))
        reader = csv.DictReader(f)
        for row in reader:
            del row["ID"]  # auto generated in new database
            rec = db.new_record()  # auto generate ID, and legal with triggers
            rec = dataclasses.replace(rec, **row)
            db.set_record(rec)
        db.store()


# === Command Line Interface =================================================
if __name__ == "__main__":
    import argparse

    desc = __doc__ + '''\n
    Storage format is a simple CSV.

    Tasks IDs are regenerated on loading.
    Loading is possible to existing database, without checking for duplicates.
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
        required = True,
        type = str,
        default = None,
        help = "Path to database file."
    )
    mutex = parser.add_mutually_exclusive_group();
    mutex.add_argument(
        "--store",
        "-s",
        type = str,
        default = None,
        help = "Path to CSV file for storing database."
    )
    mutex.add_argument(
        "--load",
        "-l",
        type = str,
        default = None,
        help = "Path to CSV file for loading into database."
    )

    # --- Argument validation ------------------------------------------------
    args = parser.parse_args()

    # --- Application --------------------------------------------------------
    if args.store:
        store_to_csv(args.file, args.store)
    elif args.load:
        load_from_csv(args.file, args.load)
