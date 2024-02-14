import json
from typing import Any

import uvicorn
from betterproto import Casing
from grpclib import GRPCError, Status
from grpclib.const import Cardinality
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route


class FakeUnaryServerStream:
    def __init__(self, req):
        self.req = req
        self.resp = None

    async def recv_message(self):
        return self.req

    async def send_message(self, msg):
        self.resp = msg


_PROTO_MIME = "application/proto"
_JSON_MIME = "application/json"


def grpc_error_to_response(err: GRPCError) -> Response:
    body = {
        "code": err.status.name.lower(),
    }
    if err.message is not None:
        body["message"] = err.message
    if err.details is not None:
        body["details"] = err.details
    return Response(content=json.dumps(body), status_code=500)


def _mk_unary_unary(handle):
    async def inner_call(req: Request) -> Response:
        mime = req.headers.get("Content-type", "").lower()
        body = await req.body()
        preq = handle.request_type()
        if mime == _PROTO_MIME:
            preq.parse(body)
        elif mime == _JSON_MIME:
            preq.from_json(body)
        else:
            raise Exception("Invalid Connect Content-type")
        stream = FakeUnaryServerStream(preq)
        try:
            await handle.func(stream)
        except GRPCError as e:
            return grpc_error_to_response(e)
        except Exception as e:
            e = GRPCError(Status.UNKNOWN, message=f"{e}")
            return grpc_error_to_response(e)

        assert stream.resp is not None
        if mime == _PROTO_MIME:
            return Response(content=bytes(stream.resp), media_type=_PROTO_MIME)
        elif mime == _JSON_MIME:
            return Response(
                content=stream.resp.to_json(casing=Casing.SNAKE), media_type=_JSON_MIME
            )
        else:
            raise Exception("Invalid Connect Content-type")

    return inner_call


class Server:
    def __init__(self, services: list[Any]):
        self.services = services

    def make_app(self) -> Starlette:
        routes = []
        for svc in self.services:
            # We have to trust that these are generated ServiceBase classes,
            # because the ABC for ServiceBase does not contain this.
            mapping = svc.__mapping__()
            # func, cardinality, request_type, reply_type
            for path, handle in mapping.items():
                if handle.cardinality != Cardinality.UNARY_UNARY:
                    raise Exception("Can only handle Unary/Unary endpoints for now")
                routes.append(
                    Route(path=path, endpoint=_mk_unary_unary(handle), methods=["POST"])
                )
        return Starlette(routes=routes)

    async def start(self, host: str, port: int):
        router = self.make_app()
        config = uvicorn.Config(app=router, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()
