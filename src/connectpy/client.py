import asyncio
import json
from enum import StrEnum
from types import TracebackType
from typing import Optional, Type
from urllib.parse import urljoin

import aiohttp
from betterproto import Casing
from grpclib import GRPCError
from grpclib.const import Cardinality, Status
from starlette.responses import Response


class UnaryUnaryClientStream:
    def __init__(
        self, channel, route, req_type, resp_type, timeout, deadline, metadata
    ):
        self.channel: "ConnectChannel" = channel
        self.route = route
        self.req_type = req_type
        self.resp_type = resp_type
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        if deadline is not None:
            raise Exception("Deadline is not yet supported")
        self.metadata = metadata
        self.req_future = None

    def get_url(self):
        return urljoin(self.channel.base_url, self.route)

    def get_headers(self):
        headers = {
            "connect-protocol-version": "1",
        }
        if self.channel.use_json:
            headers["content-type"] = "application/json"
        else:
            headers["content-type"] = "application/proto"
        return headers

    async def send_message(self, req, end=True):
        if self.channel.use_json:
            body = req.to_json(casing=Casing.SNAKE)
        else:
            body = bytes(req)
        headers = self.get_headers()
        self.req_future = self.channel.client.request(
            "POST",
            url=self.get_url(),
            data=body,
            headers=headers,
            timeout=self.timeout,
        )

    async def recv_message(self):
        if self.req_future is None:
            raise Exception("Trying to recv a message before sending one")
        resp_proto = self.resp_type()
        async with await self.req_future as resp:
            if resp.status == 200:
                body = await resp.read()
                if self.channel.use_json:
                    resp_proto.from_json(body)
                else:
                    resp_proto.parse(body)
            else:
                body = await resp.text()
                errdict = json.loads(body)
                code = errdict.get("code", None)
                if code is None:
                    raise GRPCError(
                        status=Status.UNKNOWN, message=errdict.get("message", None)
                    )
                else:
                    try:
                        status = Status[code.upper()]
                    except KeyError as k:
                        # There's a potential for a bug here; log it?
                        raise k
                raise GRPCError(status=status, message=errdict.get("message", None))

        return resp_proto

    async def __aenter__(self) -> "UnaryUnaryClientStream":
        return self

    async def __aexit__(
        self,
        _exc_type: Optional[Type[BaseException]],
        _exc_val: Optional[BaseException],
        _exc_tb: Optional[TracebackType],
    ) -> None:
        return None


class ConnectChannel:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        host: str | None = None,
        port: int | None = None,
        client: aiohttp.ClientSession | None = None,
        use_json: bool = False,
    ):
        if base_url is not None:
            self.base_url = base_url
        elif host is not None and port is not None:
            self.base_url = f"http://{host}:{port}/"
        else:
            raise Exception("One of base_url or host/port combo need to be provided")
        self.client: aiohttp.ClientSession = client or aiohttp.ClientSession()
        self.use_json = use_json

    def request(
        self,
        route,
        cardinality,
        req_type,
        response_type,
        timeout=None,
        deadline=None,
        metadata=None,
    ):
        if cardinality == Cardinality.UNARY_UNARY:
            return UnaryUnaryClientStream(
                self, route, req_type, response_type, timeout, deadline, metadata
            )
        raise Exception("Only unary calls are supported at the moment")

    async def close(self):
        await self.client.close()

    async def __aenter__(self) -> "ConnectChannel":
        return self

    async def __aexit__(
        self,
        _exc_type: Optional[Type[BaseException]],
        _exc_val: Optional[BaseException],
        _exc_tb: Optional[TracebackType],
    ) -> None:
        await self.close()
        return None
