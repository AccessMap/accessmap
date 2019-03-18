set -e

inputdir=$1
outputdir=$2
host=$3

mkdir -p ${outputdir}/tilejson

# Build tiles
tippecanoe -f -B 17 -z 17 -Z 10 -r 0 \
    -L transportation:${inputdir}/transportation.geojson \
    -e ${outputdir}/accessmap

cp /home/tippecanoe/accessmap.json ${outputdir}/tilejson/accessmap.json

sed -i s,HOSTNAME,${host},g ${outputdir}/tilejson/accessmap.json
