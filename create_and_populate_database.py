import csv
import glob
import json
import os
import sqlite3
import yaml

from nonprofitdb_insertion_statements import insertions

DBNAME = 'nonprofits.db'
conn = sqlite3.connect(DBNAME)
c = conn.cursor()
create_statements = open('create_nonprofitdb_statements.sql').read()
for stmt in create_statements.split("\n\n"):
    c.execute(stmt)
conn.commit()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Form 990/990N Data
print("Loading the Form 990/990N data.")
city_paths = glob.glob(os.path.join('data', 'form990*', '*', '*'))
queries = insertions['statements']
cols = insertions['columns']

def process_tax_return(row):
    result = []
    for c in cols['tax_return']:
        if c in cols['tax_return_cast_to_int']:
            result.append(1 if row.get(c, '') else 0)
        else:
            result.append(row.get(c, ''))
    return result

for fname in city_paths:
    with open(fname) as infile:
        rdr = csv.DictReader(infile, delimiter='\t')
        dataset = [row for row in rdr]
    c.executemany(
        queries['nfp'],
        [[row.get(c, '') for c in cols['nfp']] for row in dataset]
    )
    c.executemany(
        queries['year_terminated'],
        [(row.get('EIN'), int(row.get('TaxYr', 2015))) for row in dataset
            if row.get('Is Terminated') == 'T' and row.get('EIN')
        ]
    )
    c.executemany(
        queries['tax_return'],
        [process_tax_return(row) for row in dataset
            if row.get('Is Terminated') != 'T'
        ]
    )
    c.executemany(
        queries['latest_contact_info'],
        [[row.get(c, '') for c in cols['latest_contact_info']] for row in dataset
            if row.get('Is Terminated') != 'T'
        ]
    )


conn.commit()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Geo (lon, lat) Data
print("Loading the Geo (longitude, latitude) data.")
city_paths = glob.glob(os.path.join('data', 'geo990*', '*', '*'))
query = queries['latest_contact_info_geo_update']
def row_to_lon_lat(row):
    ein = row.get('id')
    lon_lat = row.get('lon_lat')
    if lon_lat is not None:
        lon, lat = [float(deg) for deg in lon_lat.split(',')]
    else:
        lon = lat = None
    return lon, lat, ein

for fname in city_paths:
    with open(fname) as infile:
        rdr = csv.DictReader(infile)
        for row in rdr:
            c.execute(query, row_to_lon_lat(row))
            
conn.commit()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Tags
print("Loading the tags.")
query = queries['tag']
all_tags = yaml.load(open(os.path.join('data', 'tagged_eins', 'all_tags.yml')).read())
c.executemany(query, [(k,) for k in all_tags.keys()])
conn.commit()

query = queries['tag_lookup']
city_paths = glob.glob(os.path.join('data', 'tagged_eins', '*', '*.json'))
for fname in city_paths:
    data = json.loads(open(fname).read())
    del data['EIN']  # TODO: fix the reason this exists...apparently tagged header too
    for ein, tags in data.items():
        for t in tags:
            c.execute(query, (ein, t))

conn.commit()
print("Done. database is in {}".format(DBNAME))
