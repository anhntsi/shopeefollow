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


class Crawler_product_rating:
    def __init__(self, max_fail_time=10, max_tasks=30):
        self.basepath = os.path.abspath(os.path.dirname(__file__))
        self.max_fail_time = max_fail_time
        self.max_tasks = max_tasks

        self.items_dict = {
            'itemid': [],
            'author_shopid': [],
            'userid': []
        }

    def __call__(self, result_product_id):
        async def parser_product_detail_html(html):

            products = json.loads(html)
            item = products['data']
            items_type = item['ratings']

            if items_type:
                for i in range(len(items_type)):
                    self.items_dict['itemid'].append(items_type[i]['itemid'])
                    self.items_dict['author_shopid'].append(str(items_type[i]['author_shopid']))
                    self.items_dict['userid'].append(items_type[i]['userid'])

        async def fetch_coroutine(client, url, semaphore, fail_time=None):
            try:
                async with semaphore:
                    with async_timeout.timeout(10):
                        async with client.get(url) as response:
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
            crawler_product_urls = []
            limit = 50
            for i in range(len(urls)):
                url = urls[i]
                rating_total = int([i.split("=")[-1] for i in url.split("?", 1)[-1].split("&") if i.startswith('rating_total' + "=")][0])
                if rating_total > 0:
                    page = int(rating_total / limit)
                    for j in range(page):
                        newUrl = url.replace('&rating_total=' + str(rating_total), '&limit=50&offset=' + str(j*50))
                        crawler_product_urls.append(newUrl)
                else:
                    newUrl = url.replace('&rating_total=' + str(rating_total), '&limit=50&offset=0')
                    crawler_product_urls.append(newUrl)
            
            headers = {'User-Agent': 'Googlebot'}
            semaphore = asyncio.Semaphore(self.max_tasks)
            async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(ssl=False),
                    headers=headers,
            ) as client:
                tasks = [
                    fetch_coroutine(client, url, semaphore) for url in crawler_product_urls
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

        df.to_csv(self.basepath + '/csv/product_rating.csv', index=False)

        return df


if __name__ == "__main__":
    time_start = time.time()

    basepath = os.path.abspath(os.path.dirname(__file__))
    result_product_id = pd.read_csv(basepath + '/csv/product_detail.csv')

    crawler_product_rating = Crawler_product_rating()
    result_product_rating = crawler_product_rating(result_product_id)
    print(len(result_product_rating))
    print(time.time() - time_start)