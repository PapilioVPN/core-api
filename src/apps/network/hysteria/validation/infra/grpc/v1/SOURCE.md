# Node Hysteria gRPC contract

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/hysteria/configs/bridge/grpc/proto/v1/hysteria_configs.proto)
is pinned to revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
SHA-256: `7d3c093785274c78eb7c329e3a9edb46e1c8b66110dd5158ed699d8db8d977ca`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/hysteria/validation/infra/grpc/v1/hysteria_configs.proto
```

See the [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
