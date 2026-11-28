# Node WireGuard gRPC contract

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/wireguard/interfaces/bridge/grpc/proto/v1/interfaces.proto)
is pinned to revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
SHA-256: `6a4074c82cf2ad675c350867d07476aa1ac0ecb7f5091958fbfcd9db96683957`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/wireguard/interfaces/infra/grpc/v1/interfaces.proto
```

See the [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
