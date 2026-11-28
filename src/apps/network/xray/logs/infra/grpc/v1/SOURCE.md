# Node Xray live-log gRPC contract

The unmodified [Node schema](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/logs/bridge/grpc/proto/v1/logs.proto) is pinned to `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.
Its SHA-256 is `09612d8599c0ad97cd9e7bd5dd1977913644c210895adfb75a1099318f7336f1`.

Regenerate from the Core root.

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/xray/logs/infra/grpc/v1/logs.proto
```

See the [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
