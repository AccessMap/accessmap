# AccessMap Orchestration

![AccessMap orchestration diagram](orchestration-diagram.png)

This repo contains the `docker-compose` orchestration scripts and setup for AccessMap.

It is set up to support a dev-staging-production workflow, whereby local testing can
be done in `development` mode with debug messages and (potentially) less secure
methods, while `staging` and `production` (`prod`) modes are optimized for speed, do
not show debug methods, and use best practices security.

## Configuration

AccessMap requires two types of configuration: (1) Data for routing, generating tiles,
and defining regions served by the application (e.g. multiple cities), and (2)
environment variables dictating how the deployments run.

### Getting data

For a deployment to work, you need to places two files in the `data/` directory:
`transportation.geojson` and `regions.geojson`.

#### Aside: where do I get these files?

For now, the best way to get AccessMap data is to run our reproducible ETL pipelines
in the `accessmap-data` repository: https://github.com/accessmap/accessmap-data. Note
that you may want to use the `develop` branch to get the latest build process. Using
the `accessmap-data` repository, you can run `snakemake -j 8` in each `cities`
subdirectory and then `python ./merge.py` to get all the data you need for this
deployment: `transportation.geojson` and `regions.geojson`.

#### `transportation.geojson`

This GeoJSON file describes the pedestrian network for a given region and contains
features like sidewalks, crosswalks, and curb data. It follows the OpenMapTiles tile
`transportation` layer schema, with a few extensions (read the `accessmap-data` README
for more information). This will be used as the data for routing in the `unweaver`
routing engine that powers AccessMap and will become the `transportation` layer in
the `pedestrian` tileset served by AccessMap.

#### `regions.geojson`

This GeoJSON file describes the regions served by this instance of AccessMap and is
auto-generated as part of the `accessmap-data` ETL pipeline. Each feature has a
geometry (the convex hull) of the region served and has metadata used to define front
end interactions, such as where to center the map, the name and unique key of the
region, and its `[W,S,E,N]` bounding box. This data is embedded in the front end via
the `webapp` service.


### Environment variables

AccessMap uses environment variables to configure its deployments to maximize
portability and follow best practices. These environment variables can be set at
runtime (using `source` or explicit `export` commands, for example) or configured using
a .env file, of which an example is provided at .env.sample.

Environment variables that need to be configured and distinct for different deployments
(dev, staging, production) are prepended with an environment string. For example, to
pass the `OSM_CLIENT_ID` setting to a dev environment, set `DEV_OSM_CLIENT_ID`. By
explicitly separating these deployment configurations, you can ensure your secrets will
never leak in an inappropriate environment. The following examples do not have the
prepended environment string, for simplicity:

`HOST`: The hostname of the deployment. For development, this is usually localhost,
though it might sometimes be 0.0.0.0 for tricky dev deployments (e.g., native
application clients). In staging/production modes, this should usually be a registered
domain name URI, potentially with a subdomain, e.g. `stage.yourwebsite.com` or
`yourwebsite.com`. In development mode, this host will be automatically prepended with
`http://`, while staging and production modes will have `https://`.

`MAPBOX_TOKEN`: An API access token from `mapbox.com`, used to geocode and get basemap
tiles.

`ANALYTICS`: Whether or not analytics is enabled. Set to "yes" to enable analytics,
"no" to disable. If set to "no", the two following environment variables do not need to
be set.

`ANALYTICS_URL`: This does not need to be set in `development` mode, as it is
assumed to be a local deployment from the `rakam` directory. In staging or production,
this should be the base URL for the analytics endpoint and it should be secure to
prevent MITM attacks: either a local URL at an endpoint not exposed to the internet
(like a closed port) or over HTTPS.

`ANALYTICS_KEY`: The write key for your `rakam` project. See the Analytics section for
more information.

`OSM_CLIENT_ID`: Your OAuth 1.0a registered application client ID from
openstreetmap.org. This is used for logins. Keep in mind that development mode uses
the testing API on openstreetmap.org rather than the main one, so you will need to
register an application at https://master.apis.dev.openstreetmap.org/ for development
and https://api.openstreetmap.org for production.

`OSM_CLIENT_SECRET`: Your OAuth 1.0a registered application client secret from
openstreetmap.org.

`API_SECRET`: The secret to be passed to the API for securing sessions. This should
be a properly secure hash based on something like `ssh-keygen` and should be a
closely-guarded secret in both staging and production modes. It should also be unique
between every mode.

`JWT_SECRET_KEY`: A secret used to sign JWTs, this must also be a secure and unique
secret generated by something like `ssh-keygen`. JWTs are exposed to clients and a
poorly-chosen secret could compromise your users' credentials and personal information.

`CONSUMER_CALLBACK_URI`: This is intended to control the redirect after logins occur -
for AccessMap, this is usually `$HOST/login_callback`. In development mode, this
defaults to `http://localhost:2015/login_callback`.

`OSM_URI`: This is only really intended for the staging environment, which may need to
test features in both the OpenStreetMap sandbox and then on the primary OSM deployment.
It is the base URL for the OpenStreetMap API to use.

## Running a deployment

`docker-compose` has an awkward system for managing different deployment environments
that depends on explicitly cascading different configuration files whenever you run
a `docker-compose` command. AccessMap uses a bunch of docker-compose files to make this
workflow possible.

