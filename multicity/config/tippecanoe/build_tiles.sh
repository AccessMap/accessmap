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

# Build areas_served layer
tippecanoe -f -Z 0 -z 14 -B 14 -r 2.5 \
    -L areas:${inputdir}/areas_served.geojson \
    -e ${outputdir}/areas_served

cp /home/tippecanoe/areas_served.json ${outputdir}/tilejson/areas_served.json
sed -i s,HOSTNAME,${host},g ${outputdir}/tilejson/areas_served.json
