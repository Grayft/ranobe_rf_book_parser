import asyncio
import aiohttp
from main import URLS, HEADERS, logger
from main import (
    get_finding_tag_text,
    get_finding_tags_text,
    get_parsing_url_dict,
    get_book_json,
    get_max_page,
)


@logger.catch(reraise=True)
async def aget_chapter_text(session: aiohttp.ClientSession,
                            num_chapter: float,
                            part_url: str) -> dict:
    """Функция парсит текст главы книги"""

    url = URLS.get('site')[:-1] + part_url
    async with session.get(url, headers=HEADERS) as response:
        
        resp_text = await response.text()
        if response.status:
            title = get_finding_tag_text(
                resp_text, 'h1',
                attrs={'class': 'font-medium text-2xl md:text-3xl pb-3'}
            )
            paragraph_list = [p.text for p in get_finding_tags_text(
                resp_text, 'p', attrs={})]
            chapter_text = '\n'.join(paragraph_list)
            if chapter_text:
                return {num_chapter: f'{title}\n{chapter_text}\n\n\n'}
    raise Exception(f'Не удалось загрузить страницу c главой {num_chapter}!\n'
                    f'URL:  {response.url}')


async def aget_chapters_from_site(parsing_url_dict: dict) -> dict:
    """Возращает текст всех глав книги"""
    tasks = []
    async with aiohttp.ClientSession() as session:
        for num, url in parsing_url_dict.items():
            task = asyncio.create_task(
                aget_chapter_text(session, num, url))
            tasks.append(task)
        chapters_text_dicts = await asyncio.gather(*tasks)
        chapters_dict = gather_dicts_in_one(chapters_text_dicts)
        return chapters_dict


def get_chapters_text_dict(load_params: dict, book_json: dict) -> dict:
    """Парсит главы сайта по ссылкам из url_dict.
        Возвращает словарь dict = {номер главы: текст главы}"""

    logger.info('Начало парсинга глав.')
    parsing_url_dict = get_parsing_url_dict(
        load_params, book_json['props']['pageProps']['book']['chapters'])

    loop = asyncio.get_event_loop()
    chapters_dict = loop.run_until_complete(
        aget_chapters_from_site(parsing_url_dict))

    logger.success('Конец парсинга глав.')
    return chapters_dict


async def aget_books_url_on_page(
        session: aiohttp.ClientSession, page_num: int) -> dict:

    books_url = {}
    async with session.get(URLS['books'], headers=HEADERS,
                           params={'page': page_num}) as response:
        resp_text = await response.text()
        if response.status == 200:
            books_json = get_book_json(resp_text)

            for book in books_json['props']['pageProps']['totalData']['items']:
                books_url[book['title']] = book['url']
            return books_url
        raise Exception(f'Не удалось загрузить страницу: {response.url}')


async def aget_all_books_url(max_page: int) -> dict:
    '''Возвращает словарь всех книг на сайте.
        dict = {название книги: url}'''
    tasks = []
    async with aiohttp.ClientSession() as session:
        for page_num in range(1, max_page + 1):
            task = asyncio.create_task(
                aget_books_url_on_page(session, page_num))
            tasks.append(task)
        books_dicts = await asyncio.gather(*tasks)
        all_books_dict = gather_dicts_in_one(books_dicts)
        return all_books_dict

def get_all_books_url() -> dict:
    '''Возвращает словарь всех книг на сайте.
        dict = {название книги: url}'''

    max_book_page = get_max_page(URLS['books'])
    loop = asyncio.get_event_loop()
    books_url = loop.run_until_complete(aget_all_books_url(max_book_page))

    logger.info('Начало просмотра всех книг.')

    return books_url


def gather_dicts_in_one(dicts_list: list) -> dict:
    """Возвращает обьединенный словарь"""
    res_dict = {}
    for one_dict in dicts_list:
        res_dict.update(one_dict)
    return res_dict