# Node Hysteria gRPC contract

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/hysteria/instances/bridge/grpc/proto/v1/hysteria_instances.proto)
is pinned to revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
SHA-256: `cff5683c3d1548a6d27352cd3dd68ff7dfb8e2e2bf4094b45baa1b9c322c5ebf`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/hysteria/instances/infra/grpc/v1/hysteria_instances.proto
```

See the [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
