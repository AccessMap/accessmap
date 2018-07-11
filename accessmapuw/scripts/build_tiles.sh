set -e

datadir=$1
host=$2

mkdir -p ${datadir}/tiles/tilejson

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

cp ${datadir}/paths.json ${datadir}/tiles/tilejson/paths.json
cp ${datadir}/points.json ${datadir}/tiles/tilejson/points.json

sed -i s,HOSTNAME,${host},g ${datadir}/tiles/tilejson/paths.json
sed -i s,HOSTNAME,${host},g ${datadir}/tiles/tilejson/points.json
