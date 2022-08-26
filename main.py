from multiprocessing import reduction
from urllib import request, response
import requests
from bs4 import BeautifulSoup
from json import loads, dumps
from time import sleep
import re
from typing import AnyStr, List, Dict
from loguru import logger
import os


# 'https://ранобэ.рф'
URLS = {'site': 'https://xn--80ac9aeh6f.xn--p1ai/',
        'books': 'https://xn--80ac9aeh6f.xn--p1ai/books/'}
URL = 'https://xn--80ac9aeh6f.xn--p1ai/silyneyshaya-sistema-ubiystva-drakonov'
URL = 'https://xn--80ac9aeh6f.xn--p1ai/ubegaya-ot-geroya'
# URL = 'https://xn--80ac9aeh6f.xn--p1ai/silyneyshaya-sistema-ubiystva-drakonov/glava-1-silyneyshaya-sistema-ubiystva-drakonov'
HEADERS = []


def get_finding_tag_text(content: AnyStr, tag: str, attrs: dict) -> AnyStr:
    """В сдержимом ищет нужный тег с аттрибутами и выводит его содержание"""
    soup = BeautifulSoup(content, features='html.parser')
    data = soup.find(name=tag, attrs=attrs)
    return data.get_text()


def get_finding_tags_text(content: AnyStr, tag: str, attrs: dict) -> list:
    """В сдержимом ищет нужный тег с аттрибутами и выводит его содержание"""
    soup = BeautifulSoup(content, features='html.parser')
    data = soup.find_all(name=tag, attrs=attrs)
    return data


@logger.catch(reraise=True)
def get_book_json(content: AnyStr) -> dict:
    """Возвращает json, в котором хранится данные о книге, главах и много
    всего другого"""

    if content:
        book_data = get_finding_tag_text(content, 'script',
                                         attrs={'id': '__NEXT_DATA__'})
        return loads(book_data)
    raise Exception('Пустой content а странице книги!')


logger.catch(reraise=True)


def get_chosen_url_dict(load_params: dict, chapters: dict) -> dict:
    """Возвращает словарь с url нужных глав из всех глав книги
        dict = {номер главы: url}
    """

    chosen_chapters_url_dict = {}
    for num_chapter, chapter_data in chapters.items():
        if load_params['num_chapter_start'] <= num_chapter <= load_params['num_chapter_end']:
            if not chapter_data['isaccessible']:
                raise Exception(
                    f'Нельзя спарсить, т.к. глава {num_chapter} имеет ограниченный доступ.')

            chosen_chapters_url_dict[num_chapter] = chapter_data['url']

    return chosen_chapters_url_dict


@logger.catch(reraise=True)
def get_parsing_url_dict(load_params: dict, chapters_json) -> dict:
    """Возвращает словарь url и доступности для просмотра выбранных глав.

       dict = {номер главы: {
            'url': url,
            'isaccessible': True|False - флаг того, имеется ли доступ к тексту главы
            }
        }

        Номер главы может быть десятичным числом. Пример:"50.2"
        """

    logger.info('Отбор необходимых глав.')
    book_chapters_url_dict = {}
    for ch in chapters_json:
        if ch['chapterShortNumber']:
            book_chapters_url_dict[ch['chapterShortNumber']] = {
                'url': ch['url'],
                'isaccessible': not (ch['isDonate'] or ch['isSubscription'])
            }
        elif ch['title']:
            num_chapter = None
            if 'пролог' in ch['title'].lower():
                num_chapter = 0
            else:
                num_chapter = int(re.search(r'\d+', ch['title']).group())

            book_chapters_url_dict[num_chapter] = {
                'url': ch['url'],
                'isaccessible': not (ch['isDonate'] or ch['isSubscription'])
            }

        elif ch['numberChapter']:
            num_chapter = int(re.search(r'\d+', ch['numberChapter']).group())
            book_chapters_url_dict[num_chapter] = {
                'url': ch['url'],
                'isaccessible': not (ch['isDonate'] or ch['isSubscription'])
            }

        else:
            raise Exception('Номер главы не найден при парсинге!')

    return get_chosen_url_dict(load_params, book_chapters_url_dict)


@logger.catch(reraise=True)
def get_chapter_text(num_chapter: float, part_url: str) -> str:
    """Функция парсит текст главы книги"""

    response = requests.get(url=URLS.get('site')[:-1] + part_url)
    if response.status_code == 200:
        title = get_finding_tag_text(
            response.content, 'h1',
            attrs={'class': 'font-medium text-2xl md:text-3xl pb-3'}
        )
        paragraph_list = [p.text for p in get_finding_tags_text(response.content, 'p',attrs={})]
        text = '\n'.join(paragraph_list)
        if text:
            return f'{title}\n{text}\n\n\n'
    raise Exception(f'Не удалось загрузить страницу c главой {num_chapter}!\n'
                    f'URL:  {response.url}')


