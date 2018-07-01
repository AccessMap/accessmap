set -e

datadir=$1
branch=master

mkdir -p ${datadir}/tiles

# Build tiles
tippecanoe -f -B 17 -z 17 -Z 10 -r 0 \
    -L sidewalks:${datadir}/sidewalks.geojson \
    -L crossings:${datadir}/crossings.geojson \
    -L footways:${datadir}/footways.geojson \
    -L stairs:${datadir}/stairs.geojson \
    -e ${datadir}/tiles/paths

tippecanoe -f -B 17 -z 17 -Z 10 -r 0 \
    -L elevators:${datadir}/elevators.geojson \
    -L kerbs:${datadir}/kerbs.geojson \
    -e ${datadir}/tiles/points
