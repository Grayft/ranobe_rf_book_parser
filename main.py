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


def get_chapters_file_name(book_name, num_chapter_start, num_chapter_end) \
        -> str:
    """Формирует название для файла с главами"""
    if num_chapter_end - num_chapter_start > 1:
        return f'{book_name}. Главы {num_chapter_start}-{num_chapter_end}.txt'
    elif num_chapter_end - num_chapter_start == 0:
        return f'{book_name}. Глава {num_chapter_start}.txt'
    else:
        raise Exception("Номер выгружаемой стартовой главы больше конечной!")


def get_parsing_url_dict(chapters_json, chapter_start, chapter_end) -> dict:
    """Возвращает словарь url на выбранные главы
       dict = {номер главы: url}
    """
    chapters_url_dict = {}
    for ch in chapters_json:
        if ch['chapterShortNumber']:
            chapters_url_dict[ch['chapterShortNumber']] = ch['url']
        elif ch['title']:
            num_chapter = int(re.search(r'\d+', ch['title']).group())
            chapters_url_dict[num_chapter] = ch['url']
        elif ch['numberChapter']:
            num_chapter = int(re.search(r'\d+', ch['numberChapter']).group())
            chapters_url_dict[num_chapter] = ch['url']
        else:
            raise Exception('Номер главы не найден при парсинге!')

    chosen_chapters_num = set([i for i in range(chapter_start,
                                                chapter_end + 1)])
    chosen_chapters_url_dict = {i: url for i, url in chapters_url_dict.items()
                                if i in chosen_chapters_num}
    return chosen_chapters_url_dict


def get_finding_tag_data(content: AnyStr, tag: str, attrs: dict) -> AnyStr:
    """В сдержимом ищет нужный тег с аттрибутами и выводит его содержание"""
    soup = BeautifulSoup(content, features='html.parser')
    data = soup.find(name=tag, attrs=attrs)
    return data.get_text()


def get_site_content(url):
    response = requests.get(url=url)
    if response.status_code == 200:
        print('Connection: OK')
        book_data = get_finding_tag_data(
            response.content, 'script', attrs={'id': '__NEXT_DATA__'})
        book_json = loads(book_data)

        num_parsing_chapter_start = 1
        num_parsing_chapter_end = 10
        parsing_chapters_url_dict = get_parsing_url_dict(
            book_json['props']['pageProps']['book']['chapters'],
            num_parsing_chapter_start,
            num_parsing_chapter_end)

        chapters_file_name = get_chapters_file_name(
            book_json['props']['pageProps']['book']['title'],
            num_parsing_chapter_start,
            num_parsing_chapter_end)
        with open(chapters_file_name+'.txt', 'w') as result_file:

            for num_ch in sorted(list(parsing_chapters_url_dict.keys())):
                ch_url = URLS.get('site')[:-1] + parsing_chapters_url_dict.get(
                    num_ch)
                ch_response = requests.get(url=ch_url)
                sleep(0.1)
                if ch_response.status_code == 200:
                    ch_title = get_finding_tag_data(
                        ch_response.content,
                        'h1',
                        attrs={'class': 'font-medium text-2xl md:text-3xl pb-3'})
                    ch_text = get_finding_tag_data(
                        ch_response.content,
                        'div',
                        attrs={'class': 'overflow-hidden text-base leading-5 sm:text-lg content sm:leading-6 pb-6 prose text-justify max-w-none text-black-0 dark:text-[#aaa]'}
                    )
                    if ch_text:
                        result_file.write(f'{ch_title}\n\n'
                                          f'{ch_text}\n\n')


def main():
    """Point of enter"""
    get_site_content(URL)


if __name__ == '__main__':
    main()
