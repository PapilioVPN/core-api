# Node HostService contract

Source: [Node host.proto at 1e58d0696327d66819584d6a0ef4cc11a0b81d7d](https://github.com/PapilioVPN/node/blob/1e58d0696327d66819584d6a0ef4cc11a0b81d7d/internal/host/bridge/grpc/proto/v1/host.proto)

SHA-256: `1ad2cab7145357293a1db08e016462a8d6f1f28539bb69b2c26bfeea7caf58a8`

The copied source is unmodified. The local file path determines the Python
import path. The Protobuf package and gRPC method names are unchanged.
Regenerate the checked-in stubs from the Core root using the pinned dev extra:

```sh
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
  src/apps/network/nodes/infra/grpc/v1/host.proto
```

The checked-in contract and generated files do not require a Node checkout to
build or run Core. See the upstream license included in this directory.
