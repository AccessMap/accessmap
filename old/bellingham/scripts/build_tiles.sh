set -e

datadir=$1
host=$2

mkdir -p ${datadir}/tiles/tilejson

# Build tiles
tippecanoe -f -B 17 -z 17 -Z 10 -r 0 \
    -L sidewalks:${datadir}/sidewalks.geojson \
    -L crossings:${datadir}/crossings.geojson \
    -e ${datadir}/tiles/pedestrian

cp ${datadir}/pedestrian.json ${datadir}/tiles/tilejson/pedestrian.json

sed -i s,HOSTNAME,${host},g ${datadir}/tiles/tilejson/pedestrian.json
