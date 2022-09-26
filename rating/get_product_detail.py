import aiohttp
import asyncio
import async_timeout
from asyncio import Queue

import time
import datetime
import math
import random

from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import hashlib

class Crawler_product_detail:
    def __init__(self, max_fail_time=10, max_tasks=30):
        self.basepath = os.path.abspath(os.path.dirname(__file__))
        self.max_fail_time = max_fail_time
        self.max_tasks = max_tasks

        self.items_dict = {
            'shopid': [],
            'itemid': [],
            'rating_total': []
        }

    def __call__(self, result_product_id):
        async def parser_product_detail_html(html):

            products = json.loads(html)
            item = products['item']
            self.items_dict['shopid'].append(item['shopid'])
            self.items_dict['itemid'].append(item['itemid'])
            item_rating = item['item_rating']
            self.items_dict['rating_total'].append(item_rating['rating_count'][0])   

        async def fetch_coroutine(client, url, semaphore, fail_time=None):
            try:
                async with semaphore:
                    with async_timeout.timeout(10):
                        param = url.split('?')[-1]
                        param_MD5 = hashlib.md5(str(param).encode('utf-8')).hexdigest().lower()
                        text_hash = '55b03' + param_MD5 + '55b03'
                        if_none_match = hashlib.md5(str(text_hash).encode('utf-8')).hexdigest().lower()
                        if_none_match_other = '55b03-' + if_none_match

                        headers = {'User-Agent': 'Googlebot', 'if-none-match': if_none_match, 'if-none-match-': if_none_match_other}
                        async with client.get(url, headers=headers) as response:
                            html = await response.text()
                            assert response.status == 200
                            await parser_product_detail_html(html)

                        return await response.release()
            except Exception as e:
                if fail_time is None:
                    fail_time = 0
                print('fail--------------', e, url, fail_time)
                self.q.put_nowait((url, fail_time))

        async def fetch_fail_coroutine(client, semaphore):
            try:
                while True:
                    url, fail_time = await self.q.get()

                    if fail_time > self.max_fail_time:
                        self.q.task_done()
                        break
                    fail_time += 1
                    await fetch_coroutine(client, url, semaphore, fail_time)
                    print(url, fail_time)
                    self.q.task_done()

            except asyncio.CancelledError:
                pass
            except Exception as e:
                print('66666', e)

        async def main():

            self.q = asyncio.Queue()
            urls = result_product_id['url'].values.tolist()

            semaphore = asyncio.Semaphore(self.max_tasks)
            async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(ssl=False)
            ) as client:
                tasks = [
                    fetch_coroutine(client, url, semaphore) for url in urls
                ]
                await asyncio.gather(*tasks)

                tasks_fail = [
                    asyncio.create_task(fetch_fail_coroutine(
                        client, semaphore)) for _ in range(self.max_tasks)
                ]

                await self.q.join()
                for task in tasks_fail:
                    task.cancel()

        asyncio.run(main())
        df = pd.DataFrame(self.items_dict)

        df['url'] = 'https://shopee.vn/api/v2/item/get_ratings?itemid=' + df['itemid'].astype(str) + '&shopid=' + df['shopid'].astype(str) + '&rating_total=' + df['rating_total'].astype(str)

        df.to_csv(self.basepath + '/csv/product_detail.csv', index=False)

        return df


if __name__ == "__main__":
    time_start = time.time()

    basepath = os.path.abspath(os.path.dirname(__file__))
    result_product_id = pd.read_csv(basepath + '/csv/product_id.csv')

    crawler_product_detail = Crawler_product_detail()
    result_product_detail = crawler_product_detail(result_product_id)
    print(len(result_product_detail))
    print(time.time() - time_start)