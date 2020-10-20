# nftools

These are tools for maniuplating the database used by [NeoFly](https://maugiroe.wixsite.com/neofly), the free bush-pilot addon for MSFS.

## quickstart

If you're in a hurry, put `nftools.exe` anywhere you want.  Then do one of the following:

* `nftools career --source c:\path\to\your\old\common.db` to import your 1.3.4 career to 1.4
* `nftools navdata` to import Little Navmap airport information into NeoFly
* `nftools nograss` to remove airports without a paved runway from the database.

Have fun!

## slightly more detailed usage

Place `nftools.exe` anywhere you want.  You can get basic usage info on the command line with

    nftools --help

This will show you (curently) three subcommands: career, navdata, and nograss.  Each of them has help info available. too.  For example:

    nftools career --help

The only command with a mandatory argument is `career`, which requires a `--source` argument to tell it where the old databse is.   Aside from that this tool will attempt to use the standard paths that Little Navmap and NeoFly use for their databases.  If you wish to work with data in different locations you can see the particular flags for a given command with the above help syntax.

## navdata import

Starting with version 1.3.4, NeoFly uses a local database for airport information.  It ships by default with the stock MSFS airport information.

This is a nice enhancement but it would be cooler to be able to have this actually match your own local scenery database.  Since the schema of the `aircraft` table in NeoFly's database seems to exactly match that of the `aircraft` table created by [navdatareader](https://github.com/albar965/navdatareader/wiki) and [Little NavMap](https://albar965.github.io/littlenavmap.html) this is really easy.

When run with the `navdata` argument, `nftools` will:

* open a navdatareader or Little Navmap created database 
* extract all the airports from it
* open your NeoFly database
* replace all the airports with data extracted from your local scenery
* update a few things for referential consistency

*Note:  right now it seems that most of the NeoFly data uses an airport's ICAO for identification.  The `commercialHub` table has a schema identical to that of `airport`, including an `airport_id` in addition to the ICAO; it is not clear from what Neolord has said if the `airport_id` is actually used for anything or if that is just a remnant of data from the `airport` table.  Regardless, to be safe, this tool will update `commercialHub` so that every airport in there has its `airport_id` updated to match its id in the newly updated `airport` table.  At the time of writing this seems to be the only additional place that `airport_id is used`.*

Note that as a safety measure `nftools` will, by default, refuse to update your NeoFly database if it would be reducing the number of airports present in it, since the assumption is you will be using this to _add_ airports to the stock scenery.  If you do, indeed, want to reduce the number you can force the issue with the `--force` command line argument.

## career import

You caan import your career from NeoFly 1.3.4 into 1.4 with the `career` argument.  This will copy the data from your career, hangar, and log tables from the old database to the new one.  There are a couple of extra transforms that are done along the way:

* the path used for the icon of a mission in the log is converted to the int used by 1.4 for identifying images
* the names of the aircraft in your 1.3.4 hangar are (hopefully) munged into the shorter form that 1.4 uses for substring matching

*Note:  this matching will only work if the names of the aircraft in your old database contain the string that NeoFly 1.4 uses to identify aircraft.  As long as the livery name didn't significantly change the name of the plane from the default this should hopefully always be the case.  If for some reason your favorite livery turns your plane's UI title into "Fred" this conversion won't work.  But neither will the stock 1.4 logic for managing your planes, so that's not a negative.*

## grass runway removal

Since the use of the full MSFS database adds a lot of smaller fields that may not be suitable for larger craft, some folks have wanted to be able to remove any airports that lack paved runways.  The way to do this with full LTM data would be to look at the runway table and join that with airport, but the NeoFly database dosen't have separate runway info.

Instead, we'll just remove any field which doesn't have at least one lit runway.  This seems to work pretty well.  Aftewars we clean up the missions table to make sure that we don't leave any missions to or from airports that don't exist any more.