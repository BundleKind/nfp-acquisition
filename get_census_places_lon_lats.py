#!/usr/bin/env python3
"""Get lon, lat pairs for all U.S. Census places (cities, towns, etc.)
from the Census Gazetteer data, placing them in the directory
`data/census_places_lon_lat/`, separated by two character state (or territory)
abbreviation.

    File output format is tab-separated: city\tlon\tlat.
"""
import csv
import io
import os
import urllib.request
import zipfile


data_url = (
    'http://www2.census.gov/geo/docs/maps-data/data/gazetteer/'
    '2016_Gazetteer/2016_Gaz_place_national.zip'
)
response = urllib.request.urlopen(data_url)
buffered_zipfile = io.BytesIO()
chunk = response.read(16384)
while chunk:
    buffered_zipfile.write(chunk)
    chunk = response.read(16384)

z = zipfile.ZipFile(buffered_zipfile)
fname = z.namelist()[0]
gaz = io.StringIO(z.open(fname).read().decode('latin-1'))

rdr = csv.reader(gaz, delimiter='\t')
header = [h.strip() for h in next(rdr)]
entries = [[r.strip() for r in row] for row in rdr]
locations = {}
for e in entries:
    state = e[0]
    city = e[3].rsplit(' ', 1)[0]
    lon = e[-1]
    lat = e[-2]
    if state not in locations:
        locations[state] = [[city, lon, lat]]
    else:
        locations[state].append([city, lon, lat])

census_places_lon_lat = os.path.join('data', 'census_places_lon_lat')
if not os.path.exists(census_places_lon_lat):
    os.makedirs(census_places_lon_lat)

for state, data in locations.items():
    fname = state + '.txt'
    with open(os.path.join(census_places_lon_lat, fname), 'w') as csvfile:
        state_writer = csv.writer(csvfile, delimiter='\t')
        state_writer.writerow(('city', 'lon', 'lat'))
        state_writer.writerows(data)
