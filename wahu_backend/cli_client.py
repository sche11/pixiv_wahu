import json
import aiohttp
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Optional, TYPE_CHECKING

from .wahu_config import load_config
from .constants import postRPCURL
from .wahu_methods import WahuMethods

if TYPE_CHECKING:
    from inspect import Traceback

    from .wahu_core import WahuMethod, WahuContext

    ClientBase = WahuMethods

    __ = WahuContext()  # type: ignore
else:
    ClientBase = object

    __ = None


class WahuRemoteError(Exception):
    def __init__(self, err: str):
        self.err = err

    def __str__(self) -> str:
        return self.err


class WahuRPCClient(ClientBase):
    """使用 POST RPC 接口和后端通信"""

    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url

    async def __aenter__(self) -> 'WahuRPCClient':
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self,
        excpt_type: Optional[type] = None,
        excpt_value: Optional[Exception] = None,
        excpt_tcbk: Optional['Traceback'] = None):

        await self.session.close()

        if excpt_value != None:
            raise excpt_value

    async def call(self, method: str, args: dict[str, Any]) -> Any:

        async with self.session.post(self.rpc_url, data=json.dumps({
            'method': method,
            'args': args
        })) as resp:

            ret = await resp.json()

        if ret['type'] == 'exception':
            raise WahuRemoteError(ret['return'])

        if ret['type'] == 'normal':
            return ret['return']

        if ret['type'] == 'generator':

            gen_key = ret['return']

            async def gen() -> AsyncGenerator[Any, Any]:
                send_val = None
                while True:
                    ret_val = await self.call(
                        'wahu_anext',
                        {'key': gen_key, 'send_val': send_val}
                    )

                    if ret_val is None:
                        break

                    send_val = yield ret_val

            return gen()

    def __getattr__(self, name: str) -> Callable[..., Any]:

        m: WahuMethod = getattr(WahuMethods, name)

        async def f(*args: tuple[Any, ...]) -> Any:

            args = args[1:]  # 删除第一个 ctx

            if len(args) != len(m.arg_names):
                raise ValueError(f'方法 {name} 的参数数量错误. 应为 {len(m.arg_names)}')

            args_dict = {
                n: val for n, val in zip(m.arg_names, args)
            }

            return await self.call(name, args_dict)
        return f


async def main(args: list[str], conf_path: Path):

    conf = load_config(conf_path)

    backend_host = '127.0.0.1' if conf.server_host == '0.0.0.0' else conf.server_host
    rpc_url = f'http://{backend_host}:{conf.server_port}{postRPCURL}'

    async with WahuRPCClient(rpc_url) as client:

        try:

            agen = await client.wahu_client_exec(__, args)

            send_val = None
            while True:
                try:
                    val = await agen.asend(send_val)

                    if val is None:
                        break

                    else:
                        if val == '[:input]':
                            send_val = input()
                        else:
                            print(val, end='', flush=True)

                except StopAsyncIteration:
                    break

        except WahuRemoteError as wre:
            print(wre)
            return 1

        except aiohttp.ClientConnectorError as e:
            print(f'无法连接后端: {str(e)}')
            return 1

    return 0



