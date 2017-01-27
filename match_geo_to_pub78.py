import difflib
import glob
import os
import re

from collections import namedtuple
City = namedtuple('City', ['name', 'path', 'num_charities'])


def count_charities(fname):
    i = 0
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i


def get_city_name(fname, matcher=re.compile('(?<=/)[\.\w]+(?=.txt)')):
    name_with_underscores = matcher.search(fname).group()
    return re.sub('_', ' ', name_with_underscores)


def get_lon_lat_path(state):
    path = os.path.join('data', 'census_places_lon_lat', state + '.txt')
    if not os.path.exists(path):
        return None
    else:
        return path


def find_correctly_spelled_city(test_city, cities):
    test = test_city.lower()
    split_city_name = test.split(' ', 1)
    if len(split_city_name) > 1:
        first_word, remainder = split_city_name
        if len(first_word) < 3:
            directions = {
                ('n', 'n.'): 'north',
                ('s', 's.'): 'south',
                ('w', 'w.'): 'west',
                ('e', 'e.'): 'east',
            }
            for abbr, direction in directions:
                if first_word in abbr:
                    test = ' '.join((direction, remainder))
    match = difflib.get_close_matches(test, cities.keys(), n=1, cutoff=0)[0]
    score = difflib.SequenceMatcher(None, test, match).ratio()
    if not test.startswith(match[0]) and not match.startswith('new'):
        # how can they typo the first character?
        return test_city
    elif score < 0.79:
        return test_city
        #message = (
        #    'In searching for {} we found: {} (with score {})\n'
        #    'Type 1 to use the original, 2 to use the match, or else\n'
        #    'type in the actual correct city name\nResponse: '
        #)
        #result = input(message.format(test_city, cities[match], score))
        #if result == '1':
        #    print('OK. using {}'.format(test_city))
        #    return test_city
        #elif result == '2':
        #    print('OK. using {}'.format(cities[match]))
        #    return cities[match]
        #else:
        #    print('Using {}'.format(result))
        #return result
    else:
        return cities[match]


def make_city_lookup(path, sep='\t'):
    lookup = {}
    with open(path) as geofile:
        next(geofile)  # discard the header row
        try:
            for row in geofile:
                city_place, __ = row.split(sep, 1)
                city = city_place.rsplit(' ', 1)[0]
                lookup[city.lower()] = city
        except:
            print("row that failed:", row)
    return lookup
            
        

# There are two things we want to do in this loop:
#  (1) Match up the geolocation of cities to the correct tax file
#  (2) Write this mapping out to a file
city_mappings = os.path.join('data', 'pub78_to_census')
if not os.path.exists(city_mappings):
    os.mkdir(city_mappings)

state_paths = glob.glob(os.path.join('data', 'pub78', '*'))
    for sp in state_paths:
        state = os.path.basename(sp)
        lon_lat_path = get_lon_lat_path(state)
        if not lon_lat_path:
            continue  # Probably a territory or something
        city_lookup = make_city_lookup(lon_lat_path)
        tentative_tax_to_geo_cities = {}
        for p in glob.glob(os.path.join(sp, '*')):
            city_name = get_city_name(p)
            correct_city_name = find_correctly_spelled_city(city_name, city_lookup)
            tentative_tax_to_geo_cities[city_name] = correct_city_name
        with open(os.path.join(city_mappings, state + '.txt'), 'w') as outfile:
            outfile.write('pub78_name\tmapped_name\n')
            outfile.write('\n'.join(
                '{}\t{}'.format(k, v)
                for k, v in tentative_tax_to_geo_cities.items()
            ))

# ---
# NOTE: I am abandoning this as unhelpful as of 1/25/2017 -- Tanya
