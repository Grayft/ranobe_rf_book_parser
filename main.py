import requests
from bs4 import BeautifulSoup
from json import loads, dumps
from time import sleep
import re
from typing import AnyStr
from collections import namedtuple

# 'https://ранобэ.рф'
URLS = {'site': 'https://xn--80ac9aeh6f.xn--p1ai/'}
URL = 'https://xn--80ac9aeh6f.xn--p1ai/silyneyshaya-sistema-ubiystva-drakonov'
# URL = 'https://xn--80ac9aeh6f.xn--p1ai/silyneyshaya-sistema-ubiystva-drakonov/glava-1-silyneyshaya-sistema-ubiystva-drakonov'
PARAMS = []


def get_chapters_file_name(book_name, load_params) -> str:
    """Формирует название для файла с главами"""
    num_start = load_params['num_chapter_start']
    num_end = load_params['num_chapter_end']

    if num_end - num_start > 1:
        return f"{book_name}. Главы {num_start}-{num_end}.txt"
    elif num_end - num_start == 0:
        return f"{book_name}. Глава {num_start}.txt"
    else:
        raise Exception("Номер выгружаемой стартовой главы больше конечной!")


def get_chosen_url_dict(load_params: dict, chapters: dict):
    """Возвращает словарь с url нужных глав из всех глав книги"""

    num_chosen_chapters = set(
        [num_chapter for num_chapter in range(load_params['num_chapter_start'],
                                              load_params[
                                                  'num_chapter_end'] + 1)])
    chosen_chapters_url_dict = {i: url for i, url in chapters.items()
                                if i in num_chosen_chapters}
    return chosen_chapters_url_dict


def get_parsing_url_dict(load_params: dict, chapters_json) -> dict:
    """Возвращает словарь url, выбранных глав
       dict = {номер главы: url}"""

    book_chapters_url_dict = {}
    for ch in chapters_json:
        if ch['chapterShortNumber']:
            book_chapters_url_dict[ch['chapterShortNumber']] = ch['url']
        elif ch['title']:
            num_chapter = int(re.search(r'\d+', ch['title']).group())
            book_chapters_url_dict[num_chapter] = ch['url']
        elif ch['numberChapter']:
            num_chapter = int(re.search(r'\d+', ch['numberChapter']).group())
            book_chapters_url_dict[num_chapter] = ch['url']
        else:
            raise Exception('Номер главы не найден при парсинге!')

    return get_chosen_url_dict(load_params, book_chapters_url_dict)


def get_finding_tag_data(content: AnyStr, tag: str, attrs: dict) -> AnyStr:
    """В сдержимом ищет нужный тег с аттрибутами и выводит его содержание"""
    soup = BeautifulSoup(content, features='html.parser')
    data = soup.find(name=tag, attrs=attrs)
    return data.get_text()


def get_book_json(content):
    book_data = get_finding_tag_data(content, 'script',
                                     attrs={'id': '__NEXT_DATA__'})
    return loads(book_data)


def get_chapter_text(part_url: str) -> str:
    """Функция парсит текст главы книги"""

    response = requests.get(url=URLS.get('site')[:-1] + part_url)
    if response.status_code == 200:
        title = get_finding_tag_data(response.content, 'h1',
                                     attrs={
                                         'class': 'font-medium text-2xl md:text-3xl pb-3'})
        text = get_finding_tag_data(response.content, 'div',
                                    attrs={
                                        'class': 'overflow-hidden text-base leading-5 sm:text-lg content sm:leading-6 pb-6 prose text-justify max-w-none text-black-0 dark:text-[#aaa]'}
                                    )
        if text:
            return f'{title}\n{text}\n\n'


def get_chapters_text_dict(load_params, book_json):
    """Парсит главы сайта по ссылкам из url_dict.
        Возвращает словарь dict = {номер главы: текст главы}"""

    parsing_url_dict = get_parsing_url_dict(
        load_params, book_json['props']['pageProps']['book']['chapters'])

    chapters_text_dict = {}
    for num_chapter in parsing_url_dict.keys():
        chapters_text_dict[num_chapter] = get_chapter_text(
            parsing_url_dict.get(num_chapter))
        sleep(0.05)
    return chapters_text_dict


def save_chapters_to_file(load_params, book_json, chapters_dict):
    """Функция сохраняет текст глав в файл"""
    chapters_file_name = get_chapters_file_name(
        book_json['props']['pageProps']['book']['title'], load_params)

    with open(chapters_file_name, 'w') as result_file:
        for num_chapter in sorted(chapters_dict.keys()):
            result_file.write(chapters_dict[num_chapter])


def download_book_chapters(load_params: dict):
    """Функция скачивает и сохраняет в файл главы книги.
        В качестве аргументов принимает ссылку на книгу, номер начальной и
        конечной главы. Скачивает все главы в этом промежутке, включая
        конечную главу.
    """
    response = requests.get(url=load_params['url'])
    if response.status_code == 200:
        print('Connection: OK')
        book_json = get_book_json(response.content)
        chapters_text_dict = get_chapters_text_dict(load_params, book_json)
        save_chapters_to_file(load_params, book_json, chapters_text_dict)


def main():
    """Point of enter"""
    load_params = {'url': URL,
                   'num_chapter_start': 1,
                   'num_chapter_end': 5}
    download_book_chapters(load_params)
    print('Program: Ok')


if __name__ == '__main__':
    main()
