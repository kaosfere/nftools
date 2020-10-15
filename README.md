# nftools

These are tools for [NeoFly](https://maugiroe.wixsite.com/neofly), the free bush-pilot addon for MSFS.

## nfimport

Starting with version 1.3.4, NeoFly uses a local database for airport information.  It ships with one by default that the creator, Neolord, says was given to him by @albar965.  He thinks it's just a dump of the standard MSFS navdata but isn't positive.

Regardless of what the original source is, this is a nice enhancement but it would be cooler to be able to have this actually match your own local scenery database.  Since the schema of the `aircraft` table in NeoFly's database seems to exactly match that of the `aircraft` table created by [navdatareader](https://github.com/albar965/navdatareader/wiki) and [Little NavMap](https://albar965.github.io/littlenavmap.html) this is really easy.

The small command line utility `nfimport` will:

* open a navdatareader or Little Navmap created database
* extract all the airports from it
* open your NeoFly database
* replace all the airports with data extracted from your local scenery
* update a few things for referential consistency

*Note:  right now it seems that most of the NeoFly data uses an airport's ICAO for identification.  The `commercialHub` table has a schema identical to that of `airport`, including an `airport_id` in addition to the ICAO; it is not clear from what Neolord has said if the `airport_id` is actually used for anything or if that is just a remnant of data from the `airport` table.  Regardless, to be safe, this tool will update `commercialHub` so that every airport in there has its `airport_id` updated to match its id in the newly updated `airport` table.  At the time of writing this seems to be the only additional place that `airport_id is used`.*

By default, `nfimport` expects to be run from the directory that NeoFly is installed in -- the one with `NeoFly.exe` in it.  If you run it elsewhere you can use the `--neofly` argument to tell it where neofly lives.

It will also attempt to find navdata in the standard location used by Little Navmap.  If you have LNM installed, and have created an MSFS library with it, all you should need to do would be to run `nfimport` from your NeoFly directory and magic will happen.  If it is in a different location, or you have created a standalone database with navdatareader, you can specify its location with the `--navdata` flag.

Note that as a safety measure `nfimport` will, by default, refuse to update your NeoFly database if it would be reducing the number of airports present in it, since the assumption is you will be using this to _add_ airports to the stock scenery.  If you do, indeed, want to reduce the number you can force the issue with the `--force` command line argument.

This has been tested and works on my machine using NeoFly 1.3.4 and both Little Navmap version 2.6.1 and a current version of navdatareader compiled locally, but as always YMMV.  Make a backup of your data before trying anything for the first time.  And always.