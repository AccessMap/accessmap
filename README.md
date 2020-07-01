# AccessMap

This repo contains all of the infrastructure needed to create and run AccessMap except
for the data, which can be generated using the `accessmap-data` repo. These are the
AccessMap-specific software projects used to deploy AccessMap:

- [AccessMap Web App (React-based)](https://github.com/accessmap/accessmap-webapp)

- [`unweaver`: our flexible routing engine](https://github.com/nbolten/unweaver)

- [AccessMap Users API](https://github.com/accessmap/accessmap-api)

- [AccessMap Data ETL Pipeline (to get data)](https://github.com/accessmap/accessmap-data)

The full pipeline of how AccessMap is deployed can be seen in this diagram:

![AccessMap orchestration diagram](orchestration-diagram.png)

## Deployment strategy

### `docker` and `docker-compose`

AccessMap is deployed using `docker-compose`, which ties various AccessMap-related
services in isolated `docker` containers. These services are written in a variety of
different languages and often require a significant amount of environment preparation
to run (GIS libraries, very specific programming language versions, etc), which
the automation provided by `docker` alleviates. The rest of this documentation will
assume some familiarity with `docker`, so you may want to review the
[`docker` documentation](https://docs.docker.com/) before attempting to deploy
AccessMap. Because this guide almost exclusively uses `docker-compose` to manage
`docker` containers, you may also want to review the
[`docker-compose` documentation](https://docs.docker.com/compose/).

### `develop`, `staging`, and `production` environments

This repository is developed using three discrete environments, each with unique
configurations: `develop`, `staging`, and `production`. Each environment has distinct
sources of its configurations to assist whatever step in deployment is being targeted.

The distinct environments described in this repository are exclusively about the
*deployment* of AccessMap, so the 'stage' in which this repo is deployed will often
differ from the development 'stage' from the point of view of an individual service.
For example, the default `develop` environment is meant for providing a useful
environment for making and testing modifications to the deployment scripts and configs,
but the user API is being run under its "production" settings because we're
testing its deployment, not editing its code.

All deployment environments share a core `docker-compose.yml` configuration file, but
deviate with additional files that override (or add to) its configuration. The default
environment, `develop`, uses `docker-compose.override.yml`, which `docker-compose`
automatically interprets as default overrides without any additional configuration.

## Deployment guide

### 1. Configure environment(s)

#### The `develop` environment

The `develop` environment is the default environment and it is intended for a local
deployment while developing or testing AccessMap. It exposes web APIs directly on local
ports so that they can be interfaced with by outside code. This is particularly useful
when you want to make changes to an AccessMap codebase that makes use of these
services, such as the
[`accessmap-webapp`](https://www.github.com/AccessMap/accessmap-webapp) front end,
which is only fully functional in combination with a vector tile server, users API, and
routing engine.

All of these services are made available in development mode at
`http://localhost:2015/tiles` (tile server), `http://localhost:2015/api/v1/users`
(users API), and `http://localhost:2015/api/v1/routing` (routing engine). The
aforementioned endpoints are all handled by the built-in reverse proxy, Caddy. In
addition, the users API and routing engines are directly available at
`http://localhost:5000` and `http://localhost:5656`, respectively.

The `develop` environment requires very little configuration and uses dummy default
values for many important configuration settings. Most of these can be found in
`docker-compose.override.yml`. In addition, the users API database is ephemeral and
stored in a temporary SQLite database. The `develop` environment should never be used
for any public-facing deployment as it would represent a security risk from things like
publicly-shared secret keys.

The `develop` environment does need to be configured some some environment variables.
This is best handled using the .env strategy described in the section on
[environment variables](#environment-variable-reference).  `DEV_HOST` is required and
should usually be set to `localhost` for local development. One exception is if the
deployment needs to be reached on another local device, such as when developing for a
mobile application. In this case, it should be set to your local network IP address.
`DEV_MAPBOX_TOKEN` must be set for the basemap to render. `DEV_ANALYTICS*` environment
variables must be set if you wish to configure and make use of the `rakam` analytics
back end. `DEV_OSM*` environment variables must be set if you want to make use of the
users API.

Other environment variables can be set with the `DEV_` prefix (review the
`docker-compose.overridey.yml` file to see all options). Notably, the
`DEV_CONSUMER_CALLBACK_URI` environment variable controls the behavior of the users API
authentication workflow and can be useful when testing the users API.

#### The `staging` and `production` environments

These environments are meant for deploying AccessMap to public-facing servers and are
therefore intended to be used with best practices for security and data management. As
a `.env` file is used for most configuration, it is good to set this file to be
readable only by the user deploying the docker containers, ideally a dedicated `docker`
user.

The `production` deployment represents AccessMap as it can be found at a public
endpoint like [accessmap.io](https://www.accessmap.io). However, best practices for
a complex and stateful application dictate that we should not directly make
modifications to a production deployment except in extreme circumstances. Instead, we
should test changes in an environment that is identical to `production`, but hosted
at a different location: the `staging` environment. Therefore, the `production` and
`staging` environments share identical `docker-compose` configuration files;
`docker-compose.production.yml` and `docker-compose.staging.yml` are identical aside
from environment variable names.

Unlike in the `develop` environment, the `staging` and `production` do not have
dummy values as defaults for important configuration variables, particularly those
for security. The environment variables that must be configured (see the `.env.example`
file):

- `*_HOST`: The endpoint at which AccessMap is deployed. The reverse proxy will be
configured to enable HTTPS and route traffic from this endpoint, so it must refer to a
domain that has been configured with DNS `CNAME` or `A` records pointing to your
server or cloud-hosted VM.

- `*_MAPBOX_TOKEN`: Your Mapbox token. This is necessary for the basemap to render.
You can choose to use the same token for all environments or different tokens for
each environment depending on how you want to track usage and your quotas.

- `*_ANALYTICS`: Configuration information for the `rakam` analytics server. The
`*_ANALYTICS_URL` has a sensible default and usually does not require configuration.
`*_ANALYTICS_KEY` should differ between `production` and `staging` environments, as
this will keep user interaction data from real users and internal testing separate.

- `*_API_DATABASE_URI`: A URI for the database used by the users API. This should be an
[SQLAlchemy-compatible](https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls)
connection string, though only PostgreSQL is tested. Separate databases should be used
for `production` and `staging` environments, though securely copying data from a
`production` to a `staging` database is acceptable for testing.

- `*_API_SECRET`: This is a secret used for signing data in requests to the users API.
This secret should be protected and kept secret, as anyone with this secret could
attempt to modify the users API database via web endpoints. It is a best practice to
generate this secret using a hash function at least as good as SHA-256.

- `*_JWT_SECRET_KEY`: This is a secret used for signing all JWT tokens from the users
API. Anyone with this secret can decode an intercepted request containing privileged
user information, namely the user ID and their pedestrian profile information, which
should be considered personally identifiable. Follow the same best practices as for
`*_API_SECRET`.

- `*_OSM*`: OpenStreetMap authentication details. These are OAuth 1.0 API key
credentials obtained for a given endpoint by creating an account on
https://openstreetmap.org or https://master.apis.dev.openstreetmap.org (the latter
is for testing only). These credentials must point to the callback URI defined by
`*_CONSUMER_CALLBACK_URI`.

- `*_CONSUMER_CALLBACK_URI`: This is where users are redirected after authentication
and it must match the configuration on the OpenStreetMap website. This can be set
to a local endpoint for testing, but has a sensible and functional default at the
remote endpoint.

### 2. Initialize database(s)

#### Users API database initialization

The first time that you create a deployment, you will need to run the migration
scripts to create the database. You can do this via docker-compose:

    docker-compose run api poetry run flask db upgrade

For staging or production environments, make sure to add
`-f docker-compose.{environment}.yml` immediately after `docker-compose`.

#### Running a users API database migration

If the upstream code in AccessMap changes, you may need to re-run the same command in
order for the schema to be up-to-date:

    docker-compose run api poetry run flask db upgrade

Be careful about doing such migrations on a production service: you may need to shut
it down during the migration to avoid database inconsistencies, as the service may
attempt to write to tables or columns that no longer exist.

### 3. Get data

For a deployment to work, you need to places two files in the `data/` directory:
`transportation.geojson` and `regions.geojson`. We would like to publish these data
so that they can be more easily acquired, but haven't found the right resource to do
so in a low-cost, versioned manner. Until then, they need to be generated using our
[open source ETL pipelines](https://github.com/AccessMap/accessmap-data) or shared by
our team.

#### `transportation.geojson`

This is produced by our
[open ETL pipeline](https://github.com/accessmap/accessmap-data).

This GeoJSON file describes the pedestrian network for a given region and contains
features like sidewalks, crosswalks, and curb data. It follows the OpenMapTiles tile
`transportation` layer schema, with a few extensions (read the `accessmap-data` README
for more information). This will be used as the data for routing in the `unweaver`
routing engine that powers AccessMap and will become the `transportation` layer in
the `pedestrian` tileset served by AccessMap.

#### `regions.geojson`

This is produced by our
[open ETL pipeline](https://github.com/accessmap/accessmap-data).

This GeoJSON file describes the regions served by this instance of AccessMap and is
auto-generated as part of the `accessmap-data` ETL pipeline. Each feature has a
geometry (the convex hull) of the region served and has metadata used to define front
end interactions, such as where to center the map, the name and unique key of the
region, and its `[W,S,E,N]` bounding box. This data is embedded in the web front end
during the transpiling and bundling step.

### 4. Build assets

AccessMap builds data resources as part of its deployment: it compiles the web app
into a minified set of static assets, creates a graph file for routing, and generates
vector tiles. Because these steps do not need to be run during every redeployment, they
are controlled by a separate set of docker-compose files:

- `docker-compose.build.yml` is the primary config and is shared by all environments.

- `docker-compose.build.override.yml` has `develop`-specific configuration options.

- `docker-compose.build.staging.yml` has `staging`-specific configuration options.

- `docker-compose.build.prod.yml` has `production`-specific configuration options.

Building assets for each environment is achieved by cascading configuration files with
the `-f` flag:

- The `develop` environment: `docker-compose -f docker-compose.build.yml -f
docker-compose.build.override.yml up`

- The `staging` environment: `docker-compose -f docker-compose.build.yml -f
docker-compose.build.staging.yml up`

- The `production` environment: `docker-compose -f docker-compose.build.yml -f
docker-compose.build.prod.yml up`

### 6. Deploying the services

AccessMap deploys these long-running services: a reverse proxy that handles HTTPS
security and routes (caddy), a routing engine, and the user API. Deploying these
services also uses cascading configs:

- The `develop` environment: `docker-compose up` (this is equivalent to
`docker-compose -f docker-compose.yml -f docker-compose.override.yml up`)

- The `staging` environment: `docker-compose -f docker-compose.yml -f
docker-compose.staging.yml up`

- The `production` environment: `docker-compose -f docker-compose.yml -f
docker-compose.prod.yml up`

To run in the background, you can add the `-d` flag. For example, to run in the
background in `develop` mode: `docker-compose up -d`. To shut down the services, you
can use `docker-compose down` or manually stop, remove, and recreate any services using
the associated commands (`docker-compose stop {service}`, `docker-compose rm {service}`,
`docker-compose up -d {service}`).

Once deployed, AccessMap is available by default at either `http://localhost:2015`
(`develop` mode) or at the `*_HOST` environment variable you configured earlier.

If something appears to be wrong, you can investigate a the logs from a particular
service by running `docker-compose logs -f {service}`.

### 7. (optional) Analytics with Rakam

AccessMap tracks website interactions to do research on user interactions and root out
bugs. Analytics can be disabled by the user, is not required to deploy AccessMap, and
can be disabled at the server level using the `ANALYTICS=no` environment variable.

#### Running Rakam

AccessMap uses a self-hosted deployment of `Rakam` for its analytics. We chose `rakam`
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

#### Getting an analytics project key

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

## Environment variable reference

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

## Logs

Logging solutions are many, varied, annoying, particularly with docker-based workflows.
AccessMap's deployment does not come with any sophisticated server-side logging system,
but does export all Caddy logs to stdout, which then places them into the main system
log. Therefore, all hits to the main reverse proxy are persisted to the default system
log, if it exists on the deployed server. These can be intercepted and processed using
any logging method you prefer.

AccessMap uses a simple approach of saving logs on a daily basis on the deployment
server. This involves adding these settings to the `/var/log/syslog` section of the
`/etc/logrotatde.d/rsyslog` configuration file:

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

Most of these are the default settings and are added to ensure consistency between
deployments. These settings are non-default:

- `rotate 2000` indicates how long to keep logs. Because rotations are daily, this is
2000 days, approximately five and a half years.

- `daily` indicates a daily log rotation - a new archived log file will be created
every day.

- `dateext` adds the date to the end of the compressed, archived log.

Note that under this strategy, logs only exist on the deployment server and must be
backed up by hand.
