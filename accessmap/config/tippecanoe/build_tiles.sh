set -e

inputdir=$1
outputdir=$2
host=$3

mkdir -p ${outputdir}/tilejson

# Build unified tileset where each layer has different settings - e.g. zoom info.

# Build pedestrian network layer
tippecanoe -f -Z 6 -z 14 -B 14 -r 2.5 \
    -L transportation:${inputdir}/transportation.geojson \
    -e ${outputdir}/pedestrian

cp /home/tippecanoe/pedestrian.json ${outputdir}/tilejson/pedestrian.json
sed -i s,HOSTNAME,${host},g ${outputdir}/tilejson/pedestrian.json

# Build regions layer
tippecanoe -f -Z 0 -z 14 -B 14 -r 2.5 \
    -L region:${inputdir}/regions.geojson \
    -e ${outputdir}/regions

cp /home/tippecanoe/regions.json ${outputdir}/tilejson/regions.json
sed -i s,HOSTNAME,${host},g ${outputdir}/tilejson/regions.json
