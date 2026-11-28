# Node Xray routing gRPC contract

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/routing/bridge/grpc/proto/v1/routing.proto) is pinned to `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
Its SHA-256 is `32c6fa59c991114eb5f7b254d473ec1818dcd7e84ef1607806ddcc2313ed0348`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/xray/routing/infra/grpc/v1/routing.proto
```

See the [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
