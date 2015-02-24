#!/usr/bin/env sh

mkdir fips10c
pushd fips10c
wget http://efele.net/maps/fips-10/map/fips10c.zip
unzip fips10c.zip
popd

mkdir tz_world
pushd tz_world
wget http://efele.net/maps/tz/world/tz_world.zip
unzip tz_world.zip
popd

mkdir cities
pushd cities
wget http://legacy.jefferson.kctcs.edu/techcenter/gis%20data/World/Zip/cities.zip
unzip cities.zip
popd

mkdir output
pushd output
unzip ../map.zip
popd
