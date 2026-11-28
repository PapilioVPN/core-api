# PapilioVPN Node gRPC v1 contracts

Core uses the checked-in Protobuf contracts and Python stubs. Use the pinned
`grpcio-tools` test dependency to regenerate the stubs from the Core API root.
Local schema paths determine Python imports. The Protobuf package names,
field numbers and gRPC methods follow the pinned Node contracts.

See the [PapilioVPN Node license](../../src/apps/network/nodes/observations/infra/grpc/v1/LICENSE).

## HostService

Source: [Node host.proto at 1e58d0696327d66819584d6a0ef4cc11a0b81d7d](https://github.com/PapilioVPN/node/blob/1e58d0696327d66819584d6a0ef4cc11a0b81d7d/internal/host/bridge/grpc/proto/v1/host.proto)

SHA-256: `1ad2cab7145357293a1db08e016462a8d6f1f28539bb69b2c26bfeea7caf58a8`

The copied source is unmodified. The local file path determines the Python
import path. The Protobuf package and gRPC method names are unchanged.
Regenerate the checked-in stubs from the Core root using the pinned dev extra:

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/nodes/observations/infra/grpc/v1/host.proto
```

## Xray instances and accounts

The source is pinned to Node revision
`1e58d0696327d66819584d6a0ef4cc11a0b81d7d`.

- [instances.proto](https://github.com/PapilioVPN/node/blob/1e58d0696327d66819584d6a0ef4cc11a0b81d7d/internal/engines/xray/instances/bridge/grpc/proto/v1/instances.proto)
  upstream SHA-256 `973ad88e291e5b9cf4a779f99002794fd1b3273ec1950eb3dc95d004d22eccbd`.
  Only its accounts import path is relocated for Python code generation.
  Local SHA-256 `6d21596ba592a6e98f9cfdb795ecbc95ca57377bf09ac27c76fa43c869fe4de6`.
- [accounts.proto](https://github.com/PapilioVPN/node/blob/1e58d0696327d66819584d6a0ef4cc11a0b81d7d/internal/engines/xray/accounts/bridge/grpc/proto/v1/accounts.proto)
  is an unmodified type dependency, SHA-256
  `449584494c5dc636e072a8cf76072892c2549ecec2eac59eb9dddea8c4665b84`.
  Core shares these message types between the instance contract and the
  AccountsService client. Only `CountVLESSAccounts` is wired to the Panel.

Local paths control Python imports. Protobuf package names, field numbers
and gRPC method names follow the Node contract. Regenerate from the Core root.

```sh
contract=src/apps/network/xray/instances/infra/grpc/v1
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. \
  "$contract/accounts.proto" "$contract/instances.proto"
python -m grpc_tools.protoc -I. --grpc_python_out=. \
  "$contract/accounts.proto" "$contract/instances.proto"
```

## Xray live logs

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/logs/bridge/grpc/proto/v1/logs.proto) is pinned to `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
Its SHA-256 is `09612d8599c0ad97cd9e7bd5dd1977913644c210895adfb75a1099318f7336f1`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/xray/logs/infra/grpc/v1/logs.proto
```

## Xray outbounds

Pinned to Node revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.

- [outbounds.proto](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/outbounds/bridge/grpc/proto/v1/outbounds.proto)
  Upstream SHA-256 `2ecf04d3db14891731537ddd800999e548045cb7ac7087070e8f815b0e0a7d64`.

Regenerate from the Core root.

```sh
contract=src/apps/network/xray/outbounds/infra/grpc/v1
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. \
  "$contract/outbounds.proto"
python -m grpc_tools.protoc -I. --grpc_python_out=. "$contract/outbounds.proto"
```

## Xray routing

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/routing/bridge/grpc/proto/v1/routing.proto) is pinned to `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
Its SHA-256 is `32c6fa59c991114eb5f7b254d473ec1818dcd7e84ef1607806ddcc2313ed0348`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/xray/routing/infra/grpc/v1/routing.proto
```

## Xray stats

Pinned to Node revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.

- [runtime_stats.proto](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/stats/bridge/grpc/proto/v1/runtime_stats.proto)
  Upstream SHA-256 `dba5ba91c36b6e58f66fe675237225e640c899b1ce32ff6304dfa84ece13c714`.
  Local SHA-256 `0138f2281dcbc12e1ff9cb8fb2ca64ffbb9a6316f0a21f88d3097221f6e7f854` after Python import relocation.
- [traffic.proto](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/stats/bridge/grpc/proto/v1/traffic.proto)
  Upstream SHA-256 `3b8eafb82541298763581020fb08a2f77fea73d905d14871b1afc8bd10b7d199`.
- [online.proto](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/stats/bridge/grpc/proto/v1/online.proto)
  Upstream SHA-256 `5aedd661371b79d7e1d6fab5b6ce258ecc86cb71e8cd8e6919a6d2f26e46cf64`.

Regenerate from the Core root.

```sh
contract=src/apps/network/xray/stats/infra/grpc/v1
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. \
  "$contract/runtime_stats.proto" "$contract/traffic.proto" "$contract/online.proto"
python -m grpc_tools.protoc -I. --grpc_python_out=. "$contract/runtime_stats.proto"
```

## Xray validation

The [configs.proto source](https://github.com/PapilioVPN/node/blob/1e58d0696327d66819584d6a0ef4cc11a0b81d7d/internal/engines/xray/configs/bridge/grpc/proto/v1/configs.proto)
is unmodified and pinned to Node revision
`1e58d0696327d66819584d6a0ef4cc11a0b81d7d`.
Its SHA-256 is
`fd1b7574b19d369dd549f150736f0c9ab8ac71824c116795eea9cc14922f18b6`.

Regenerate from the Core root.

```sh
contract=src/apps/network/xray/validation/infra/grpc/v1
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  "$contract/configs.proto"
```

## WireGuard interfaces

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/wireguard/interfaces/bridge/grpc/proto/v1/interfaces.proto)
is pinned to revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
SHA-256: `6a4074c82cf2ad675c350867d07476aa1ac0ecb7f5091958fbfcd9db96683957`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/wireguard/interfaces/infra/grpc/v1/interfaces.proto
```

## WireGuard diagnostics

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/wireguard/diagnostics/bridge/grpc/proto/v1/wireguard_diagnostics.proto)
is pinned to revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
SHA-256: `38710d56a3258143ec19475a5f980435e15950856c4e82ef7c363e8dda270ca3`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/wireguard/diagnostics/infra/grpc/v1/wireguard_diagnostics.proto
```

## OpenVPN instances, configuration and sessions

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/openvpn/instances/bridge/grpc/proto/v1/openvpn_instances.proto)
is pinned to revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
SHA-256: `4f9fb69f2c27cc2dde6ea7c0c4326dbb833080f4838e1021f848b34f898c4bb5`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/openvpn/instances/infra/grpc/v1/openvpn_instances.proto
```

## Hysteria instances

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/hysteria/instances/bridge/grpc/proto/v1/hysteria_instances.proto)
is pinned to revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
SHA-256: `cff5683c3d1548a6d27352cd3dd68ff7dfb8e2e2bf4094b45baa1b9c322c5ebf`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/hysteria/instances/infra/grpc/v1/hysteria_instances.proto
```

## Hysteria validation

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/hysteria/configs/bridge/grpc/proto/v1/hysteria_configs.proto)
is pinned to revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
SHA-256: `7d3c093785274c78eb7c329e3a9edb46e1c8b66110dd5158ed699d8db8d977ca`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/hysteria/validation/infra/grpc/v1/hysteria_configs.proto
```

## Hysteria stats

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/hysteria/stats/bridge/grpc/proto/v1/hysteria_stats.proto)
is pinned to revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
SHA-256: `22c42925d772f6490ebeb087a194397980e88ca480558729e59cc47b37934b56`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/hysteria/stats/infra/grpc/v1/hysteria_stats.proto
```
