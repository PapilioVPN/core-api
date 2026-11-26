# Node Xray configuration validation contract

Source: [Node configs.proto at 1e58d0696327d66819584d6a0ef4cc11a0b81d7d](https://github.com/PapilioVPN/node/blob/1e58d0696327d66819584d6a0ef4cc11a0b81d7d/internal/engines/xray/configs/bridge/grpc/proto/v1/configs.proto)

SHA-256: `fd1b7574b19d369dd549f150736f0c9ab8ac71824c116795eea9cc14922f18b6`

The schema is unmodified. The local path controls the generated Python import
path, not the Protobuf package or gRPC method names. From the Core root:

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/engines/xray/infra/grpc/v1/configs.proto
```

See the included [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
