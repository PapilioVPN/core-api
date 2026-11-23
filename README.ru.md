<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/banner.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.png">
    <img alt="PapilioVPN Core API" src="assets/banner-light.png" width="100%">
  </picture>
</p>

<h1 align="center">PapilioVPN Core API</h1>

<p align="center" lang="ru">Центральный API управления PapilioVPN. Версия 0.0.0 включает управление доступом и проверку состояния системы.</p>

<p align="center">
  <a href="README.md" lang="en"><img src="assets/flags/gb.svg" width="24" alt=""> English</a> · <a href="README.fa.md" lang="fa"><img src="assets/flags/ir-lion-and-sun.svg" width="24" alt=""> فارسی</a> · <strong lang="ru"><img src="assets/flags/ru.svg" width="24" alt=""> Русский</strong> · <a href="README.zh-CN.md" lang="zh-CN"><img src="assets/flags/cn.svg" width="24" alt=""> 简体中文</a>
</p>

<p align="center">
  <a href="https://github.com/PapilioVPN/core-api/actions/workflows/check.yml"><img alt="Checks" src="https://github.com/PapilioVPN/core-api/actions/workflows/check.yml/badge.svg?branch=main"></a>
</p>

<p align="center">
  <a href="#quick-start">Быстрый запуск</a> ·
  <a href="#capabilities">Возможности</a> ·
  <a href="#management">API управления</a> ·
  <a href="#development">Разработка</a>
</p>

<a name="quick-start"></a>

## Быстрый запуск

На Linux amd64 с Docker Engine и Compose v2 скачайте артефакт из
[успешного запуска Checks](https://github.com/PapilioVPN/core-api/actions/workflows/check.yml). Распакуйте скачанный ZIP и замените
`YOUR_COMMIT_SHA` на идентификатор коммита из имени архива.
При первом запуске установщик загружает образы PostgreSQL и Redis.

```bash
archive=core-api-0.0.0-linux-amd64-YOUR_COMMIT_SHA.tar.gz
sha256sum -c "$archive.sha256" && tar -xzf "$archive"
cd core-api
./install.sh runtime
./run.sh runtime up
./run.sh runtime owner
curl -fsS http://127.0.0.1:8000/health
```

Установщик создаёт учётные данные в `.local/runtime`. При обновлении
сохраните этот каталог и том PostgreSQL. Команда owner запрашивает имя,
номер телефона и пароль, затем создаёт одного супер­администратора на базу.
По умолчанию API слушает `127.0.0.1:8000`. При запуске за обратным
прокси с TLS укажите `CORE_BIND` и `CORE_PORT`.

Эти команды показывают состояние и журналы, применяют миграции и
останавливают сервисы. После остановки данные PostgreSQL сохраняются.

```bash
./run.sh runtime status
./run.sh runtime logs
./run.sh runtime migrate
./run.sh runtime stop
```

Профиль jobs запускает процессы Scheduler, beat и Events вместе с
NATS JetStream. Scheduler удаляет историю просроченных токенов обновления.

```bash
CORE_JOBS=1 ./run.sh runtime up
```

<a name="capabilities"></a>

## Возможности

| Область | Операции |
| --- | --- |
| Аутентификация | Вход по паролю, ротация и отзыв токенов обновления. |
| Пользователи | Создание, просмотр, изменение и удаление пользователей, назначение ролей и управление паролями. Просмотр и изменение своего профиля и пароля. |
| Роли и разрешения | Управление ролями и областями доступа, единичное и пакетное назначение разрешений ролям. |
| Система | Проверка PostgreSQL и Redis. Метрики процессора, памяти, дисков, сети, датчиков и процессов доступны с соответствующим разрешением. |

<a name="management"></a>

## API управления

`GET /health` возвращает статус подключения и время сервера PostgreSQL.
Передайте `mobile` и `password` в `POST /admin/auth/tokens`. Токен доступа
используется как Bearer для `GET /admin/account/me`. Для `/admin/users`,
`/admin/roles`, `/admin/scopes` и `/admin/health` нужны соответствующие
разрешения.

<a name="development"></a>

## Разработка

В рабочей копии репозитория `./install.sh runtime` собирает и устанавливает
сервис из исходников. Образ из реестра устанавливается командой
`./install.sh runtime IMAGE@sha256:DIGEST`. Для запуска через Python создайте
конфигурацию на основе `config.yml.sample` и укажите её в `PAPILIO_CONFIG`.

Для проверок нужны Python 3.13 и Docker. Тесты используют изолированный
PostgreSQL. Wheel, архив и контрольная сумма записываются в `dist/`.

```bash
./install.sh test
bash scripts/ci/check.sh
bash scripts/ci/package.sh
```
