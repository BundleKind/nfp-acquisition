#!/bin/bash

echo '\nThis takes a while...\n'

IFS=$'\n'
mkdir -p data/geo990N
for f in `ls -1d data/form990N/*`
do
    st=`echo $f | cut -f 3 -d "/"`
    echo "\nthe state is $st"
    for ff in `ls -1 $f/*.txt`
    do
      city=`echo "${ff}" | cut -f 4 -d "/"`
      echo "the city is $city"
      mkdir -p data/geo990N/${st}
      cat "${ff}" | python census_geocoder_mapper.py > "data/geo990N/${st}/${city}"
    done
    sleep 1
done
echo '\nDone with 990N datasets\n'


mkdir -p data/geo990
for f in `ls -1d data/form990/*`
do
    st=`echo $f | cut -f 3 -d "/"`
    echo "the state is $st"
    for ff in `ls -1  $f/*.txt`
    do
      city=`echo "${ff}" | cut -f 4 -d "/"`
      echo "the city is $city"
      mkdir -p data/geo990/${st}
      cat "${ff}" | python census_geocoder_mapper.py > "data/geo990/${st}/${city}"
    done
    sleep 1
done
echo 'Done with 990 datasets'
