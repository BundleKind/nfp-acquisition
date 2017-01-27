#!/usr/bin/env python3
"""Get the current list of pub78 (nonprofit) organizations from the IRS,
and store them in `data/pub78/<State Abbr.>/<City Name>.txt`

These are split out from a single zipped file at:
https://apps.irs.gov/pub/epostcard/data-download-pub78.zip

    File output format is tab-separated: EIN\tLegal Name\tDeductibility status
"""
import csv
import io
import os
import re
import urllib.request
import zipfile


data_url = 'https://apps.irs.gov/pub/epostcard/data-download-pub78.zip'
response = urllib.request.urlopen(data_url)
buffered_zipfile = io.BytesIO()
chunk = response.read(16384)
while chunk:
    buffered_zipfile.write(chunk)
    chunk = response.read(16384)

z = zipfile.ZipFile(buffered_zipfile)
fname = z.namelist()[0]
pub78 = io.StringIO(z.open(fname).read().decode('utf-8'))

# Layout is pipe-separated, defined here:
#  https://apps.irs.gov/app/eos/forwardToPub78DownloadLayout.do
rdr = csv.reader(pub78, delimiter='|')
header = [
    'EIN',
    'Legal Name',
    'City',
    'State',
    'Country',
    'Deductibility Status Description'
]
header_minus_extraneous = header[:2] + header[-1:]

# Separate out by state and city
by_state = {}
for row in rdr:
    if len(row):
        country = row.pop(4)  # Always 'United States'
        state = row.pop(3)
        city = re.sub(' ', '_', row.pop(2))
        if state not in by_state:
            by_state[state] = {}  # initialize
        if city not in by_state[state]:
            by_state[state][city] = []  # initialize
        by_state[state][city].append(row)


pub78 = os.path.join('data', 'pub78')
if not os.path.exists(pub78):
    os.makedirs(pub78)


for state, by_city in by_state.items():
    if not state:
        continue  # Foreign charities have nan empty 'state' field

    state_dir = os.path.join(pub78, state)
    if not os.path.exists(state_dir):
        os.makedirs(state_dir)

    for city, data in by_city.items():
        fname = 'no_city.txt' if not city else city + '.txt'
        with open(os.path.join(state_dir, fname), 'w') as csvfile:
            city_writer = csv.writer(csvfile, delimiter='\t')
            city_writer.writerow(header_minus_extraneous)
            city_writer.writerows(data)
