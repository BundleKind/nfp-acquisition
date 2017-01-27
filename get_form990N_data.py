#!/usr/bin/env python3
"""Pull the current 990-N (nonprofit < $25k) list from the IRS.
"""
import csv
import difflib
import glob
import io
import os
import re
import urllib.request
import zipfile

def get_city_or_state_name(fname, matcher=re.compile('(?<=/)[\.\w]+(?=.txt)')):
    name_with_underscores = matcher.search(fname).group()
    return re.sub('_', ' ', name_with_underscores)

# This dataset is updated weekly
# https://apps.irs.gov/app/eos/forwardToEpostDownload.do
data_url = 'https://apps.irs.gov/pub/epostcard/data-download-epostcard.zip'
response = urllib.request.urlopen(data_url)
buffered_zipfile = io.BytesIO()
chunk = response.read(16384)
while chunk:
    buffered_zipfile.write(chunk)
    chunk = response.read(16384)

print("Got the dataset")
z = zipfile.ZipFile(buffered_zipfile)
fname = z.namelist()[0]
epostcard = io.StringIO(z.open(fname).read().decode('utf-8'))

# Layout is pipe-separated, defined here:
# https://apps.irs.gov/app/eos/forwardToEpostDownloadLayout.do
header = [
    'EIN',
    'Tax Year',
    'Organization Name',
    'Gross Receipts are Under $25k',
    'Is Terminated',
    'Tax Period Begins',
    'Tax Period Ends',
    'Website URL',
    'Officer Name',
    'Officer Address Line 1',
    'Officer Address Line 2',
    'Officer Address City',
    'Officer Address Province',
    'Officer Address State',
    'Officer Address Postal Code',
    'Officer Address Country',
    'Organization Address Line 1',
    'Organization Address Line 2',
    'Organization Address City',
    'Organization Address Province',
    'Organization Address State',
    'Organization Address Postal Code',
    'Organization Address Country',
    'Doing Business As Name 1',
    'Doing Business As Name 2',
    'Doing Business As Name 3'
]

state_idx = header.index('Organization Address State')  # 20
country_idx = header.index('Organization Address Country')  # 22
city_idx = header.index('Organization Address City')  # 18

## Use the census city lat, lon data to get correct spellings
#correctly_spelled_cities = {}
#for lon_lat_path in glob.glob(os.path.join('data', 'census_places_lon_lat', '*')):
#    state = get_city_or_state_name(lon_lat_path)
#    correctly_spelled_cities[state] = {}
#    with open(lon_lat_path) as geofile:
#        next(geofile)  # skip header
#        for line in geofile:
#            city, __, __ = line.strip().split('\t')
#            city = city.rsplit(' ', 1)[0]
#            correctly_spelled_cities[state][city.lower()] = city
#
#print("loaded the spellchecker (haha)")

# Separate out by state and city
counter = 0
by_state = {}
rdr = csv.reader(epostcard, delimiter='|', quotechar=None)
for row in rdr:
    if len(row):
        state = row[state_idx]
        if state not in ('NY', 'IL', 'GA', 'WA', 'MI', 'MT'):
            continue
        counter += 1
        if counter % 200 == 0:
            print(counter//200)
        original_city = row[city_idx]
        city = original_city
        ## Try to fix misspelled city
        #if state in correctly_spelled_cities:
        #    matches = difflib.get_close_matches(
        #        original_city.lower(),
        #        correctly_spelled_cities[state].keys(),
        #        n=1
        #    )
        #    if matches and matches[0][0] == original_city[0].lower():
        #        city = correctly_spelled_cities[state][matches[0]]
        if state not in by_state:
            by_state[state] = {}  # initialize
        if city not in by_state[state]:
            by_state[state][city] = []  # initialize
        by_state[state][city].append(row)


form990N = os.path.join('data', 'form990N')
if not os.path.exists(form990N):
    os.makedirs(form990N)

for state, by_city in by_state.items():
    if not state:
        continue  # Foreign charities have nan empty 'state' field
    state_dir = os.path.join(form990N, state)
    if not os.path.exists(state_dir):
        os.makedirs(state_dir)

    for city, data in by_city.items():
        fname = 'no_city.txt' if not city else city + '.txt'
        with open(os.path.join(state_dir, fname), 'w') as csvfile:
            city_writer = csv.writer(csvfile, delimiter='\t')
            city_writer.writerow(header)
            city_writer.writerows(data)
