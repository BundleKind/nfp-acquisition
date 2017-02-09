import csv
import glob
import json
import os
import yaml
from collections import Counter


nfp_names = {}  # Map the EIN number to the business name
missions = {}  # Map the EIN number to the mission statement(s)


# We will also want a future lookup of state + city --> EIN
ein_state_city = {}

def get_city(path):
    return os.path.basename(path)[:-4]


# Go through all of the entries from all of the Form 990 tax forms.
# We want
#  - the EIN number (to identify the business)
#  - their business name (because sometimes that's all there is)
#  - their mission statement(s)
state_paths = glob.glob(os.path.join('data', 'form990', '*'))
for dirname in state_paths:
    cities_990 = glob.glob(os.path.join(dirname, '*'))
    # Set up to collect all of the EINs in a given state and city.
    state_abbr = os.path.basename(dirname)
    ein_state_city[state_abbr] = {}

    for fname in cities_990:
        city = get_city(fname)
        ein_state_city[state_abbr][city] = []
        with open(fname) as infile:
            rdr = csv.reader(infile, delimiter='\t')
            nfp_names_etc = [
                (row[0], row[2], row[27], row[-1], row[-2])
                for row in rdr
            ]
            nfp_names.update(dict(entry[:2] for entry in nfp_names_etc))
            missions.update(dict(
                    (entry[0], '  '.join(set(entry[1:])))  # remove duplicates
                    for entry in nfp_names_etc
            ))
            ein_state_city[state_abbr][city].extend(
                [row[0] for row in nfp_names_etc]
            )

# Also go through the Form 990N tax forms.
state_paths = glob.glob(os.path.join('data', 'form990N', '*'))
for dirname in state_paths:
    state_abbr = os.path.basename(dirname)
    if state_abbr not in ein_state_city:
        ein_state_city[state_abbr] = {}
    cities_990 = glob.glob(os.path.join(dirname, '*'))
    for fname in cities_990:
        city = get_city(fname)
        if city not in ein_state_city[state_abbr]:
            ein_state_city[state_abbr][city] = []
        with open(fname) as infile:
            rdr = csv.reader(infile, delimiter='\t')
            ein_to_name = dict((row[0], row[2]) for row in rdr)
            nfp_names.update(ein_to_name)
            # Missions too (use the name as the mission for 990Ns)...
            missions.update(ein_to_name)
            ein_state_city[state_abbr][city].extend(ein_to_name.keys())


del missions['']  # There was an empty EIN somewhere


#-------------------------------------------------------------------- Tagging
# Read in the YAML tags file
tags_path = 'all_tags.yml'
tags = yaml.load(open(tags_path).read())

tagged_missions = {}
unmatched = 0
no_mission = 0
for ein, mission in missions.items():
    if len(ein) == 0:  # Skip the ones wihout eins
        continue
    tagged_missions[ein] = []
    lower_mission = mission.lower()
    if len(lower_mission) == 0:
        no_mission += 1
        continue
    for tag, matchers in tags.items():
        for m in matchers:
            if m in lower_mission:
                tagged_missions[ein].append(tag)
                break
    if len(tagged_missions[ein]) == 0:
        unmatched += 1



#-------------------------------------------------------------------- Output
msg = '{} out of {} missions remain unmatched'
print(msg.format(unmatched, len(tagged_missions)))
print('{} missions have no statement at all'.format(no_mission))


# Make all directories if they don't exist
def setup_path(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


# Write JSON objects containing the EINS and tags to file.
# Directory structure:
#   . tagged_eins
#   |-- <state-abbr>
#     |-- <city>.json
directory = os.path.join('data', 'tagged_eins')
setup_path(directory)
for state, city_lookups in ein_state_city.items():
    subdir = os.path.join(directory, state)
    setup_path(subdir)
    for city, selected_eins in city_lookups.items():
        eins_destination = os.path.join(subdir, city + '.json')
        tagged_subset = dict(
            (k, v) for k, v in tagged_missions.items()
            if k in selected_eins
        )
        with open(eins_destination, 'w') as outfile:
            outfile.write(json.dumps(tagged_subset))


#---------------------------------------------- Quick performance assessment
tag_counts = Counter(
        [tag for tag_list in tagged_missions.values()
         for tag in tag_list]
    )

total_missions = len(tagged_missions)
print('Total nonprofits classified: ', total_missions)
for entry in tag_counts.most_common():
    tag, count = entry
    print('{:<14}'.format(tag), end='  ')
    print('{:2.0f}% ({})'.format(100 * count / total_missions, count))

print('Done.\n')
