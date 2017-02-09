# Overview

The list of registered nonprofits in the U.S. is public data, as are their tax returns.
This repository provides code to acquire a current list of nonprofits and their tax returns.


## Steps

1. Use `get_pub78_data.py` to pull the
    pub78 data to map EIN to city:
    and place them in `./data/pub78/
    This will make it possible for us only choose EINs
    from specifically desired cities.

2. Pull the data from the tax forms; there are different
   datasets for smaller and for larger organizations:
   `get_form990N_data.py` will pull the data for smaller organizations
   `get_aws_990_data.py` will pull the data for larger organizations.
   Column output will overlap, with the 990 data containing additional
   columns after the ones that exist in the 990N data.
   Data will be placed in `./data/form990N/` and `./data/form990/`
    - The form 990 N data are in a zipped text file, so that is easy to get.
    - The form 990 data are in XML files, stored in Amazon's S3 service.
      You can get the data directly with a `curl` command, for example
      from this URL:
      https://s3.amazonaws.com/irs-form-990/201541349349307794_public.xml
    - There are index files that map the EIN number of a charity to the URL
      of its tax return.
      You need to have an Amazon AWS account and have installed the
      AWS Command Line Interface https://aws.amazon.com/cli/ to get the
      initial lookups. Details are at the top of the script `get_aws_990_data.py`.
      But eventually the goal is to change to the boto3 library and automate
      what's currently done using the CLI.

3. In case people want to map these locations, use the US
  [Census Geocoder web service][usgeo] to run through all of the
  locations and map them individually to lon,lat positions.
  The script `census_geocoder_mapper.py` provides a way.
  We just need to pipe the output from the form 990/990N data into the
  mapper and it will select the appropriate fields and then send them along
  to the geocoder query.<br/>
  Use `run_geocoder_mapper.sh` (sorry Windows people, I didn't check whether
  it works in powershell) to automate this.

4. Try and group nonprofits by their mission.
   - There is no mission information in the 990N data, so we can only
     infer from the group name.
   - There are three fields in the 990 data that may be helpful.
   Pull them, cluster, and see what we get.

  This was done in the notebook `cluster_missions.ipynb`, which output the
  mappings as individual JSON-formatted files in _data/tagged_eins/_.
  There is also and a mapping of all terms to their tags in _data/tagged_eins/all_tags.yml_.
  Edit the _all_tags.yml_ file and run `retag_everything.py` to
  retag everything.

5. Combine the tax data, location data, and tag data into a single SQLite
   database.  The script is: `create_and_populate_database.py`



## Abandonded scripts

*  Use `get_census_places_lon_lats.py` to
   pull the US Census places data
   and place them in `./data/census_places_lon_lat/`

*  There are misspelled cities in the pub78 data.
  `match_geo_to_pub78.py` maps the cities in the tax forms to
  place names in the census, or keeps the city name as is.
  Mappings are placed in `./data/pub78_to_census/<State-abbr>.txt`


[usgeo]: https://geocoding.geo.census.gov/geocoder/geographies/addressbatch
