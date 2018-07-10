set -e

datadir=$1

mkdir -p ${datadir}/tiles

# Build tiles
tippecanoe -f -B 17 -z 17 -Z 10 -r 0 \
    -L sidewalks:${datadir}/sidewalks.geojson \
    -L crossings:${datadir}/crossings.geojson \
    -L elevator_paths:${datadir}/elevator_paths.geojson \
    -e ${datadir}/tiles/pedestrian

cp ${datadir}/pedestrian.json ${datadir}/tiles/pedestrian/tile.json
