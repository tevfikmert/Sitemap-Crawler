import asyncio
import time
import traceback
import sys
import cchardet

import logging

import aiohttp
from aiohttp.client_reqrep import ClientRequest

logger = logging.getLogger(__name__)


class ResponseTimer:
    start = None
    end = None
    time = None

    def __enter__(self):
        self._start = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end = time.monotonic()
        self.time = self._end - self._start
        return False


class ClientRequestWithTimer(ClientRequest):
    def __init__(self, *args, **kwargs):
        kwargs.pop('timer')
        super().__init__(
            timer=ResponseTimer(), *args, **kwargs
        )


# you can change with this option to increase timeout to await for response
READ_TIMEOUT_ON_REQUEST = 10
QUANTITY_ONETIME_REQUESTS = 100
INPUT_FILE = 'url-list.txt'
OUTPUT_FILE = 'final-output.csv'


def update_data(data, url, status, duration):
    _data = data
    if data[6] == 0:
        _data[0] = url
        _data[1] = status
        _data[5] = round(duration, 2)
    elif data[6] == 1:
        _data[2] = status
        _data[5] = round(data[5] + duration, 2)
    elif data[6] > 1:
        _data[3] = status
        _data[5] = round(data[5] + duration, 2)
    return _data


async def getStatus(url, session, output):

    data = [url.strip(), "ERR", "", "", "", '', 0]

    async def makeRecursiveRequest(url, session, previous_data):
        try:
            res = await session.head(url, timeout=READ_TIMEOUT_ON_REQUEST)
            data = update_data(
                previous_data, url, res.status, res._timer.time)
            if (res.status >= 300) and (res.status <= 399):
                if data[6] == 4:
                    return data
                data[4] = res.headers.get('Location')
                data[6] = data[6] + 1
                return await makeRecursiveRequest(
                    data[4],
                    session,
                    data
                )
            return data
        except aiohttp.ClientConnectionError as e:
            req_time = 0
            data = update_data(previous_data, url, "ERR", req_time)
            return data
        except Exception as e:
            req_time = 0
            data = update_data(previous_data, url, "ERR", req_time)
            return data

    returnValue = await makeRecursiveRequest(
        url.strip(),
        session,
        data
    )
    output.write(",".join(str(x) for x in returnValue) + '\n')
    return returnValue


async def save_results(allResults):
    with open("output.csv", "w") as f:
        for res in allResults:
            f.write(",".join(str(x) for x in res) + '\n')


async def doWork(urls, loop, session, output):
    await asyncio.gather(
        *[getStatus(url, session, output) for url in urls],
        loop=loop,
        return_exceptions=True
    )


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


async def main(urls, loop):
    output = open(OUTPUT_FILE, "w")
    count = 0
    for part in chunks(urls, QUANTITY_ONETIME_REQUESTS):
        print('in process from {} to {} urls'.format(
            count * QUANTITY_ONETIME_REQUESTS,
            (count + 1) * QUANTITY_ONETIME_REQUESTS
        ))
        count = count + 1
        conn = aiohttp.TCPConnector(
            limit=QUANTITY_ONETIME_REQUESTS,
            keepalive_timeout=5,
            verify_ssl=False
        )
        session = aiohttp.ClientSession(
            loop=loop,
            connector=conn,
            read_timeout=30,
            request_class=ClientRequestWithTimer
        )
        await doWork(
                part,
                loop,
                session,
                output
            )
        conn.close()
    output.close()


loop = asyncio.get_event_loop()


try:
    with open(INPUT_FILE, 'rb') as file:
        raw = file.read(32)
        encoding = cchardet.detect(raw)['encoding']

    starttime = time.time()
    print('detected encoding is: ',  encoding)
    with open(INPUT_FILE, 'r', encoding=encoding) as f:
        urls = f.readlines()

    loop.run_until_complete(main(urls, loop))
    endtime = time.time()
    print('Total time: ', endtime - starttime)
except KeyboardInterrupt:
    loop.close()

loop.close()
