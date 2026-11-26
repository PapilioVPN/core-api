# Node Xray gRPC contracts

Source: [Node configs.proto at 1e58d0696327d66819584d6a0ef4cc11a0b81d7d](https://github.com/PapilioVPN/node/blob/1e58d0696327d66819584d6a0ef4cc11a0b81d7d/internal/engines/xray/configs/bridge/grpc/proto/v1/configs.proto)

SHA-256: `fd1b7574b19d369dd549f150736f0c9ab8ac71824c116795eea9cc14922f18b6`

The configuration validation schema is unmodified.

- [instances.proto](https://github.com/PapilioVPN/node/blob/1e58d0696327d66819584d6a0ef4cc11a0b81d7d/internal/engines/xray/instances/bridge/grpc/proto/v1/instances.proto)
  upstream SHA-256 `973ad88e291e5b9cf4a779f99002794fd1b3273ec1950eb3dc95d004d22eccbd`.
  Only its accounts import path is relocated for Python code generation.
  Local SHA-256 `fb79826f74986838d765f795533e9bd9bf14816e4a8b3843dcae3a76b3aa6508`.
- [accounts.proto](https://github.com/PapilioVPN/node/blob/1e58d0696327d66819584d6a0ef4cc11a0b81d7d/internal/engines/xray/accounts/bridge/grpc/proto/v1/accounts.proto)
  is an unmodified type dependency, SHA-256
  `449584494c5dc636e072a8cf76072892c2549ecec2eac59eb9dddea8c4665b84`.
  Core does not generate an accounts RPC client for this dependency.

The local paths control Python imports, not the Protobuf packages, field
numbers or gRPC method names. Regenerate from the Core root:

```sh
contract=src/apps/network/engines/xray/infra/grpc/v1
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. \
  "$contract/configs.proto" "$contract/instances.proto" "$contract/accounts.proto"
python -m grpc_tools.protoc -I. --grpc_python_out=. \
  "$contract/configs.proto" "$contract/instances.proto"
```

See the included [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
