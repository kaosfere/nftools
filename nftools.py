import click
import os
import sys
import logging
import sqlite3

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

@click.group()
def main():
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
def navdata(neofly, navdata, force):
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

    qs = ",".join(["?" for _ in range(len(COLUMNS))])
    with sqlite3.connect(neofly) as conn:
        cur = conn.cursor()
        cur.execute("select count(*) from airport")
        old_rows = cur.fetchone()[0]
        new_rows = len(results)
        logging.info(f"Replacing {old_rows} airports with {new_rows}.")
        if new_rows == old_rows and not force:
            raise Exception("Execution would reduce airport count.  Run again with --force if this is wanted.")
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
def nograss(neofly):
    if not os.path.exists(neofly):
        raise Exception(f"Unable to find neofly data at '{neofly}")    
    with sqlite3.connect(neofly) as conn:
        cur = conn.cursor()
        cur.execute("select count(*) from airport")
        old_rows = cur.fetchone()[0]
        cur.execute("delete from airport where num_runway_light = 0")
        cur.execute("delete from missions where departure not in (select ident from airport) or arrival not in (select ident from airport)")
        cur.execute("select count(*) from airport")
        new_rows = cur.fetchone()[0]
        logging.info(f"Deleted {old_rows - new_rows} of {old_rows} airports.")
        conn.commit()
        logging.info("Done!") 

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s]: %(message)s")
    try:
        main()
    except Exception as exc:
        logging.fatal(exc)