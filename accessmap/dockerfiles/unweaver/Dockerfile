FROM python:3.6-stretch
MAINTAINER Nick Bolten <nbolten@gmail.com>

ARG GIT_HASH="916e63dd3c10d3827133a98bd65bdd67e6692ca8"

RUN apt-get update && \
    apt-get install -y \
      fiona \
      libsqlite3-mod-spatialite

RUN pip install poetry

RUN mkdir -p /install
WORKDIR /install

# TODO: don't use poetry? It's a bit hacky
RUN git clone https://github.com/nbolten/unweaver.git unweaver

WORKDIR /install/unweaver

RUN git checkout $GIT_HASH \
 && poetry install

RUN poetry add osm-humanized-opening-hours \
  && poetry add pytz


CMD ["poetry", "run", "unweaver"]
