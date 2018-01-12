set -e

datadir=$1

# Fetch the data
curl -L -o ${datadir}/sidewalks.geojson https://raw.githubusercontent.com/accessmap/accessmap-data/master/cities/seattle/data/sidewalk_network.geojson & \
curl -L -o ${datadir}/crossings.geojson https://raw.githubusercontent.com/accessmap/accessmap-data/master/cities/seattle/data/crossing_network.geojson

# Wait for parallelized processes to finish
wait

mkdir -p ${datadir}/tiles

# Build tiles
tippecanoe -f -B 17 -z 17 -Z 12 -r 0 -L sidewalks:${datadir}/sidewalks.geojson -L crossings:${datadir}/crossings.geojson -e ${datadir}/tiles/pedestrian