def get_chapters_text_dict(load_params: dict, book_json: dict) -> dict:
    """Парсит главы сайта по ссылкам из url_dict.
        Возвращает словарь dict = {номер главы: текст главы}"""

    logger.info('Начало парсинга глав.')
    parsing_url_dict = get_parsing_url_dict(
        load_params, book_json['props']['pageProps']['book']['chapters'])

    chapters_text_dict = {}
    for num_chapter in parsing_url_dict.keys():
        chapters_text_dict[num_chapter] = get_chapter_text(
            num_chapter, parsing_url_dict.get(num_chapter))
        sleep(0.05)
    logger.success('Конец парсинга глав.')
    return chapters_text_dict


@logger.catch(reraise=True)
def get_chapters_file_name(load_params: dict, book_name: str) -> str:
    """Формирует название для файла с главами"""

    num_start = load_params['num_chapter_start']
    num_end = load_params['num_chapter_end']

    if num_end - num_start > 1:
        return f"{book_name}. Главы {num_start}-{num_end}.txt"
    elif num_end - num_start == 0:
        return f"{book_name}. Глава {num_start}.txt"
    else:
        raise Exception("Номер выгружаемой стартовой главы больше конечной!")


def save_chapters_to_file(load_params: dict, book_json: dict, chapters_dict: dict) -> None:
    """Функция сохраняет текст глав в файл"""

    logger.info('Сохранение результата в файл.')
    chapters_file_name = get_chapters_file_name(
        load_params, book_json['props']['pageProps']['book']['title'])

    with open(chapters_file_name, 'w') as result_file:
        for num_chapter in sorted(chapters_dict.keys()):
            result_file.write(chapters_dict[num_chapter])


@logger.catch(reraise=True)
def download_book_chapters(load_params: dict) -> None:
    """Функция скачивает и сохраняет в файл главы книги.
        В качестве аргументов принимает ссылку на книгу, номер начальной и
        конечной главы. Скачивает все главы в этом промежутке, включая
        конечную главу.
    """
    logger.info('Получение данных о книге.')
    response = requests.get(url=load_params['url'])
    if response.status_code == 200:
        logger.info('Парсинг данных о книге.')
        book_json = get_book_json(response.content)

        chapters_text_dict = get_chapters_text_dict(load_params, book_json)
        save_chapters_to_file(load_params, book_json, chapters_text_dict)
    else:
        raise Exception('Не удалось загрузить страницу книги!')


def initiate_logging() -> None:
    """Инициирует логирование"""
    log_folder = 'logs'
    log_file = 'log_last_launch.log'
    if not log_folder in os.listdir():
        os.mkdir(log_folder)

    with open(f'{log_folder}/{log_file}', 'w') as file:
        pass

    logger.add(f'{log_folder}/{log_file}')


@logger.catch(reraise=True)
def get_max_page(url: str) -> int:
    """Возвращает номер последней страницы в пагинации"""

    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        pages_num_list = get_finding_tags_text(
            response.content, 'a',
            attrs={'class': 'h-11 w-11 flex items-center j'
                            'ustify-center lg:cursor-pointer '
                            'cursor-default'}
        )
        max_page = pages_num_list[-1].get_text()

        return int(max_page)
    raise Exception('Не получилось загрузить страницу /books')


def get_all_books_url() -> dict:
    '''Возвращает словарь всех книг на сайте.
        dict = {название книги: url}'''

    max_book_page = get_max_page(URLS['books'])
    books_url = {}

    logger.info('Начало просмотра всех книг.')
    for num_page in range(1, max_book_page + 1):

        response = requests.get(
            URLS['books'], headers=HEADERS, params={'page': num_page})
        if response.status_code == 200:
            books_json = get_book_json(response.content)
            for book in books_json['props']['pageProps']['totalData']['items']:
                books_url[book['title']] = book['url']
    return books_url


def print_and_sort_books(books: dict) -> dict:
    """Выводит в консоль список всех книг"""
    sorted_books = sorted(books.keys())
    sorted_books_dict = {i: name for i, name in enumerate(sorted_books)}
    print('***' * 10)
    print('Список книг:')
    for i in range(len(sorted_books_dict)):
        print(f'{i}: "{sorted_books_dict[i]}"')

    return sorted_books_dict


def get_load_params() -> dict:
    """Возвращает словарь с параметрами парсера,
    которые определяют книгу и главы для парсинга."""

    all_books_url_dict = get_all_books_url()
    book_dict = print_and_sort_books(all_books_url_dict)
    
    num_book = int(input('Введите номер книги: '))
    num_chapters = list(map(int, input('Введите \
        диапазон глав через дефиз: ').split('-')))

    return {'url': URLS['site'][:-1] + all_books_url_dict[book_dict[num_book]],
            'num_chapter_start': num_chapters[0],
            'num_chapter_end': num_chapters[1]}


if __name__ == '__main__':
    initiate_logging()
    load_params = get_load_params()

    logger.info(f"\nПараметры:\n\
        URL: {load_params['url']}\n\
        Chapters:{load_params['num_chapter_start']}-{load_params['num_chapter_end']}")

    download_book_chapters(load_params)
    logger.success('Окончание работы скрипта!')
