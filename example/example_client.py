import argparse
import asyncio

from grpclib.client import Channel
from proto.svc.v1 import CapsRequest, CapsServiceStub, MustErrorRequest

from connectpy import ConnectChannel, GRPCError

parser = argparse.ArgumentParser(description="Run a connect or GRPC server")
parser.add_argument("--grpc", default=False, action="store_true")
parser.add_argument("--hostport", default="127.0.0.1:5001")
parser.add_argument("--msg", default="hello world")


async def main():
    args = parser.parse_args()
    host, port = args.hostport.split(":")
    if args.grpc:
        channel = Channel(host=host, port=int(port))
    else:
        channel = ConnectChannel(host=host, port=int(port))
    async with channel:
        svc = CapsServiceStub(channel)  # type: ignore
        resp = await svc.caps(caps_request=CapsRequest(msg=args.msg))
        print(f"Got response! caps message = {resp.msg}")
        try:
            resp = await svc.must_error(
                MustErrorRequest(err_msg="this is inside the Python err_msg")
            )
        except GRPCError as g:
            print(f"Got GRPC error: {g}")


if __name__ == "__main__":
    asyncio.run(main())
