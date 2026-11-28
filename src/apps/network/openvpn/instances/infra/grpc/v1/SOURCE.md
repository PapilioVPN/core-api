# Node OpenVPN gRPC contract

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/openvpn/instances/bridge/grpc/proto/v1/openvpn_instances.proto)
is pinned to revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
SHA-256: `4f9fb69f2c27cc2dde6ea7c0c4326dbb833080f4838e1021f848b34f898c4bb5`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/openvpn/instances/infra/grpc/v1/openvpn_instances.proto
```

See the [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
