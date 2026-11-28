# Node Xray outbounds gRPC contract

Pinned to Node revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.

- [outbounds.proto](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/outbounds/bridge/grpc/proto/v1/outbounds.proto)
  Upstream SHA-256 `2ecf04d3db14891731537ddd800999e548045cb7ac7087070e8f815b0e0a7d64`.

Regenerate from the Core root.

```sh
contract=src/apps/network/xray/outbounds/infra/grpc/v1
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. \
  "$contract/outbounds.proto"
python -m grpc_tools.protoc -I. --grpc_python_out=. "$contract/outbounds.proto"
```

See the [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
