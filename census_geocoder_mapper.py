#!/usr/bin/env python3
"""census_geocoder

Time constraints
    "addresses take a few minutes to do a batch of 1000"
    --> At this rate, about 3 minutes per 1k, and assuming 1.4 million NFPs
    We have 1.4k batches ... taking 4.2k minutes (~3 days)
    --> If we wanted to do this in one hour, it would take 72 mappers.
        assuming 100 bytes / address ==>  100kB for 1k addreses.
        Plus whatever it takes for a requests object
        => looks like 200 MB or so
        => One AWS small/(micro?) instance could probably all of this.
        => Do not know whethere there is throttling on their end for
           excessive queries from one IP in a time frame (to present DDOS).
           -> Try something human-ish like pausing a second between pulls?
           1.4k batches / 72 machines ~ 20 pulls per machine; no problem?
            (the 72 simultaneous queries may be a problem though)

Output
    Identifier, original address, "Match" or "No_Match"
    and then, if "Match"
    "Exact" or "Not_Exact", found address, lonlat pair, geo, 

"208970676","po box 439465 , chicago, IL, 60643","No_Match"
"363157630","c/of Armetta Keith 8606 S Blackstone Ave, chicago, IL, 60619","Match","Exact","8606 S BLACKSTONE AVE, CHICAGO, IL, 60619","-87.58789,41.738476","605550571","R","17","031","834300","4009"
    

API instructions
    https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.pdf
    https://www2.census.gov/geo/pdfs/maps-data/data/GeocodingURL.pdf

more details
    https://www.census.gov/geo/maps-data/data/geocoder.html
"""
import sys
import time
import requests


ONELINE_URL = 'https://geocoding.geo.census.gov/geocoder/geographies/address'
URL = 'https://geocoding.geo.census.gov/geocoder/geographies/addressbatch'


def get_ein_address(row):
    # EIN, House Number + Street name, City, State, Zip
    indices = (0, 16, 17, 18, 19, 20) #20, 21)  ### TANYA TANYA FIX FIX FIX ###
    alt_indices = (0, 10, 9, 11, 13, 14)
    components = row.split('\t')
    ein, addr1, addr2, city, state, zipcode = [
        components[i].strip() for i in indices
    ]
    addr = ' '.join((addr1, addr2))
    if ('po box' in addr.lower() or
        'p.o. box' in addr.lower() or
        'p o box' in addr.lower() or
        'p. o. box' in addr.lower()
    ):
        ein, addr1, addr2, city, state, zipcode = [
            components[i].strip() for i in alt_indices
        ]
        if len(addr2) > 0:
            addr = ' '.join((addr1, addr2))
        else:
            addr = addr1
    return '"{}","{}","{}","{}","{}"'.format(ein, addr, city, state, zipcode)


def make_query(csv_rows,
        returntype='geographies',
        benchmark='Public_AR_Current', # Public_AR_ACS2016',
        vintage='Current_Current',  #Current_ACS2016'
    ):
    """Prepare the query parameters for the Census Geocoder.

    csv_rows should be a list of string rows that we can '\n'.join()
    This is written to accommodate the piped standard input for a Hadoop streaming process.

    The format of each row is copied here from
    https://www.census.gov/geo/maps-data/data/geocoder.html
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Addresses should be formatted in a single line with comma delimiters.
        The address should consist of:
            Unique ID,
            House Number and Street Name,
            City,
            State,
            ZIP Code

        City and State, or ZIP Code may be left blank, but there must be the
        appropriate number of commas to represent the blank data, for example:
for line in dataset:
            1, 1600 Pennsylvania Ave NW, Washington, DC,
            2, 1600 Pennsylvania Ave NW, , , 20502

        are both valid entries, while:
            3, 1600 Pennsylvania Ave NW, Washington, DC
            4, 1600 Pennsylvania Ave NW, 20502

        are both invalid entries.
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The Unique IDs are our own -- so a database index or an EIN number
    (for the not-for-profits lookup project)

    For all benchmark names:
        https://geocoding.geo.census.gov/geocoder/benchmarks
    For all benchmark IDs:
        https://geocoding.geo.census.gov/geocoder/vintages?benchmark=benchmarkId. 
        (Defaults to current vintage if unspecified, and must match the benchmark name...)
    For all layer IDs:
        https://tigerweb.geo.census.gov/ArcGIS/rest/services/TIGERweb/tigerWMS_Current/MapServer
    """
    parsed_rows = [get_ein_address(row) for row in csv_rows]
    return (
        {'addressFile': ('input.csv', '\n'.join(parsed_rows), 'text/csv', {'Expires': '0'})},
        dict(
            benchmark=benchmark,
            vintage=vintage,
            layers='16,18,20',  # The 'layers' actually has no effect. Don't know why I'm keeping it.
        )
    )


def make_onerow_query(
        street='1 Elvis Presley Blvd.',
        city='Memphis',
        state='TN',
        zip='38116',
        benchmark='Public_AR_Current',  #'Public_AR_ACS2016',
        vintage='Current_Current',  #'Census2010_ACS2016',
        layers=(
            '2016 State Legislative Districts - Lower,'
            '2016 State Legislative Districts - Upper,'
            '115th Congressional Districts,'
            'Unified School Districts,Secondary School Districts,Elementary School Districts,'
            'County Subdivisions'
        ) #'10,14,16,18,22,54,56,58',
    ):
    """
    Return a formatted query to send to the Census API.

    See 'https://www.census.gov/geo/maps-data/data/geocoder.html' for more details
    about what values the query parameters can take.

    For all benchmark names:
        https://geocoding.geo.census.gov/geocoder/benchmarks
    For all benchmark IDs:
        https://geocoding.geo.census.gov/geocoder/vintages?benchmark=benchmarkId. 
        (Defaults to current vintage if unspecified, and must match the benchmark name...)
    For all layer IDs:
        https://tigerweb.geo.census.gov/ArcGIS/rest/services/TIGERweb/tigerWMS_Current/MapServer
    """
    return dict(
        street=street,
        city=city,
        state=state,
        zip=zip,
        benchmark=benchmark,
        vintage=vintage,
        layers=layers,
        format='json'
    )



def map():
    column_names = (
        'id', 'orig_address', 'match_or_not', 'exact_or_not', 'matched_address',
        'lat_lon', 'tiger_line_id', 'side_of_street',
        'state_fips', 'county_fips', 'census_tract', 'census_block'
    )
    lines = []
    print(','.join(column_names))
    for line in sys.stdin:
        if len(line.strip()) == 0 or line.startswith('EIN'):
            continue  # skip the header
        line = line.strip()
        lines.append(line)
        if len(lines) == 1000:  # up to 1000 at a time
            files, query = make_query(lines)
            lines = []
            response = requests.post(URL, files=files, params=query)
            print(response.text)
    # finish
    files, query = make_query(lines)
    response = requests.post(URL, files=files, params=query)
    for row in response.text.split('\n'):
        if 'No_Match' not in row:
            print(row)
    sys.stderr.write('Finished\n')


if __name__ == '__main__':
    map()
