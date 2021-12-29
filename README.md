# AccessMap

This repo contains all of the infrastructure needed to create and run AccessMap except
for the data, which can be generated using the `opensidewalks-data` repo. These are the
AccessMap-specific software projects used to deploy AccessMap:

- [AccessMap Web App (React-based)](https://github.com/accessmap/accessmap-webapp)

- [`unweaver`: our flexible routing engine](https://github.com/nbolten/unweaver)

- [AccessMap Users API](https://github.com/accessmap/accessmap-api)

- [AccessMap Data ETL Pipeline (to get data)](https://github.com/accessmap/accessmap-data)

The full pipeline of how AccessMap is deployed can be seen in this diagram:

![AccessMap orchestration diagram](orchestration-diagram.png)

## Deployment strategy

*Important: outside of deploying Rakam, all of the following steps sould be
executed in the `accessmap/` subdirectory of this repository.*

AccessMap is currently deployed using `docker-compose`, so the documentation
will assume some familiarity with the command line and `docker`. It uses the
relatively recent `docker-compose` config version 3.8 or above, which requires
a newer version of the `docker-compose` CLI (it is developed using version
1.29).

AccessMap uses a 3-stage development-staging-production workflow, wherein new
ideas can be tested out in feature branches, merged to develop, tested on a
staged copy of the production application, and finally released:

- New features/branches are developed within each separate repository and
tested against a deployment of this repository.

- Once a given feature or branch is mature, a tagged release is made for that
service's repository.

- This repository may be updated to refer to those releases as part of internal
testing and development. This happens on the `develop` branch of this
repository.

- When we are ready to release a new version of AccessMap to the public, we
merge the `develop` branch into `master` and tag a new release of this
repository. Therefore, the latest tagged release on the `master` branch always
reflects the code running on www.accessmap.io.

If you are running your own deployment of AccessMap, you can, of course, follow
any release strategy that you prefer and build from any version of our
services, but this is the primary workflow around which we have designed this
repository.

## Configuration

An AccessMap deployment is configured by (1) environment variables and (2)
networkable pedestrian network feature data.

### Environment variables

AccessMap uses environment variables to configure its deployments to maximize
portability and follow best practices. These environment variables can be set
in a number of ways according to the
[`docker-compose` documentation](https://docs.docker.com/compose/environment-variables/),
but the easiest is to use an environment file. We provide a template
environment file, `accessmap.env.sample`, that should be copied to
`accessmap.env` and can be edited to your needs. The included sample
environment file documents the purpose and meaning of each environment
variable.

### Pedestrian network data

AccessMap requires two data files in the `data/` directory:
`transportation.geojson` and `regions.geojson`. The data used by AccessMap can
be generated from scratch using this repository:
https://github.com/opensidewalks/opensidewalks-data.

#### `transportation.geojson`

This should be a GeoJSON file formatted according to the OpenSidewalks Schema
spec: https://github.com/OpenSidewalks/OpenSidewalks-Schema.
[Our data pipeline](https://github.com/OpenSidewalks/OpenSidewalks-Schema)
generates GeoJSON data that conforms to this spec.

The data in such a file will be LineString features representing pedestrian
pathways as well as metadata that describe them. Where they meet end-to-end,
AccessMap's routing engine (Unweaver) will network them together.

#### `regions.geojson`

This should be a GeoJSON file containing Polygons of service areas. Each
Feature should have these properties defined:

- `key`: A unique string by which the region will be tracked within the web
application. For example, Seattle's key is `wa.seattle`.

- `name`: A human-readable name for the region. This should be kept short, as
the UI does not yet adapt well to long names.

- `bounds`: An array of `[West, South, East, North]` coordinates that describe
the bounding box of the region.

- `lon`: The preferred longitude of the map view starting location for the
region.

- `lat`: The preferred latitude of the map view starting location for the
region.

- `zoom`: The preferred map zoom level of the map view starting at the region.

[Our data pipeline](https://github.com/OpenSidewalks/OpenSidewalks-Schema)
generates a combined regions.geojson file that conforms to this spec.

## Running a deployment

### Configuration

#### QuickStart

See the section on setting up the `accessmap.env` file above.

### Building assets

#### Quickstart

Run these three commands:
    docker-compose run build_webapp
    docker-compose run build_tiles
    docker-compose run build_router

#### Explanation

Several assets must be built before deployment: (1) The web application must
be transpiled and optimized, (2) map vector tiles must be built from the
input GeoJSON files, and (3) the routable graph must be built from
`transportation.geojson`.

These can be built using `docker-compose run <service>`, where `<service>` is
the build container name. The build container names are, `build_webapp`,
`build_tiles`, and `build_router`, so `docker-compose run build_webapp` will
build the assets for the AccessMap `webapp` container. As an alternative, it
is also possible to start the service *and* build containers using the `build`
profile: `docker-compose --profile build up`. Note that the build steps take
time, so it may be several minutes before the state of the `services` reflects
the new built assets.

The built assets will be added to the `build/` directory.

### Database migrations

#### Quickstart

To create and/or migrate the `api` database schemas, just run
`docker-compose run migrate_api-db`.

#### Explanation

The user api (`api`) service needs to store user and profile information in an
SQLAlchemy-compatible database. The sample `accessmap.env` file defines a
(temporary) sqlite3 endpoint, but in production this should be a dedicated
server like `postgresql`.

Once the database has been defined, its schemas must be created by the `api`
service. In addition, if the `api` codebase is updated to change any schemas,
the existing database must be 'migrated' to match it.

### Running Accessmap services

#### Quickstart - During Development

Run `docker-compose up`. Alternatively, run `docker-compose up -d` to
background the compose process.

#### Quickstart - In Production

Run `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up`.
Alternatively, run `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
to background the compose process.

Note that you may need to set or change your `accessmap.env` file for a
production set up. See the file for documentation on what to change.

## Analytics

AccessMap tracks website interactions to do research on user interactions and
root out bugs. Analytics are disabled from a deployment by default. An
AccessMap user can also opt out of client-side analytics.

In order to have full control over data provenance (preserve privacy) and
collect fully custom datasets, AccessMap makes use of a self-hosted instance of
the [Rakam API](https://github.com/rakam-io/rakam-api). Just like with the
AccessMap services, this repository provides a `docker-compose`-based
deployment workflow for Rakam, under the `rakam/` subdirectory.

### Running rakam

#### During development

In development mode, `rakam` requires no configuration, just run:

    docker-compose up -d

This will create a docker-based `postgresql` database and a self-configuring
instance of Rakam.

#### In production

For production, two environment variables must be configured: one to set the
URI for a persistent `postgresql` database, ideally defined outside of this
repository, and a unique secret key that will be used to create and access
client-side analytics data. These are easiest to configure using a `rakam.env`
file, for which we have provided a template, `rakam.env.sample`. To use it,
copy it (`cp rakam.env.sample rakam.env`) and edit with a plain text editor.
The meaning of each environment variale is described in the sample environment
file.

To run the software in production mode, we need to skip the `override` file.
This can be done by running `docker-compose -f docker-compose.yml up`.

### Getting an analytics project key

`rakam` operates on the basis of "projects", which are isolated namespaces in
the analytics database. It is a good idea to create a new project for every new
study you do, e.g. for A/B testing.

`rakam` uses a web API to manage the creation of projects. To create a new one,
you need to have the `RAKAM_CONFIG_LOCK__KEY` credential mentioned above and
create a request to the endpoint. An example in development mode:

    curl --request POST --url http://localhost:9999/analytics/project/create -d '{"name": "project1", "lock_key": "mylockKey"}'

Save the response data! At a minimum, you will need to save the write key for
use by AccessMap. If necessary, you can retrieve these data at a later time
directly in the database in the `api_key` table.

In the POSTed data, `"name"` is the unique namespace for your new project and
`"lock_key"` is the secret key (essentially a password) you've defined in your
config. Make sure to run `rakam` in production mode if it is internet-facing.

When AccessMap is also deployed, it proxies requests to `/analytics` to this
`rakam` instance (if correctly configured), so you can also create new projects
at the `http(s)://$hostname/analytics/project/create` endpoint.

Save these credentials! The `write_key` is needed for any project that wants to
send analytics to this rakam project. If you lose these credentials for any
reason, they can be accessed at the database backing `rakam` in the `api_key`
table.

## Logs

Logging solutions are many, varied, annoying, particularly with docker-based
workflows. We just deploy on Ubuntu systems and edit /etc/logrotate.d/rsyslog
and add the following settings under the `/var/log/syslog` section:

    rotate 2000
    daily
    create
    missingok
    notifempty
    delaycompress
    compress
    dateext
    postrotate
        invoke-rc.d rsyslog rotate > /dev/null
    endscript

Most of these are the default settings as of writing. The import parts are:

1. `rotate 2000` indicates how long to keep logs. Because rotations are daily,
this is 2000 days.

2. `daily` indicates a daily log rotation - a new archived log file will be
created every day.

3. `dateext` adds the date to the end of the compressed, archived log.
