import requests
from bs4 import BeautifulSoup
from json import loads

# 'https://ранобэ.рф'
# URL = 'https://xn--80ac9aeh6f.xn--p1ai/'
URL = 'https://xn--80ac9aeh6f.xn--p1ai/silyneyshaya-sistema-ubiystva-drakonov'
# URL = 'https://xn--80ac9aeh6f.xn--p1ai/silyneyshaya-sistema-ubiystva-drakonov/glava-1-silyneyshaya-sistema-ubiystva-drakonov'
PARAMS = []


def get_site_content(url):
    response = requests.get(url=url)
    if response.status_code == 200:
        print('Connection: OK')
        # with open("site-page.html", 'w', encoding='utf-8') as file:
        #     file.write(response.text)
        soup = BeautifulSoup(response.text, features='html.parser')
        # with open('parsing.txt', 'w') as p_file:
        data = soup.find('script', attrs={'id': '__NEXT_DATA__'})
        s = str(data)
        s = s.replace('\u200b', '')
        s = s.replace('\\u003c', '<')
        s = s.replace('\\u003e', '>')
        s = s[51:-9]
        j = loads(s)
        b = j['props']
        with open('chapters.txt', 'w') as chapter_file:

            for i in j['props']['pageProps']['book']['chapters'][:5]:
                chapter_file.write(str(i))
                chapter_file.write('\n')
            # print(str(i))
            # p_file.write(s)
            # for i, d in enumerate(data):

            # print(l)
        # print(soup.find_all('script', attrs={'id': '__NEXT_DATA__'}))


def main():
    """Point of enter"""
    get_site_content(URL)


if __name__ == '__main__':
    main()
