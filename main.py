import requests
from bs4 import BeautifulSoup
from json import loads, dumps
from time import sleep
import re
from collections import namedtuple

# 'https://ранобэ.рф'
URLS = {'site': 'https://xn--80ac9aeh6f.xn--p1ai/'}
URL = 'https://xn--80ac9aeh6f.xn--p1ai/silyneyshaya-sistema-ubiystva-drakonov'
# URL = 'https://xn--80ac9aeh6f.xn--p1ai/silyneyshaya-sistema-ubiystva-drakonov/glava-1-silyneyshaya-sistema-ubiystva-drakonov'
PARAMS = []


def get_chapters_file_name(book_json, num_chapter_start, num_chapter_end):
    chapters_file_name = book_json['props']['pageProps']['book'][
                             'title'] + '. ' + str(
        num_chapter_start) + '-' + str(num_chapter_end)
    return chapters_file_name


def get_parsing_url_dict(chapters_json, chapter_start, chapter_end):
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


def get_site_content(url):
    response = requests.get(url=url)
    if response.status_code == 200:
        print('Connection: OK')
        book_page_soup = BeautifulSoup(response.content,
                                       features='html.parser')
        book_data = book_page_soup.find('script',
                                        attrs={'id': '__NEXT_DATA__'})
        book_json = loads(book_data.get_text())

        num_parsing_chapter_start = 1
        num_parsing_chapter_end = 10
        parsing_chapters_url_list = get_parsing_url_dict(
            book_json['props']['pageProps']['book']['chapters'],
            num_parsing_chapter_start, num_parsing_chapter_end)

        parsing_chapter_slice = slice(num_parsing_chapter_start - 1,
                                      num_parsing_chapter_end)
        chapters_file_name = get_chapters_file_name(
            book_json, num_parsing_chapter_start, num_parsing_chapter_end)
        # with open('chapters_content.txt', 'w') as file:
        #     for chapter in book_json['props']['pageProps']['book'][
        #         'chapters'][parsing_chapter_slice]:
        #         chapter_url = URLS.get('site')[0:-1] + chapter.get('url')
        #         chapter_response = requests.get(url=chapter_url)
        #         sleep(0.1)
        #
        #         chapter_page_soup = BeautifulSoup(chapter_response.content,
        #                                           features='html.parser')
        #         chapter_data = chapter_page_soup.find(
        #             'div',
        #             attrs={
        #                 'class': 'overflow-hidden text-base leading-5 sm:text-lg content sm:leading-6 pb-6 prose text-justify max-w-none text-black-0 dark:text-[#aaa]'}
        #         )
        #         file.write(chapter_data.get_text(separator='\n'))
        #         print(chapter_url)
        #         print(chapter_data.get_text(separator='\n'))


def main():
    """Point of enter"""
    get_site_content(URL)


if __name__ == '__main__':
    main()
