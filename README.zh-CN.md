<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/banner.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.png">
    <img alt="PapilioVPN Core API" src="assets/banner-light.png" width="100%">
  </picture>
</p>

<h1 align="center">PapilioVPN Core API</h1>

<p align="center" lang="zh-CN">PapilioVPN 的中央管理 API。0.0.0 版本提供操作员访问管理与系统健康检查。</p>

<p align="center">
  <a href="README.md" lang="en"><img src="assets/flags/gb.svg" width="24" alt=""> English</a> · <a href="README.fa.md" lang="fa"><img src="assets/flags/ir-lion-and-sun.svg" width="24" alt=""> فارسی</a> · <a href="README.ru.md" lang="ru"><img src="assets/flags/ru.svg" width="24" alt=""> Русский</a> · <strong lang="zh-CN"><img src="assets/flags/cn.svg" width="24" alt=""> 简体中文</strong>
</p>

<p align="center">
  <a href="https://github.com/PapilioVPN/core-api/actions/workflows/check.yml"><img alt="Checks" src="https://github.com/PapilioVPN/core-api/actions/workflows/check.yml/badge.svg?branch=main"></a>
</p>

<p align="center">
  <a href="#quick-start">快速开始</a> ·
  <a href="#capabilities">功能</a> ·
  <a href="#management">管理 API</a> ·
  <a href="#development">开发</a>
</p>

<a name="quick-start"></a>

## 快速开始

在装有 Docker Engine 和 Compose v2 的 Linux amd64 系统上，从
[成功的 Checks 运行](https://github.com/PapilioVPN/core-api/actions/workflows/check.yml)下载运行包。解压下载的 ZIP 文件，
并将 `YOUR_COMMIT_SHA` 替换为归档文件名中的提交哈希。
初次安装会拉取 PostgreSQL 和 Redis 镜像。

```bash
archive=core-api-0.0.0-linux-amd64-YOUR_COMMIT_SHA.tar.gz
sha256sum -c "$archive.sha256" && tar -xzf "$archive"
cd core-api
./install.sh runtime
./run.sh runtime up
./run.sh runtime owner
curl -fsS http://127.0.0.1:8000/health
```

安装脚本在 `.local/runtime` 生成凭据。升级时请保留此目录和
PostgreSQL 数据卷。owner 命令会提示输入姓名、手机号和密码，并为每个
数据库创建一个超级管理员。API 默认监听 `127.0.0.1:8000`。
通过 TLS 反向代理访问时，可在启动时设置 `CORE_BIND` 和 `CORE_PORT`。

以下命令可查看服务状态和日志、应用迁移或停止服务。
停止后 PostgreSQL 数据仍会保留。

```bash
./run.sh runtime status
./run.sh runtime logs
./run.sh runtime migrate
./run.sh runtime stop
```

启用 jobs 配置可启动 Scheduler、beat 和 Events 进程以及 NATS JetStream。
Scheduler 会清理已过期的刷新令牌历史。

```bash
CORE_JOBS=1 ./run.sh runtime up
```

<a name="capabilities"></a>

## 功能

| 范围 | 可用操作 |
| --- | --- |
| 身份验证 | 密码登录、轮换与撤销刷新令牌。 |
| 用户 | 创建、查询、修改和删除用户，分配角色和管理密码，以及查看和修改自己的资料和密码。 |
| 角色与权限 | 管理角色和权限范围，支持单条或批量为角色分配权限。 |
| 系统 | 检查 PostgreSQL 和 Redis。具备相应权限可读取 CPU、内存、存储、网络、传感器和进程指标。 |

<a name="management"></a>

## 管理 API

`GET /health` 返回连接状态和 PostgreSQL 服务器时间。
向 `POST /admin/auth/tokens` 提交 `mobile` 和 `password`，
然后将访问令牌作为 Bearer 令牌访问 `GET /admin/account/me`。
访问 `/admin/users`、`/admin/roles`、`/admin/scopes` 和
`/admin/health` 下的端点需要相应权限。

<a name="development"></a>

## 开发

在仓库工作副本中运行 `./install.sh runtime` 可从源码构建并安装。
运行 `./install.sh runtime IMAGE@sha256:DIGEST` 可从镜像仓库安装。
直接通过 Python 运行时，请以 `config.yml.sample` 为模板，并将
`PAPILIO_CONFIG` 指向配置文件。

检查需要 Python 3.13 和 Docker。测试使用隔离的 PostgreSQL 实例。
打包会在 `dist/` 生成 wheel、运行归档和归档校验和。

```bash
./install.sh test
bash scripts/ci/check.sh
bash scripts/ci/package.sh
```
