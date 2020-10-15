import argparse
import os
import sqlite3
import sys

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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--navdata", action="store", help="path to navdatareader/LNM database"
    )
    parser.add_argument("--neofly", action="store", help="neofly directory location")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Update even if new table has fewer records",
    )
    return parser.parse_args()


def replace_airports(navdata_path, neofly_path, force):
    columnlist = ",".join(COLUMNS)

    print("Reading airport info from source database.")
    with sqlite3.connect(navdata_path) as conn:
        cur = conn.cursor()
        cur.execute(f"select {columnlist} from airport")
        results = cur.fetchall()

    qs = ",".join(["?" for _ in range(len(COLUMNS))])
    with sqlite3.connect(neofly_path) as conn:
        cur = conn.cursor()
        cur.execute("select count(*) from airport")
        old_rows = cur.fetchone()[0]
        new_rows = len(results)
        print(f"Replacing {old_rows} airports with {new_rows}")
        if new_rows < old_rows and not force:
            raise Exception(
                f"Execution would reduce airport count.  Run again with --force if this is wanted."
            )
        cur.execute("delete from airport")
        cur.executemany(f"insert into airport ({columnlist}) values ({qs})", results)
        print("Updating commercialHubs with new airport IDs")
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
        print("Done!")


def main():
    args = parse_args()
    if args.navdata:
        navdata_path = args.navdata
    else:
        navdata_path = os.path.expandvars(
            "%APPDATA%\ABarthel\little_navmap_db\little_navmap_msfs.sqlite"
        )

    print(f"Using {navdata_path} for navdata.")
    if not os.path.exists(navdata_path):
        sys.exit("ERROR: Source path does not exist.")

    if args.neofly:
        neofly_path = os.path.join(args.neofly, "db", "common.db")
    else:
        neofly_path = os.path.join(os.getcwd(), "db", "common.db")

    print(f"Using {neofly_path} for NeoFly.")
    if not os.path.exists(neofly_path):
        sys.exit("ERROR: NeoFly path does not exist.")
        
    try:
        replace_airports(navdata_path, neofly_path, args.force)
    except Exception as exc:
        sys.exit(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
