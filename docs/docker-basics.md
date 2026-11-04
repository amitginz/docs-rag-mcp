# Docker basics

## Images and containers
An image is a read-only template built from a Dockerfile. A container is a running instance of an image. Containers share the host kernel and use Linux namespaces and cgroups for isolation and resource limits.

## Dockerfile tips
Order instructions from least to most frequently changed so layer caching works: copy `requirements.txt` and install dependencies before copying the application code. Use a slim base image and add a `.dockerignore` file to keep the build context small.

## Data and networking
Container filesystems are ephemeral. Use volumes to persist data. Publish a port with `-p 8080:80` to reach a container from the host. Containers on the same user-defined network can reach each other by service name.

## Docker Compose
`docker compose up` starts several services defined in one YAML file, for example an API, a database and a cache, with shared networks and environment variables.
