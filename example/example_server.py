import argparse
import asyncio

from grpclib.server import Server as GRPCServer
from proto.svc.v1 import (CapsRequest, CapsResponse, CapsServiceBase,
                          MustErrorRequest, MustErrorResponse)

from connectpy import GRPCError
from connectpy import Server as ConnectServer
from connectpy import Status

parser = argparse.ArgumentParser(description="Run a connect or GRPC server")
parser.add_argument("--grpc", default=False, action="store_true")
parser.add_argument("--hostport", default="0.0.0.0:5001")


class CapsService(CapsServiceBase):
    async def caps(self, caps_request: CapsRequest) -> CapsResponse:
        return CapsResponse(msg=caps_request.msg.upper())

    async def must_error(
        self, must_error_request: MustErrorRequest
    ) -> MustErrorResponse:
        raise GRPCError(status=Status.INTERNAL, message=must_error_request.err_msg)


async def main():
    args = parser.parse_args()
    host, port = args.hostport.split(":")
    svc = CapsService()
    if args.grpc:
        server = GRPCServer([svc])
        await server.start(host, int(port))
        await server.wait_closed()
    else:
        server = ConnectServer([svc])
        await server.start(host, int(port))


if __name__ == "__main__":
    asyncio.run(main())
