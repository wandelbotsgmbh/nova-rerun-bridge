# Nova Rerun Bridge

[![PyPI version](https://badge.fury.io/py/nova-rerun-bridge.svg)](https://badge.fury.io/py/nova-rerun-bridge)
[![License](https://img.shields.io/github/license/wandelbotsgmbh/nova-rerun-bridge.svg)](https://github.com/wandelbotsgmbh/nova-rerun-bridge/blob/main/LICENSE)
[![Build Status](https://github.com/wandelbotsgmbh/nova-rerun-bridge/actions/workflows/release.yml/badge.svg)](https://github.com/wandelbotsgmbh/nova-rerun-bridge/actions/workflows/release.yml)

Visualizes the state of your nova instance inside of [rerun.io](https://rerun.io). Rerun is a tool to quickly visualize time series data. [Instructions](https://rerun.io/docs/reference/viewer/overview) for navigation within the Rerun Viewer.
This is intended to be used alongside the [nova python lib](https://github.com/wandelbotsgmbh/wandelbots-nova). You will need a running nova instance. Register on [wandelbots.com](https://www.wandelbots.com/) to get access.

## 🚀 Quick Start

```bash
# Install the package
poetry install nova-rerun-bridge

# Download required robot models
poetry run download-models

´´´python
from nova_rerun_bridge import NovaRerunBridge
from nova import Nova

# Initialize
nova = Nova()
bridge = NovaRerunBridge(nova)

# Setup visualization
await bridge.setup_blueprint()

# Log a trajectory
await bridge.log_trajectory(joint_trajectory, tcp, motion_group)
```

# ✨ Features

- 🤖 Real-time 3D robot visualization (see a [list](https://wandelbotsgmbh.github.io/wandelbots-js-react-components/?path=/story/3d-view-robot-supported-models) of supported robots)
- 🎯 Trajectory playback and analysis
- 💥 Collision scene visualization
- ⏱️ Motion timing analysis
- 🔄 Continuous monitoring mode

## 💻 Usage Examples

The python library can be used to feed data to the rerun desktop app. The library is built on top of the nova python library and provides a simple interface to feed data to the rerun desktop app. See the [minimal example](https://github.com/wandelbotsgmbh/nova-rerun-bridge/tree/main/minimal_example) on how to use the library.

### Basic Motion Logging

```python
# Log simple motion
await bridge.log_trajectory(joint_trajectory, tcp, motion_group)
```

### Collision Scene Visualization

```python
# Log collision scenes
await bridge.log_collision_scene()
```

## Setup

Adjust the `NOVA_API` and `NOVA_ACCESS_TOKEN` in the `.env` file to your instance URL (e.g. `https://unzhoume.instance.wandelbots.io`) and access token. You can find the access token in the developer portal.

Run the following command to install the dependencies:

```bash
poetry install
```

You can try out the [examples](https://github.com/wandelbotsgmbh/nova-rerun-bridge/tree/main/nova_rerun_bridge/examples) in the `examples` folder.

## ⚙️ Configuration

The bridge can be configured through environment variables:

- RECORDING_INTERVAL: Set visualization update interval (default: 0.1s)

This project contains a python library (rerun-nova-bridge) to use the rerun bridge in your own project and an app setup which you can install on your nova instance.

https://github.com/user-attachments/assets/ab527bc4-720a-41f2-9499-54d6ed027163

## Download Robot Models

After installing the library, you need to download the robot models:

```bash
# If installed via poetry
poetry run download-models

# If installed via pip
python -m nova_rerun_bridge.models.download_models
```

This will download the robot models into your project folder. You can use the library without downloading the models, but you will not be able to visualize the robot models in the rerun viewer.

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

#### Install a development branch in Poetry

```
nova-rerun-bridge = { git = "https://github.com/wandelbotsgmbh/nova-rerun-bridge.git", branch = "feature/branchname" }
```

# Run as Nova App

The easiest way to try it out is to install the app on your nova instance. Use the nova cli tool and run:

```bash
nova catalog install rerun
```

to use it on your nova instance.

The rerun bridge can be run as a nova app. To install the app on your nova instance, use the nova cli tool and run:

```bash
nova catalog install rerun
```

There are two script which can be run to feed the data to the rerun desktop app. The app automatically runs both scripts in the background. You can also run the scripts manually on your local machine.

- run `python nova_rerun_bridge/polling/populate.py` to start a service which periodically polls the nova instance for new planned trajectories
- run `python nova_rerun_bridge/polling/stream_motion_groups.py` to start a service which streams the state of the active motion groups

## Development

### Deploy on local instance

- use the kubeconfig from your nova instance and run `export KUBECONFIG=kubeconfig`

- you can use [skaffold](https://skaffold.dev/) to build the image and change the deployment

```bash
skaffold dev --cleanup=false --status-check=false
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

# 📝 License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.
