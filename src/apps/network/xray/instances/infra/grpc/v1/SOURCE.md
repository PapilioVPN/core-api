# Node Xray instance gRPC contract

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

See the [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
