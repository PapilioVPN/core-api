"""Exercise scalar and bulk Xray revision removal against PostgreSQL."""

from asyncio import Event, TaskGroup, timeout
from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy import event, insert
from sqlalchemy.engine import Engine

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.scopes.app.interfaces.services import IScopeService
from src.apps.core.access.scopes.domain.dtos.records import ScopeCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.network.xray.assignments.infra.pg.repositories.records import (
    XrayAssignmentRepository,
)
from src.apps.network.xray.instances.infra.pg.tables import (
    XrayRestartRolloutTable,
    XrayStartTable,
)
from src.apps.network.xray.revisions.infra.pg.readers.records import (
    XrayRevisionReader,
)
from src.apps.network.xray.revisions.infra.pg.repositories.records import (
    XrayRevisionRepository,
)

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
PATH = "/admin/xray/revisions"
BULK = f"{PATH}/bulk/delete"


async def _revision(
    client: AsyncClient, headers: dict[str, str], label: str
) -> dict:
    response = await client.post(
        PATH,
        headers=headers,
        json={"config_json": f'{{"remarks":"removal-{label}"}}'},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def _node(
    client: AsyncClient, headers: dict[str, str], label: str
) -> int:
    response = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": label,
            "address": f"{label}.example.invalid",
            "port": 8443,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


async def test_remove_scalar_and_bulk(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000645", role_key="revision-removal"
    )
    single = (await _revision(client, headers, "single"))["id"]
    assert (await client.delete(f"{PATH}/{single}")).status_code == 401
    reply = await client.delete(f"{PATH}/{single}", headers=headers)
    assert reply.status_code == 204 and not reply.content
    assert (
        await client.get(f"{PATH}/{single}", headers=headers)
    ).status_code == 404
    assert (
        await client.delete(f"{PATH}/{single}", headers=headers)
    ).status_code == 404

    desired = (await _revision(client, headers, "desired"))["id"]
    operation = (await _revision(client, headers, "operation"))["id"]
    rollout = await _revision(client, headers, "rollout")
    removed = [
        (await _revision(client, headers, f"group-{index}"))["id"]
        for index in range(5)
    ]
    node_id = await _node(client, headers, "revision-removal")
    base = f"/admin/nodes/{node_id}/xray/instances/edge/desired-revision"
    assigned = await client.put(
        base, headers=headers, json={"revision_id": desired}
    )
    assert assigned.status_code == 200, assigned.text
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        uow = await scope.get(PGUnitOfWork)
        async with uow.transaction():
            await uow.execute(
                insert(XrayStartTable).values(
                    node_id=node_id,
                    instance_id="edge",
                    request_key=uuid4(),
                    address="revision-removal.example.invalid",
                    port=8443,
                    revision_id=operation,
                    state="succeeded",
                )
            )
            await uow.execute(
                insert(XrayRestartRolloutTable).values(
                    request_key=uuid4(),
                    revision_id=rollout["id"],
                    config_sha256=rollout["config_sha256"],
                    state="succeeded",
                )
            )

    for id in (desired, operation, rollout["id"]):
        reply = await client.delete(f"{PATH}/{id}", headers=headers)
        assert reply.status_code == 409, reply.text
        assert reply.json()["error"]["message_code"] == "xray_revision_in_use"
    for ids in ([], [True], ["1"], [1] * 101):
        body = await client.post(BULK, headers=headers, json={"ids": ids})
        assert body.status_code == 422, body.text

    commands: list[str] = []

    def observe_sql(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        sql = statement.strip().lower()
        if "tbl_xray_revisions" in sql:
            commands.append(sql.split(None, 1)[0])

    event.listen(Engine, "before_cursor_execute", observe_sql)
    try:
        reply = await client.post(
            BULK, headers=headers, json={"ids": removed[:1]}
        )
        assert reply.status_code == 200, reply.text
        assert commands == ["select", "delete"]
        commands.clear()
        ids = [
            desired,
            removed[1],
            single,
            operation,
            rollout["id"],
            *removed[2:],
            desired,
        ]
        reply = await client.post(BULK, headers=headers, json={"ids": ids})
        assert reply.status_code == 200, reply.text
        assert commands == ["select", "delete"]
        assert reply.json()["data"] == [
            {"revision_id": id, "status": status}
            for id, status in zip(
                ids[:-1],
                (
                    "in_use",
                    "deleted",
                    "not_found",
                    "in_use",
                    "in_use",
                    *("deleted",) * 3,
                ),
                strict=True,
            )
        ]
    finally:
        event.remove(Engine, "before_cursor_execute", observe_sql)

    for id in (desired, operation, rollout["id"]):
        assert (
            await client.get(f"{PATH}/{id}", headers=headers)
        ).status_code == 200
    assert (await client.get(base, headers=headers)).json()["data"]["desired"][
        "revision_id"
    ] == desired
    replay = await client.post(BULK, headers=headers, json={"ids": removed})
    assert replay.status_code == 200, replay.text
    assert [row["status"] for row in replay.json()["data"]] == [
        "not_found"
    ] * len(removed)


@pytest.mark.parametrize("first", ["assignment", "removal"])
async def test_remove_and_assignment_commit_in_order(
    app: FastAPI,
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    first: str,
) -> None:
    headers = await admin_headers(
        app,
        client,
        mobile="09120000646" if first == "assignment" else "09120000647",
        role_key=f"revision-removal-{first}-race",
    )
    id = (await _revision(client, headers, f"{first}-race"))["id"]
    node_id = await _node(client, headers, f"revision-removal-{first}-race")
    assignment = f"/admin/nodes/{node_id}/xray/instances/edge/desired-revision"
    entered = Event()
    waited = Event()
    release = Event()
    set_revision = XrayAssignmentRepository.set_revision
    remove = XrayRevisionRepository.remove_unreferenced_by_id

    async def hold_assignment(
        repo: XrayAssignmentRepository,
        node_id: int,
        instance_id: str,
        revision_id: int,
    ):
        entered.set()
        await release.wait()
        return await set_revision(repo, node_id, instance_id, revision_id)

    async def hold_removal(repo: XrayRevisionRepository, id: int):
        result = await remove(repo, id)
        entered.set()
        await release.wait()
        return result

    if first == "assignment":
        monkeypatch.setattr(
            XrayAssignmentRepository, "set_revision", hold_assignment
        )
        expected_lock = "FOR UPDATE"
    else:
        monkeypatch.setattr(
            XrayRevisionRepository, "remove_unreferenced_by_id", hold_removal
        )
        expected_lock = "FOR KEY SHARE"

    def observe_sql(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        if "tbl_xray_revisions" in statement and expected_lock in statement:
            waited.set()

    async def assign():
        response = await client.put(
            assignment, headers=headers, json={"revision_id": id}
        )
        return response

    async def delete():
        response = await client.delete(f"{PATH}/{id}", headers=headers)
        return response

    front, back = (
        (assign, delete) if first == "assignment" else (delete, assign)
    )
    event.listen(Engine, "before_cursor_execute", observe_sql)
    try:
        async with timeout(5), TaskGroup() as tasks:
            front_task = tasks.create_task(front())
            await entered.wait()
            back_task = tasks.create_task(back())
            await waited.wait()
            assert not back_task.done()
            release.set()
    finally:
        release.set()
        event.remove(Engine, "before_cursor_execute", observe_sql)
    first_response = front_task.result()
    second_response = back_task.result()
    assert (first_response.status_code, second_response.status_code) == (
        (200, 409) if first == "assignment" else (204, 404)
    ), (first_response.text, second_response.text)


async def test_save_retries_when_matching_revision_is_removed(
    app: FastAPI, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = await admin_headers(
        app,
        client,
        mobile="09120000648",
        role_key="revision-removal-save-race",
    )
    revision = await _revision(client, headers, "save-race")
    id = revision["id"]
    before_lookup = Event()
    release = Event()
    lock_by_digest = XrayRevisionReader.lock_by_digest

    async def hold_lookup(reader: XrayRevisionReader, digest: str):
        before_lookup.set()
        await release.wait()
        return await lock_by_digest(reader, digest)

    monkeypatch.setattr(XrayRevisionReader, "lock_by_digest", hold_lookup)
    async with timeout(5), TaskGroup() as tasks:
        saving = tasks.create_task(_revision(client, headers, "save-race"))
        await before_lookup.wait()
        response = await client.delete(f"{PATH}/{id}", headers=headers)
        assert response.status_code == 204, response.text
        release.set()
    replacement = saving.result()
    assert replacement["id"] != id
    assert replacement["config_sha256"] == revision["config_sha256"]


async def test_remove_requires_delete_permission(
    app: FastAPI, client: AsyncClient
) -> None:
    admin = await admin_headers(
        app, client, mobile="09120000649", role_key="revision-removal-admin"
    )
    container = cast(AsyncContainer, app.state.dishka_container)
    password = "isolated-xray-removal-test-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        scopes = await scope.get(IScopeService)
        users = await scope.get(IUserCreateCommand)
        network = await scopes.find_by_key("network")
        if network is None:
            network = await scopes.create(
                ScopeCreate(key="network", title="Network")
            )
        role = await roles.create(
            RoleCreate(
                key="revision-removal-operator",
                title="Revision removal operator",
            )
        )
        operator = await users.create(
            UserCreate(
                first_name="Xray",
                last_name="Operator",
                mobile="09120000650",
                role_id=role.id,
                password=password,
            )
        )
    grants = f"/admin/roles/{role.id}/scopes/batch"
    credentials = await client.post(
        "/admin/auth/tokens",
        json={"mobile": operator.mobile, "password": password},
    )
    assert credentials.status_code == 200, credentials.text
    token = credentials.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    ids = [
        (await _revision(client, admin, label))["id"]
        for label in ("grant-single", "grant-bulk")
    ]

    async def grant(method: str, permission: AdminPermission) -> None:
        response = await client.request(
            method,
            grants,
            headers=admin,
            json={
                "items": [{"scope_id": network.id, "permissions": permission}]
            },
        )
        assert response.status_code == 200, response.text

    await grant("POST", AdminPermission.CREATE)
    assert (
        await client.delete(f"{PATH}/{ids[0]}", headers=headers)
    ).status_code == 403
    assert (
        await client.post(BULK, headers=headers, json={"ids": ids})
    ).status_code == 403
    await grant("PATCH", AdminPermission.DELETE)
    assert (
        await client.delete(f"{PATH}/{ids[0]}", headers=headers)
    ).status_code == 204
    bulk = await client.post(BULK, headers=headers, json={"ids": ids[1:]})
    assert bulk.status_code == 200, bulk.text
    assert bulk.json()["data"] == [
        {"revision_id": ids[1], "status": "deleted"}
    ]
