import csv
import logging
import os
import sqlite3
import sys

import click

COLUMNS = (
    "airport_id",
    "file_id",
    "ident",
    "icao",
    "iata",
    "xpident",
    "name",
    "city",
    "state",
    "country",
    "region",
    "flatten",
    "fuel_flags",
    "has_avgas",
    "has_jetfuel",
    "has_tower_object",
    "tower_frequency",
    "atis_frequency",
    "awos_frequency",
    "asos_frequency",
    "unicom_frequency",
    "is_closed",
    "is_military",
    "is_addon",
    "num_com",
    "num_parking_gate",
    "num_parking_ga_ramp",
    "num_parking_cargo",
    "num_parking_mil_cargo",
    "num_parking_mil_combat",
    "num_approach",
    "num_runway_hard",
    "num_runway_soft",
    "num_runway_water",
    "num_runway_light",
    "num_runway_end_closed",
    "num_runway_end_vasi",
    "num_runway_end_als",
    "num_runway_end_ils",
    "num_apron",
    "num_taxi_path",
    "num_helipad",
    "num_jetway",
    "num_starts",
    "longest_runway_length",
    "longest_runway_width",
    "longest_runway_heading",
    "longest_runway_surface",
    "num_runways",
    "largest_parking_ramp",
    "largest_parking_gate",
    "rating",
    "is_3d",
    "scenery_local_path",
    "bgl_filename",
    "left_lonx",
    "top_laty",
    "right_lonx",
    "bottom_laty",
    "mag_var",
    "tower_altitude",
    "tower_lonx",
    "tower_laty",
    "transition_altitude",
    "altitude",
    "lonx",
    "laty",
)

ICON_MAP = {
    "partner.png": "1",
    "freight.png": "2",
    "mail.png": "3",
    "sensfreight.png": "4",
    "vip.png": "5",
    "secretpax.png": "6",
    "emergency.png": "7",
    "susfreight.png": "8",
    "transit.png": "9",
    "humanitarian.png": "12",
}


@click.group()
def main():
    """Stub function to invoke subcommand processing."""
    pass


@main.command()
@click.option(
    "--neofly",
    help="path to neofly database",
    default=os.path.expandvars("%PROGRAMDATA%\\NeoFly\common.db"),
)
@click.option(
    "--navdata",
    help="path to navdata database",
    default=os.path.expandvars(
        "%APPDATA%\ABarthel\little_navmap_db\little_navmap_msfs.sqlite"
    ),
)
@click.option("--force", help="do it even if airport count would reduce", default=False)
def navdata(neofly: str, navdata: str, force: bool) -> None:
    """Import data from a navdatareader database.

    The NeoFly database uses an airport table with the same schema as that
    used by navdatareader and Little Navmap.  This function will copy the
    data from an LNM-style database into the Neofly DB.
    """
    if not os.path.exists(neofly):
        raise Exception(f"Unable to find neofly data at '{neofly}")

    if not os.path.exists(navdata):
        raise Exception(f"Unable to find navdata at '{navdata}'")

    columnlist = ",".join(COLUMNS)

    logging.info("Reading airport info from source database.")
    with sqlite3.connect(navdata) as conn:
        cur = conn.cursor()
        cur.execute(f"select {columnlist} from airport")
        results = cur.fetchall()

    qs = make_qs(COLUMNS)
    with sqlite3.connect(neofly) as conn:
        cur = conn.cursor()
        cur.execute("select count(*) from airport")
        old_rows = cur.fetchone()[0]
        new_rows = len(results)
        logging.info(f"Replacing {old_rows} airports with {new_rows}.")
        if new_rows < old_rows and not force:
            raise Exception(
                "Execution would reduce airport count.  Run again with --force if this is wanted."
            )
        cur.execute("delete from airport")
        cur.executemany(f"insert into airport ({columnlist}) values ({qs})", results)
        logging.info("Updating commercialHubs with new airport IDs")
        cur.execute(
            """
            update commercialHubs as c 
            set airport_id = (
                select airport_id
                from airport as a
                where c.ident = a.ident
            )
        """
        )
        conn.commit()
        logging.info("Done!")


@main.command()
@click.option(
    "--neofly",
    help="path to neofly database",
    default=os.path.expandvars("%PROGRAMDATA%\\NeoFly\common.db"),
)
def nograss(neofly: str) -> None:
    """Remove non-hard-surfaced airports from the NeoFly database.

    Since the use of the full MSFS database adds a lot of smaller fields
    that may not be suitable for larger craft, some folks have wanted to
    be able to remove any airports that lack paved runways.

    The way to do this with full LTM data would be to look at the runway
    table and join that with airport, but the NeoFly database dosen't have
    separate runway info.

    Instead, we'll just remove any field which doesn't have at least one
    lit runway.  This seems to work pretty well.
    """
    if not os.path.exists(neofly):
        raise Exception(f"Unable to find neofly data at '{neofly}")
    with sqlite3.connect(neofly) as conn:
        cur = conn.cursor()
        cur.execute("select count(*) from airport")
        old_rows = cur.fetchone()[0]
        cur.execute("delete from airport where num_runway_light = 0")
        cur.execute(
            "delete from missions where departure not in (select ident from airport) or arrival not in (select ident from airport)"
        )
        cur.execute("select count(*) from airport")
        new_rows = cur.fetchone()[0]
        logging.info(f"Deleted {old_rows - new_rows} of {old_rows} airports.")
        conn.commit()
        logging.info("Done!")

