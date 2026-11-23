<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/banner.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.png">
    <img alt="PapilioVPN Core API" src="assets/banner-light.png" width="100%">
  </picture>
</p>

<h1 align="center">PapilioVPN Core API</h1>

<p align="center" lang="en">The central management API for PapilioVPN. Version 0.0.0 provides operator access and system health.</p>

<p align="center">
  <strong lang="en"><img src="assets/flags/gb.svg" width="24" alt=""> English</strong> · <a href="README.fa.md" lang="fa"><img src="assets/flags/ir-lion-and-sun.svg" width="24" alt=""> فارسی</a> · <a href="README.ru.md" lang="ru"><img src="assets/flags/ru.svg" width="24" alt=""> Русский</a> · <a href="README.zh-CN.md" lang="zh-CN"><img src="assets/flags/cn.svg" width="24" alt=""> 简体中文</a>
</p>

<p align="center">
  <a href="https://github.com/PapilioVPN/core-api/actions/workflows/check.yml"><img alt="Checks" src="https://github.com/PapilioVPN/core-api/actions/workflows/check.yml/badge.svg?branch=main"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#capabilities">Capabilities</a> ·
  <a href="#management">Management APIs</a> ·
  <a href="#development">Development</a>
</p>

<a name="quick-start"></a>

## Quick start

On Linux amd64 with Docker Engine and Compose v2, download the runtime
artifact from a successful [Checks run](https://github.com/PapilioVPN/core-api/actions/workflows/check.yml). Unzip the downloaded artifact,
then replace `YOUR_COMMIT_SHA` with the commit in the archive filename.
The installer pulls PostgreSQL and Redis images on the first setup.

```bash
archive=core-api-0.0.0-linux-amd64-YOUR_COMMIT_SHA.tar.gz
sha256sum -c "$archive.sha256" && tar -xzf "$archive"
cd core-api
./install.sh runtime
./run.sh runtime up
./run.sh runtime owner
curl -fsS http://127.0.0.1:8000/health
```

The installer generates credentials under `.local/runtime`. Keep this
directory and the PostgreSQL volume when upgrading. The owner command prompts
for a name, mobile number, and password. It creates one Super Admin per database.
The API binds to `127.0.0.1:8000` by default. Set `CORE_BIND` and `CORE_PORT`
when starting behind your TLS reverse proxy.

Use the following commands to inspect the stack, apply migrations, or stop it.
PostgreSQL data persists across a stop.

```bash
./run.sh runtime status
./run.sh runtime logs
./run.sh runtime migrate
./run.sh runtime stop
```

Enable the jobs profile to start the Scheduler worker, beat, Events, and
NATS JetStream. Scheduler clears expired refresh-token history.

```bash
CORE_JOBS=1 ./run.sh runtime up
```

<a name="capabilities"></a>

## Capabilities

| Area | Available operations |
| --- | --- |
| Authentication | Password sign-in, refresh-token rotation and revocation. |
| Users | User CRUD, role assignment, and administrator password management. Read and update your own profile and password. |
| Roles and scopes | Role and scope CRUD, plus single and batch role-scope grants. |
| System | PostgreSQL readiness, Redis checks, and permission-protected CPU, memory, storage, network, sensor and process metrics. |

<a name="management"></a>

## Management APIs

`GET /health` reports connection status and PostgreSQL server time.
Send `mobile` and `password` to `POST /admin/auth/tokens`.
Use the returned access token as a Bearer token for `GET /admin/account/me`,
and an authorized token for `/admin/users`, `/admin/roles`, `/admin/scopes`,
and `/admin/health` endpoints.

<a name="development"></a>

## Development

From a repository checkout, run `./install.sh runtime` to build and install
from source. An existing registry image can be installed with
`./install.sh runtime IMAGE@sha256:DIGEST`. Use `config.yml.sample` for
a native Python setup and point `PAPILIO_CONFIG` at your configuration.

Checks require Python 3.13 and Docker. They run against an isolated
PostgreSQL instance. Packaging writes the wheel, runtime archive, and archive
checksum in `dist/`.

```bash
./install.sh test
bash scripts/ci/check.sh
bash scripts/ci/package.sh
```
