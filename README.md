# nova rerun bridge

Visualizes the state of your nova instance inside of [rerun.io](https://rerun.io). Rerun is a tool to quickly visualize time series data. [Instructions](https://rerun.io/docs/reference/viewer/overview) for navigation within the Rerun Viewer.
This is intended to be used alongside the [nova python lib](https://github.com/wandelbotsgmbh/wandelbots-nova). You will need a running nova instance. Register on [wandelbots.com](https://www.wandelbots.com/) to get access.

The bridge supports:

- robot (see a [list](https://wandelbotsgmbh.github.io/wandelbots-js-react-components/?path=/story/3d-view-robot-supported-models) of supported robots)
- trajectory
- dh parameters of robot
- collision model of robot
- safety zones of the robot controller
- collision objects defined in the collision store

Install the app with the nova cli tool by running:

```bash
nova catalog install rerun
```

to use it on your nova instance.

https://github.com/user-attachments/assets/ab527bc4-720a-41f2-9499-54d6ed027163

## rerun desktop app

### Setup

Adjust the `WANDELAPI_BASE_URL` and `NOVA_ACCESS_TOKEN` in the `.env` file to your instance URL (e.g. `https://unzhoume.instance.wandelbots.io`) and access token. You can find the access token in the developer portal.

Run the following command to install the dependencies:

```bash
poetry install
```

### Run

There are two script which can be run to feed the data to the rerun desktop app:

- run `python scripts/populate.py` to start a service which periodically polls the nova instance for new planned trajectories
- run `python scripts/stream_motion_groups.py` to start a service which streams the state of the active motion groups

## Development

### Deploy on local instance

- use the kubeconfig from your nova instance and run `export KUBECONFIG=kubeconfig`

- you can use [skaffold](https://skaffold.dev/) to build the image and change the deployment

```bash
skaffold dev --cleanup=false --status-check=false
```

### Tools

- code formatting and linting is done with [ruff]

```bash
poetry run ruff check scripts/. --fix
poetry run ruff format
```

### Build

To build the package locally, run the following command

```bash
poetry build
```

This will create a dist/ directory with the built package (.tar.gz and .whl files).

#### Installation

```bash
pip install wandelbots
```

#### Install a development branch in Poetry

```
nova-rerun-bridge = { git = "https://github.com/wandelbotsgmbh/nova-rerun-bridge.git", branch = "feature/branchname" }
```

## Issues

- rerun is able to run behind reverse proxy and the viewer can connect via web
- rerun sdk is _not_ able to connect to rerun which is hosted behind reverse proxy
  - [client](https://github.com/rerun-io/rerun/blob/cf9299d9205134713687e54fdf13551ed1f44bce/crates/store/re_sdk_comms/src/buffered_client.rs#L2) communicates just via sockets
  - intermediate solution is [socat](https://linux.die.net/man/1/socat)

```bash
brew install socat
socat TCP4-LISTEN:6666,fork SYSTEM:"curl -X POST -d @- http://172.30.2.224/some/rerun/sdk/"

{ echo "load_module /usr/lib/nginx/modules/ngx_stream_module.so;"; cat /etc/nginx/nginx.conf; } > temp_file && mv temp_file /etc/nginx/nginx.conf
```
