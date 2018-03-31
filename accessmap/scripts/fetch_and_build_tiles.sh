set -e

datadir=$1
branch=feature/snakemake

# Fetch the data
curl -L -o ${datadir}/sidewalks.geobuf https://github.com/AccessMap/accessmap-data/raw/$branch/cities/seattle/output/sidewalks_network.geobuf
curl -L -o ${datadir}/crossings.geobuf https://github.com/AccessMap/accessmap-data/raw/$branch/cities/seattle/output/crossings.geobuf
curl -L -o ${datadir}/elevator_paths.geobuf https://github.com/AccessMap/accessmap-data/raw/$branch/cities/seattle/output/elevator_paths.geobuf

# Wait for parallelized processes to finish
wait

mkdir -p ${datadir}/tiles

# Build tiles
tippecanoe -f -B 17 -z 17 -Z 12 -r 0 \
    -L sidewalks:${datadir}/sidewalks.geobuf \
    -L crossings:${datadir}/crossings.geobuf \
    -L elevator_paths:${datadir}/elevator_paths.geobuf \
    -e ${datadir}/tiles/pedestrian
