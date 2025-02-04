# CHANGELOG


## v0.27.3 (2025-02-04)

### Bug Fixes

- Update mkdocs configuration to use index.md as home page and install local package
  ([`f2f6984`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/f2f698460485f55a6c181e282177423dfbed3461))


## v0.27.2 (2025-02-04)

### Bug Fixes

- Add API reference documentation and update index
  ([`85b464a`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/85b464a2dc0fa4f4a0751800c91a1aa0f2e89c14))


## v0.27.1 (2025-02-04)

### Bug Fixes

- Add data folder
  ([`35242b9`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/35242b96b2d7e3043a577393fce098a725d7ac8d))


## v0.27.0 (2025-02-04)

### Build System

- **deps**: Bump trimesh from 4.6.0 to 4.6.1
  ([`55987cc`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/55987cc642a742c7d0acb71e9d92de38a3a285f9))

Bumps [trimesh](https://github.com/mikedh/trimesh) from 4.6.0 to 4.6.1. - [Release
  notes](https://github.com/mikedh/trimesh/releases) -
  [Commits](https://github.com/mikedh/trimesh/compare/4.6.0...4.6.1)

--- updated-dependencies: - dependency-name: trimesh dependency-type: direct:production

update-type: version-update:semver-patch

...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps-dev**: Bump ruff from 0.9.3 to 0.9.4
  ([`ed7894e`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/ed7894e57d69c965cf7eafc71f5f1046f2a418e5))

Bumps [ruff](https://github.com/astral-sh/ruff) from 0.9.3 to 0.9.4. - [Release
  notes](https://github.com/astral-sh/ruff/releases) -
  [Changelog](https://github.com/astral-sh/ruff/blob/main/CHANGELOG.md) -
  [Commits](https://github.com/astral-sh/ruff/compare/0.9.3...0.9.4)

--- updated-dependencies: - dependency-name: ruff dependency-type: direct:development

update-type: version-update:semver-patch

...

Signed-off-by: dependabot[bot] <support@github.com>

### Features

- Add API documentation and update mkdocs configuration
  ([`6a6b7ec`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/6a6b7ec1a96a492a73f6660eda8f5b92ac9c3659))


## v0.26.9 (2025-02-04)

### Bug Fixes

- Update Dockerfile and nginx configuration to include data directory for nova.rrd
  ([`bc40b49`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/bc40b498240ce835054594e9fbe0dd7a7a5551a9))


## v0.26.8 (2025-02-04)

### Bug Fixes

- Refactor controller initialization and cleanup in example scripts
  ([`2092579`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/2092579f2637aa71c4c9523fac8cfb333fc20e37))

- Store logging in rrd
  ([`60a94c5`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/60a94c5a94ef7575e1c10f0b3fdfadf65b253cc1))


## v0.26.7 (2025-02-04)

### Bug Fixes

- Set mounting of robot
  ([`0607e5f`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/0607e5fd1229f7b3ba93589bf68f428f4f3dc73b))


## v0.26.6 (2025-02-03)

### Bug Fixes

- Update motion group handling in main function
  ([`b743b23`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/b743b2384c473e067d141ab408c94b4193c846bc))


## v0.26.5 (2025-02-03)

### Bug Fixes

- Always refresh blueprint
  ([`a63a892`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/a63a89208acda56b635d07ba59f8773574b19b00))


## v0.26.4 (2025-02-03)

### Bug Fixes

- Save ram by serving the app from same python process
  ([`d7514c4`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/d7514c4888e5942c8c8af663db999fafe54702bc))


## v0.26.3 (2025-02-03)

### Bug Fixes

- Update Nova API host for production instances
  ([`91c1dbb`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/91c1dbb542ca3459d796dd66af1949bd6b7c74c4))


## v0.26.2 (2025-02-03)

### Bug Fixes

- Update websocket protocol handling in nginx configuration
  ([`224c89b`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/224c89b6e5eb4090d75955bcf5a084d475060469))


## v0.26.1 (2025-02-03)

### Bug Fixes

- Correct variable name for websocket protocol in nginx configuration
  ([`79cb44d`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/79cb44d9252acc77be5b9f648593c7068e72370f))

- Update websocket protocol handling in nginx configuration
  ([`e92680e`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/e92680e77d9ee5be85e516749c9d303c55dc46aa))


## v0.26.0 (2025-02-02)

### Features

- Add example for coordinated robot movements and enhance NovaRerunBridge functionality
  ([`4dc3f65`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/4dc3f659636cfd84733a4fd44070cbe0ad998f59))


## v0.25.0 (2025-02-02)

### Features

- Add example for moving robot and setting I/Os; enhance logging for actions
  ([`2ab97f9`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/2ab97f96d7cf6d19d647c6d52e3c140a05ede746))


## v0.24.0 (2025-02-01)

### Features

- Add external axis example
  ([`9e286e6`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/9e286e648abb061c5b045e36122f4ce6888d72b5))


## v0.23.1 (2025-02-01)

### Bug Fixes

- Prevent index error in robot joint transformations
  ([`3742627`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/3742627759eb07bf2362a63b53150f539a8e610d))


## v0.23.0 (2025-01-31)

### Features

- Update robots, external axis example
  ([`5cbd9ee`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/5cbd9eed71957bc751cbd935014f77f928a7a685))


## v0.22.16 (2025-01-31)

### Bug Fixes

- Don't activate motion groups
  ([`6def1ed`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/6def1edf29489fd67f3b015a01ac3946b1e82421))

- Update Nova host to use production instance URL
  ([`1400d82`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/1400d82a36888bc6b3b05a340f37344dafeffcf5))


## v0.22.15 (2025-01-31)


## v0.22.14 (2025-01-30)

### Bug Fixes

- Ensure websocket protocol is set to wss for HTTPS requests
  ([`7397261`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/7397261671c5d97a9033cc7edb0d6bbbe7161378))


## v0.22.13 (2025-01-30)

### Bug Fixes

- Remove redundant websocket protocol condition for improved clarity
  ([`b03b608`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/b03b608a948af12a94a397019f3fb0cc712f9533))


## v0.22.12 (2025-01-30)

### Bug Fixes

- Update websocket protocol condition for improved host matching
  ([`91bcec3`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/91bcec347c72709174f904ea5e09fd5057c6534c))


## v0.22.11 (2025-01-30)

### Bug Fixes

- Enhance websocket protocol handling in nginx configuration
  ([`a449457`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/a449457916e132acc6fc2185fda9bc87e96bb053))


## v0.22.10 (2025-01-30)

### Bug Fixes

- Update nginx configuration to dynamically set protocol for websocket connections
  ([`0fe0ad1`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/0fe0ad15536a841dbeadf564f7f1e7c11bf376df))


## v0.22.9 (2025-01-30)

### Bug Fixes

- Update nginx configuration to use regex for BASE_PATH location
  ([`316e5b6`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/316e5b6960fb6d9551449c3d604b348aece4ec34))


## v0.22.8 (2025-01-30)

### Bug Fixes

- Update nginx configuration to allow dynamic BASE_PATH location
  ([`91e041b`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/91e041b6d25a28287fd5920e15d08ec68fdd5c7b))


## v0.22.7 (2025-01-30)

### Bug Fixes

- Update nginx configuration to improve redirect handling for wandelbots.io
  ([`934bbf1`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/934bbf13b7252e25d4c65276c1160fad66059c9f))


## v0.22.6 (2025-01-30)

### Bug Fixes

- Update redirect handling for wandelbots.io base path in nginx configuration
  ([`cd6bcd4`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/cd6bcd48f85b01d164898c30410c85d87edacaa2))


## v0.22.5 (2025-01-30)

### Bug Fixes

- Streamline WebSocket protocol handling for wandelbots.io base path
  ([`e1de412`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/e1de412772d17cd9fb6c4bb5b782205e78051113))


## v0.22.4 (2025-01-30)

### Bug Fixes

- Update WebSocket protocol condition to use BASE_PATH for secure domains
  ([`8ced059`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/8ced059bb81e6342d2efd0d6d6bf71cd9550a7c0))


## v0.22.3 (2025-01-30)

### Bug Fixes

- Enhance WebSocket protocol handling for secure domains
  ([`c1f3a0c`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/c1f3a0c82b836fed3836091a9fddaed9f654829b))


## v0.22.2 (2025-01-30)

### Bug Fixes

- Update WebSocket protocol handling in nginx configuration
  ([`212631b`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/212631b450a621b43aec7739b5c973a84c2ea5f1))


## v0.22.1 (2025-01-30)

### Bug Fixes

- Project settings
  ([`454ff65`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/454ff657c52822208cc3ed6b0328be2f943ea3e8))

- Remove unused protocol detection logic in populate.py
  ([`f597bfb`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/f597bfba59a982a9308620eb5f56b9716cbf1ac2))


## v0.22.0 (2025-01-30)

### Features

- Add async protocol detection for API gateway connection
  ([`abde59f`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/abde59fd40ab0cc3f11b12834cd79076e8c73d9f))


## v0.21.0 (2025-01-29)

### Features

- Update Dockerfile to copy entire project and install dependencies without dev packages
  ([`63043ba`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/63043ba7aaa71fad1ec8072197264d3f7b9ed113))


## v0.20.0 (2025-01-28)

### Features

- Trigger pipeline
  ([`1102a9b`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/1102a9b8386b0fa785c636c975d4cf7c98457191))


## v0.19.0 (2025-01-28)

### Features

- Correct tcp collision geometry transform
  ([`d069c4f`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/d069c4f183f4ae342ca0a1a85be24e58ab38b13f))


## v0.18.0 (2025-01-27)

### Features

- Use correct box sizes
  ([`058c1e8`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/058c1e8ad0b8fc543bb9da2fb4a4d2cf1a9dc77b))


## v0.17.0 (2025-01-27)

### Bug Fixes

- Trigger pipeline
  ([`3e5be44`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/3e5be44ed9006cadb47d01cccb983008deda6046))

- Use half sizes for box object
  ([`08f59b7`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/08f59b7c3f329e853de4345be973c184efa4dcb4))

### Features

- Trigger pipeline
  ([`aa3f60b`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/aa3f60be432667b0dce8948aba6871ccc39cc13d))


## v0.16.0 (2025-01-27)

### Features

- Only push image on successfull release
  ([`20e3bda`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/20e3bdae1f01e239dea47a245f9907d2aa0a92c9))


## v0.15.3 (2025-01-27)

### Bug Fixes

- Use fixed host on catalog app
  ([`81d2b9f`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/81d2b9fb48b1a261d299188e5aebd3f663af7be8))

### Build System

- **deps**: Bump docker/build-push-action from 5 to 6
  ([`7ba4fec`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/7ba4fec2b0f0f6618c5120b94fed49cb50d3c772))

Bumps [docker/build-push-action](https://github.com/docker/build-push-action) from 5 to 6. -
  [Release notes](https://github.com/docker/build-push-action/releases) -
  [Commits](https://github.com/docker/build-push-action/compare/v5...v6)

--- updated-dependencies: - dependency-name: docker/build-push-action dependency-type:
  direct:production

update-type: version-update:semver-major

...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump python-semantic-release/publish-action
  ([`fe82a91`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/fe82a91f9f3eba9700828ddf5bdbb43ce6d7dddb))

Bumps
  [python-semantic-release/publish-action](https://github.com/python-semantic-release/publish-action)
  from 9.16.1 to 9.17.0. - [Release
  notes](https://github.com/python-semantic-release/publish-action/releases) -
  [Changelog](https://github.com/python-semantic-release/publish-action/blob/main/releaserc.toml) -
  [Commits](https://github.com/python-semantic-release/publish-action/compare/v9.16.1...v9.17.0)

--- updated-dependencies: - dependency-name: python-semantic-release/publish-action dependency-type:
  direct:production

update-type: version-update:semver-minor

...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump python-semantic-release/python-semantic-release
  ([`5456cd2`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/5456cd2104dcd335769d3459404919e493d90d4c))

Bumps
  [python-semantic-release/python-semantic-release](https://github.com/python-semantic-release/python-semantic-release)
  from 9.16.1 to 9.17.0. - [Release
  notes](https://github.com/python-semantic-release/python-semantic-release/releases) -
  [Changelog](https://github.com/python-semantic-release/python-semantic-release/blob/master/CHANGELOG.rst)
  -
  [Commits](https://github.com/python-semantic-release/python-semantic-release/compare/v9.16.1...v9.17.0)

--- updated-dependencies: - dependency-name: python-semantic-release/python-semantic-release
  dependency-type: direct:production

update-type: version-update:semver-minor

...

Signed-off-by: dependabot[bot] <support@github.com>


## v0.15.2 (2025-01-26)

### Bug Fixes

- Add dockerignore
  ([`bf69000`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/bf69000d558bed49e24f6f294541a6befe11cb41))


## v0.15.1 (2025-01-25)

### Bug Fixes

- Push image
  ([`dde8118`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/dde81187eb1107bb8504bf85984d6d791a8ed9cc))


## v0.15.0 (2025-01-25)

### Features

- Push image to azure
  ([`23017a8`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/23017a82aef8b1de26a384c2e58ec4efdf1256ed))


## v0.14.1 (2025-01-23)

### Bug Fixes

- Use lib in skaffold
  ([`07ebb63`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/07ebb637b38a30376d1767c49645ce3f046121fc))


## v0.14.0 (2025-01-23)

### Features

- Fixes docker and skaffold builds
  ([`ea64d48`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/ea64d48afe98d35a33199b1459505721f7e74b05))


## v0.13.1 (2025-01-22)

### Bug Fixes

- Toggle connection off
  ([`2dd09e1`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/2dd09e19432df0319682961c5b4bc7686958f793))


## v0.13.0 (2025-01-22)

### Features

- Log actions
  ([`28ecd76`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/28ecd76668299aef7aca052af27398ac5d2dacea))


## v0.12.0 (2025-01-22)

### Features

- Add log out of workspace
  ([`788b2e3`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/788b2e34a6b18d4667f0ead6fb56dfd6a4d92bc0))


## v0.11.0 (2025-01-22)

### Features

- Add robot state streaming
  ([`49615cd`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/49615cd1e2ea1bc4575ce437f7aec3860db361af))


## v0.10.1 (2025-01-21)

### Bug Fixes

- Model path check
  ([`97723b8`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/97723b81e19475037ff2bd4dfaa851dec1a3353d))


## v0.10.0 (2025-01-21)

### Features

- Add download models job
  ([`ecd13ea`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/ecd13eaf92eb6dc04c6f8d796c30d3f8ca7e1b0b))


## v0.9.0 (2025-01-21)

### Features

- Add sync and continue modes
  ([`8e7b415`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/8e7b4154cb49482351e3f65ae71ed2e9324e27c3))

- Add timing_mode
  ([`803ee99`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/803ee99067a7f0d1112f40ceb358edc0f7e6d9ac))


## v0.8.0 (2025-01-21)

### Features

- Log info for each motion group
  ([`e257928`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/e257928c9cb0945acb078ebe84e8fe10e26b571c))


## v0.7.0 (2025-01-21)

### Features

- Pass logs
  ([`b02aea2`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/b02aea20e181eea8902c7549c01ecaf324be21a8))


## v0.6.0 (2025-01-21)

### Features

- Add multiple robot example
  ([`431cee2`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/431cee2acb6687c337891e6763f86f49f942c464))


## v0.5.0 (2025-01-20)

### Features

- Log trajectory from nova
  ([`859069e`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/859069e4023abb29a5740210750ba3869633dc2a))


## v0.4.0 (2025-01-17)

### Features

- Expose main api class
  ([`c0d4698`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/c0d4698854c0cb7e0c19bf326f41afe5e5221764))


## v0.3.0 (2025-01-17)

### Features

- Add log collision scene
  ([`3d555e6`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/3d555e6b73dfbde1f28283da6b67394549eeb351))


## v0.2.0 (2025-01-17)

### Features

- Extract blueprint setup
  ([`c9ca937`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/c9ca937a6a9695fc408773899d1da0bb62727c1a))


## v0.1.0 (2025-01-17)

### Features

- Show collision motion group
  ([`02bd9c3`](https://github.com/wandelbotsgmbh/nova-rerun-bridge/commit/02bd9c3818d24732c53785d5677f79b679bc4294))


## v0.0.0 (2025-01-16)