`docker-compose` also does not have a good way to separate out long-running services
from those that only need to be run once or very infrequently, so we use separate
configuration files for the `build` steps (compiling the web app, creating the routing
graph, creating vector tiles) from the `run` steps (running the reverse proxy, the
routing engine, the API).

### Building assets

AccessMap builds data resources as part of its deployment: it compiles the web app
into a minified set of static assets, creates a graph file for routing, and generates
vector tiles. Because these steps do not need to be run during every redeployment, they
are controlled by a separate set of docker-compose files: `docker-compose.build.yml`,
`docker-compose.staging.yml`, and `docker-compose.prod.yml`. To deploy different
environments, cascade the configs. Examples:

In development mode:

    `docker-compose -f docker-compose.build.yml up`

In staging mode:

    `docker-compose -f docker-compose.build.yml -f docker-compose.build.staging.yml up`

In production mode:

    `docker-compose -f docker-compose.build.yml -f docker-compose.build.prod.yml up`

*Note: the build steps will fail if you haven't added your files to the `data/`
directory*

### Database migrations

The user api (`api`) service is stateful and depends on precise table definitions in
its database that may change over the lifetime of the project. Setting up the database
can therefore sometimes have two steps: database initialization and database
migrations. Because running migrations on staging/production databases should be
carefully curated, database migration is not automatically built into the main
build/run workflow.

#### Database initialization

During the first time that you create a deployment, you will need to run the migration
scripts to create the database. You can do this via docker-compose:

    docker-compose run api poetry run flask db upgrade

For other environments, make sure to add `-f docker-compose.{environment}.yml` after
the `docker-compose` command.

#### Running a migration

If you want to update your database to match the latest in AccessMap, you'll need to
run the same command as above:

    docker-compose run api poetry run flask db upgrade

Be careful about doing such migrations on a production service - you may often need to
use intermediate database schemas to transition from an old schema to a new schema,
where data is copied to multiple tables until all clients have transitioned to the new
schema.

### Long-running services

AccessMap deploys a few long-running services: a reverse proxy that handles HTTPS
security and routes (caddy), an instance of the routing engine, and an instance of the
user API. These are also created by cascading configs:

In development mode:

    `docker-compose -f docker-compose.yml up`

In staging mode:

    `docker-compose -f docker-compose.yml -f docker-compose.staging.yml up`

In production mode:

    `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up`

## Analytics

AccessMap tracks user interactions to do research on user interactions and root out
bugs. Analytics is not required to deploy AccessMap and can be disabled using
`ANALYTICS=no` environment variable.

### Running rakam

AccessMap uses a self-hosted deployment of `rakam` for its analytics. We chose `rakam`
because it could be self-hosted (no data shared with third parties) and has a very
flexible data storage model that works well for doing studies.

You do not need to run your own deployment of `rakam` to enable analytics - you can
just as easily use the paid rakam service. However, if you want to self-deploy, the
`rakam` directory contains the `docker-compose` configs you need to get up and running.

In development mode, `rakam` requires no configuration, just run:

    docker-compose up -d

In staging and production modes, you should be using a secure production database to
run `rakam`, so set these environment variables (prepend `STAGING_` or `PROD_`):

- `RAKAM_CONFIG_LOCK_KEY`: This is a secret used for generating new projects and should
be treated as root access to the analytics server and database. Make it secret!

- `RAKAM_DB_URL`: The JDBC-compatible database URL. Using SSL is strongly recommended.
AccessMap uses the postgres driver.


### Getting a key

`rakam` operates on the basis of "projects", which are isolated namespaces in the
analytics database. It is a good idea to create a new project for every new study you
do, e.g. for A/B testing.

`rakam` uses a web API to manage the creation of projects. To create a new one, you
need to have the `RAKAM_CONFIG_LOCK_KEY` credential mentioned above and create a
request to the endpoint. An example in development mode:

    curl --request POST --url http://localhost:9999/analytics/project/create -d '{"name": "project1", "lock_key": "mylockKey"}'

Save the response data! At a minimum, you will need to save the write key for use by
AccessMap. If necessary, you can retrieve these data at a later time directly in the
database in the `api_key` table.

In the POSTed data, `"name"` is the unique namespace for your new project and
`"lock_key"` is the secret key (essentially a password) you've defined in your config.
Make sure to run `rakam` in staging or development mode if it is internet-facing.

When AccessMap is also deployed, it proxies requests to `/analytics` to this `rakam`
instance (if correctly configured), so you can also create new projects at the
`http(s)://$hostname/analytics/project/create` endpoint.

Save these credentials! The `write_key` is needed for any project that wants to send
analytics to this rakam project. If you lose these credentials for any reason, they
can be accessed at the database backing `rakam` in the `api_key` table.

## Logs

Logging solutions are many, varied, annoying, particularly with docker-based workflows.
We just deploy on Ubuntu systems and edit /etc/logrotate.d/rsyslog and add the
following settings under the `/var/log/syslog` section:

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

1. `rotate 2000` indicates how long to keep logs. Because rotations are daily, this is
2000 days.

2. `daily` indicates a daily log rotation - a new archived log file will be created
every day.

3. `dateext` adds the date to the end of the compressed, archived log.
