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

### accessmap-no-db-or-analytics

This deployment launches all services necessary to run AccessMap Seattle
except for the database or analytics server.