@main.command()
@click.option(
    "--neofly",
    help="path to neofly database",
    default=os.path.expandvars("%PROGRAMDATA%\\NeoFly\common.db"),
)
@click.option(
    "--career",
    help="name of the career to move HQ",
    required=True,
)
def randomhq(neofly: str, career: str) -> None:
    """Move the chosen career pilot to some random airport where the company
    has at least one owned aircraft not already on a mission.
    """
    import random
    if not os.path.exists(neofly):
        raise Exception(f"Unable to find neofly data at '{neofly}")
    with sqlite3.connect(neofly) as conn:
        cur = conn.cursor()
        # Select all the locations where there are owned aircraft on the ground
        cur.execute(f"SELECT DISTINCT Location from hangar JOIN career ON hangar.owner = career.id WHERE career.name='{career}' AND hangar.status = 0")
        # Get the airport code
        locations = [l[0] for l in cur]
        logging.info(f"Eligible locations: {str(locations)}")
        new_location = random.choice(locations)
        logging.info(f"Chosen location: {new_location}")
        cur.execute(f"UPDATE career SET pilotCurrentICAO = '{new_location}' WHERE career.name='{career}'")
        conn.commit()
        logging.info("Done!")

@main.command()
@click.option("--source", help="path to old neofly database", required=True)
@click.option(
    "--target",
    help="path to new neofly database",
    default=os.path.expandvars("%PROGRAMDATA%\\NeoFly\common.db"),
)
def career(source: str, target: str) -> None:
    """Import an old career into NeoFly 1.4.

    This will copy the data from a NeoFly 1.3.4 database into a database
    for version 1.4.  In the process we do conversions for the images that
    appear in logs and in the way names are stored in the hangar.
    """
    if not os.path.exists(source):
        raise Exception(f"Unable to find source data at '{source}'")

    if not os.path.exists(target):
        raise Exception(f"Unable to find source data at '{target}")

    logging.info("Loading old career.")
    with sqlite3.connect(source) as conn:
        cur = conn.cursor()
        cur.execute("select * from career")
        career = cur.fetchall()
        cur.execute("select * from hangar")
        hangar = cur.fetchall()
        cur.execute("select * from log")
        log = cur.fetchall()

    new_log = []
    for row in log:
        new_row = list(row)
        new_row[1] = ICON_MAP.get((os.path.split(new_row[1])[-1]).lower(), "NONE")
        new_log.append(new_row)

    logging.info("Loading new aircraft data.")
    with sqlite3.connect(target) as conn:
        cur = conn.cursor()
        cur.execute("select aircraft from aircraftData")
        # Sort the list of aircraft by length of name descending
        aclist = sorted([row[0] for row in cur.fetchall()], key=len, reverse=True)

    new_hangar = []
    for row in hangar:
        for item in aclist:
            if item.upper() in row[0].upper():
                new_ac_name = item
                break
        new_row = list(row)
        new_row[0] = new_ac_name
        new_hangar.append(new_row)

    with sqlite3.connect(target) as conn:
        cur = conn.cursor()
        logging.info("Replacing career data.")
        qs = make_qs(career[0])
        cur.execute("delete from career")
        cur.executemany(f"insert into career values ({qs})", career)
        logging.info("Replacing log data.")
        qs = make_qs(new_log[0])
        cur.execute("delete from log")
        cur.executemany(f"insert into log values ({qs})", new_log)
        logging.info("Replacing hangar data.")
        qs = make_qs(new_hangar[0])
        cur.execute("delete from hangar")
        cur.executemany(f"insert into hangar values ({qs})", new_hangar)
        conn.commit()
    logging.info("Done.")

@main.command()
@click.option(
    "--neofly",
    help="path to neofly database",
    default=os.path.expandvars("%PROGRAMDATA%\\NeoFly\common.db"),
)
@click.option(
    "--source",
    help="path to CSV with aircraft data"
)
def aircraft(neofly: str, source: str) -> None:
    """Load new aircraft data from a CSV.

    This will replace the aircraft data in your database with the content of a 
    CSV containing new records.  If none is provided, a default file provided
    by @LostBoii on the NeoFly discord server will be used.

    If creating your own, the CSV must have a header line with a name for each
    columns that matches one from the aircraft table.
    """
    if not os.path.exists(neofly):
        raise Exception(f"Unable to find neofly data at '{neofly}")

    if not source:
        try:
            pwd = sys._MEIPASS
        except (ModuleNotFoundError, AttributeError):
            pwd = os.path.abspath(".")
        source = os.path.join(pwd, "aircraftdata.csv")
        logging.info("Using bundled aircraft data.")
    else:
        logging.info(f"Loading aircraft data from {source}.")

    with open(source, "r") as rawsrc:
        reader = csv.reader(rawsrc)
        header = next(reader)
        qs = make_qs(header)
        row_string = ",".join(header)

        logging.info("Replacing aircraft data.")
        with sqlite3.connect(neofly) as conn:
            cur = conn.cursor()
            cur.execute("delete from aircraftData")
            cur.executemany(f"insert into aircraftData ({row_string}) values ({qs})", reader)
            conn.commit()
    logging.info("Done.")

def make_qs(listname: list) -> str:
    """Create a list of '?'s for use in a query string.

       This is a convenience function that will take a list and return a string
       composed of len(list) queston marks joined by commas for use in an sql
       VALUES() clause.
       
       Args:
           listname: The list to use for generation.
    """
    return ",".join(["?" for _ in range(len(listname))])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s]: %(message)s")
    try:
        main()
    except Exception as exc:
        logging.fatal(exc)
