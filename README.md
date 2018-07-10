# AccessMap Orchestration

This repo contains orchestration info for AccessMap's deployments. At the
moment, that entails docker-compose setups for different use cases, primarily
focused on:
  - The production deployment on accessmap.io
  - Testing / research deployments for students / researchers
  - Development environments

## The deployments

### Configuration

Each directory is a self-contained docker-compose setup. Configuration is
controlled by using either a .env file or exporting the necessary environment
variables globally or in the scope of the docker-compose command. An example
.env file is available for each directory as .env.example.

Please note that because all of the services run in a docker container, the
host network is not available without some hacky workarounds. Therefore, if
an environment variable requires a database URI that refers to `localhost`, it
will be looking at the docker container's network, not the host's network.

### Running a deployment

To run any given deployment, just run `docker-compose up` in its directory. To
launch as a background daemon, run `docker-compose -d up`.

The docker-compose files are all version `3`, so make sure you have a recent
version of `docker-compose` (they were initially developed with v1.15).

Running the containers should require only `docker` and `docker-compose`.
Doing some of the follow-up setup may require `curl`.

### Setup

#### Rakam analytics

This step is optional - everything will run fine without the analytics server, except
user interactions won't be tracked (of course).

Rakam has been isolated into its own deployment, found in the `rakam` directory. In
development mode (default), it persists data in /docker/rakamdb, a postgres database.
This poses a challenge for other services that use it - they need access to the host
network. This is handled somewhat automatically in development mode, but should be
kept in mind if networking issues arise. In staging and production environments, rakam
should have its own stable URL and use a properly managed database (not using a docker
DB).

Do the following steps in the `rakam` directory:

1. (production mode only) Set up the following environment variables in the `.env`
file:
  - `RAKAM_CONFIG_LOCK__KEY`: set this to a secret string. This is a 'master'
  password for making new analytics projects, and its endpoint will be public. In
  development mode, this would be set to a hard-coded, publicly visible (in this repo)
  string, so make sure to set this variable properly in production!
  - `RAKAM_PROD_DB_URL`: A postgres database URI for connecting to the database
  backing rakam in production mode. All of the settings can be created arbitrarily,
  but the default string in development mode is
  `postgres://rakam:dummy@rakamdb:5432/rakam`.
  - `RAKAM_STAGING_DB_URL`: when running in staging mode (docker-compose.staging.yaml),
  use this instead of `RAKAM_PROD_DB_URL`.

2. Start the services

`docker-compose up`

3. Access rakam at `{host}:9999`

4. Create a project. The example below is for a development version (hence port 2015).

    curl --request POST --url http://localhost:2015/analytics/project/create -d '{"name": "project1", "lock_key": "mylockKey"}'

Save these credentials! The `write_key` is needed for any project that wants to send
analytics to this rakam project. If you lose these credentials for any reason, they
can be accessed at the database backing `rakam` in the `api_key` table.

#### accessmap, accessmapuw, accessmapemission

Setting up this deployment is a two-step process, as the analytics
server requires a bit of setup and creating some credentials, and then the
webapp needs to know those credentials and get restarted (i.e. the
docker-compose file needs to be edited).

1. Edit environment variables in the `.env` file. If one doesn't exist, copy
it from `.env_sample`: `cp .env_sample .env`:

  - `DATADIR`: The host directory for storing persistent data (routing and tiles). This
  defaults to `/docker/{subproject}_data` if not set, e.g. `/docker/accessmap_data`.
  - `MAPBOX_TOKEN`: A Mapbox token for your deployment, lets you use their
  vector tiles for your map.
  - `OPENID_CLIENT_ID`: The client ID value that is registered with OpenToAll accounts.
  This is only necessary if you want logins to work.

2. (optional) Add analytics environment variables to the `.env` file. In dev mode,
these do not need to be configured - just set up and run `rakam` in the previous
section. The staging/production environment variables;

   - `ANALYTICS_SERVER`: the full URL to the analytics server, including the port if
   it hasn't been proxied to a path on port :80. Examples: mycoolwebsite.com:9999 or
   192.168.0.34:9999 (static local network IP of your computer).
   - `ANALYTICS_KEY`: a write key for a project on the `rakam` instance. It's best to
   create a new analytics project for at least every major release, and ideally on a
   per-study basis.

3. Put the required input data in the `DATADIR` folder if you set that variable in
`.env`, `/docker/{subproject}_data` if you didn't. Example: `/docker/accessmap-data`.

Note that the data should correspond to the `config/layers.json` file in the
subproject as well as the tippecanoe build script in `scripts/build_tiles.sh`. For
example, the `accessmap` project expects these files to exist:

  - `sidewalks.geobuf`

  - `crossings.geobuf`

  - `elevator_paths.geobuf`

The data used in all of these projects can be generated using the
[accessmap-data](https://github.com/accessmap/accessmap-data) repository.

4. Start the services: `docker-compose up -d`.

To run in production or staging mode, cascade the configs:
`docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

Some of the services may take a while to load, depending on the size of the dataset.
You can track their current status using `docker logs`, e.g. to check the tile-building
container:

    docker logs -f tippecanoe

5. Test the servies

For projects running in development mode, the website will be available at
`localhost:2015` (and available externally at `{your_ip}:2015`. Note that accessmapuw
does not currently have a website, and will only provide tiles and the routing
service, as it's focused on native mobile apps.
