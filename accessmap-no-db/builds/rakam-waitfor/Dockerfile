FROM buremba/rakam

COPY ./wait-for-it.sh .

RUN chmod +x ./wait-for-it.sh

ENTRYPOINT ./wait-for-it.sh $WAITFOR -- rakam/target/rakam-*-bundle/rakam-*/bin/launcher run --config ../config.properties
