# Node Xray stats gRPC contract

Pinned to Node revision `01bc80696b1e56b7c65a47b7ab516df9b25bc99b`.

- [runtime_stats.proto](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/stats/bridge/grpc/proto/v1/runtime_stats.proto)
  Upstream SHA-256 `dba5ba91c36b6e58f66fe675237225e640c899b1ce32ff6304dfa84ece13c714`.
  Local SHA-256 `0138f2281dcbc12e1ff9cb8fb2ca64ffbb9a6316f0a21f88d3097221f6e7f854` after Python import relocation.
- [traffic.proto](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/stats/bridge/grpc/proto/v1/traffic.proto)
  Upstream SHA-256 `3b8eafb82541298763581020fb08a2f77fea73d905d14871b1afc8bd10b7d199`.
- [online.proto](https://github.com/PapilioVPN/node/blob/01bc80696b1e56b7c65a47b7ab516df9b25bc99b/internal/engines/xray/stats/bridge/grpc/proto/v1/online.proto)
  Upstream SHA-256 `5aedd661371b79d7e1d6fab5b6ce258ecc86cb71e8cd8e6919a6d2f26e46cf64`.

Regenerate from the Core root.

```sh
contract=src/apps/network/xray/stats/infra/grpc/v1
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. \
  "$contract/runtime_stats.proto" "$contract/traffic.proto" "$contract/online.proto"
python -m grpc_tools.protoc -I. --grpc_python_out=. "$contract/runtime_stats.proto"
```

See the [PapilioVPN Node license](../../../../../nodes/infra/grpc/v1/LICENSE).
