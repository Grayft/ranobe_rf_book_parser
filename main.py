import requests
from json import load

# 'https://ранобэ.рф'
# URL = 'https://xn--80ac9aeh6f.xn--p1ai/'
URL = 'https://xn--80ac9aeh6f.xn--p1ai/silyneyshaya-sistema-ubiystva-drakonov'
# URL = 'https://xn--80ac9aeh6f.xn--p1ai/silyneyshaya-sistema-ubiystva-drakonov/glava-1-silyneyshaya-sistema-ubiystva-drakonov'
PARAMS = []


def get_site_content(url):
    request = requests.get(url=url)
    if request.status_code == 200:
        print('Connection: OK')
        print(request.json())
        # with open("site-page.html", 'w', encoding='utf-8') as file:
        #     file.write(request.json)


def main():
    """Point of enter"""
    get_site_content(URL)


if __name__ == '__main__':
    main()
