# connectpy

An implementation of the [Buf Connect](https://connectrpc.com/) protocol for Python, atop [betterproto](https://github.com/danielgtaylor/python-betterproto) atop [Starlette](https://www.starlette.io/) and, therefore, compatible interfaces (eg, [FastAPI](https://fastapi.tiangolo.com/))

If you're already using [grpclib](https://github.com/vmagamedov/grpclib) it's aiming to be a drop-in replacement to allow HTTP/1.1 compatibility. If you're not, it allows you to adopt gRPC on your HTTP/1.1 infrastructure, and slowly migrate to full-blown gRPC. However, a current limitation is that it can only run in one mode or the other for now.

By emulating the grpclib server/client instances, this gives an option for using the same gRPC server and client classes, and only change the implementation underneath at creation time.

## Examples

`/example` is full of all the cross-compatibility examples.

### Run the Python server
```
python example/example_server.py
```

Runs immediately in Connect mode. Adding the `--grpc` flag switches to using `grpclib` and all the HTTP/2, default gRPC listeners instead.

### Run the Python client
```
python example/example_client.py
```
Runs a client to make a few requests against either compatible server (below). Again, adding `--grpc` will connect over HTTP/2 using grpclib vs 1.1 and connectpy

### Run the Go server

```
cd example/go; go run ./cmd/server
```

Runs a Go reference server in full Buf Connect mode. As per the [Buf Connect Go example](https://connectrpc.com/docs/go/getting-started)  it supports both modes of operation, so running a Python client with either `--grpc` or not will work fine.

### Run the Go client
```
cd example/go; go run ./cmd/client
```

Runs a Go reference client using the Buf Connect library. As per the [Buf Connect Go example](https://connectrpc.com/docs/go/getting-started)  it supports both modes of operation, which requires a slight code change, so `--grpc` exists here too, to connect to either server in the appropriate mode. (connectpy, as a server, doesn't do both simultaneously, for now, but if you're ambitious that would be amazing)


## Wishlist

- [ ] betterproto 2.0 release!
  - [ ] betterproto Buf plugin release
- [ ] betterproto to support metadata passing
- [ ] support both gRPC and Buf/HTTP/1.1 simultaneously in connectpy's server

## Development
This repo assumes you have the appropriate virtualenvs set up. 
The developer prefers [rye](https://rye-up.com/).
If you feel like contributing, however, you do you -- the best part of rye is that it's a standard python package.

