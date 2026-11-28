# Node Xray validation gRPC contract

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

See the [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
