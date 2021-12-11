import pandas as pd
import requests
from bs4 import BeautifulSoup

DOMAIN = 'https://www.marketwatch.com'
BASE_URL = DOMAIN + '/tools/markets/crypto-currencies/1'
COLUMNS = ['crypto_id',
           'crypto_name',
           'last_value',
           'last_closing_value',
           'starting_range_value',
           'ending_range_value',
           '5_Day',
           '1_Month',
           '3_Month',
           '1_Year',
           'YTD']


def transform_text_to_float(tag):
    return float(tag.replace(',', ''))


def format_key_name(name):
    return name.replace(' ', '_')


def scrap_crypto(crypto_url, data):
    print(f'Scraping {crypto_url}')

    crypto_page = requests.get(crypto_url)
    crypto_content = BeautifulSoup(crypto_page.text, 'lxml')

    row = {}
    trade_info = crypto_content.find('div', {'class': 'region--intraday'})

    row['crypto_id'] = crypto_content.find('span', {'class': 'company__ticker'}).string

    row['crypto_name'] = crypto_content.find('h1', {'class': 'company__name'}).string

    row['last_value'] = transform_text_to_float(trade_info.find('bg-quote', {'class': 'value'}).string)

    row['last_closing_value'] = transform_text_to_float(
        trade_info.find('div', {'class': 'intraday__close'}).td.string[1:])

    week_range = trade_info.find('div', {'class': 'range__header'})

    starting_range_value, ending_range_value = [value.string for value in week_range.find_all('span', class_='primary')]

    row['starting_range_value'] = transform_text_to_float(starting_range_value)
    row['ending_range_value'] = transform_text_to_float(ending_range_value)

    performance_info = crypto_content.find('div', {'class': 'performance'})

    infos = performance_info.find_all('tr')

    for info in infos:
        key_name = format_key_name(info.find('td', class_='table__cell').string)
        performance_value = info.find('li', class_='value').string.replace('%', '')
        row[key_name] = performance_value

    return data.append(row, ignore_index=True)


if __name__ == '__main__':
    page = requests.get(BASE_URL)
    soup = BeautifulSoup(page.text, 'lxml')

    crypto_data = pd.DataFrame(columns=COLUMNS)

    has_pages = True
    while has_pages:
        crypto_links = soup.find('table', class_='table-condensed').find_all('a')

        for link in crypto_links:
            crypto_data = scrap_crypto(DOMAIN + link.attrs['href'], crypto_data)

        pagination = soup.find('ul', class_='pagination')
        has_pages = pagination.find('li', class_='disabled') is None or \
                    pagination.find('li', class_='disabled').string != '»'

        if has_pages:
            next_page = requests.get(DOMAIN + pagination.find_all('li')[-1].find('a').attrs['href'])
            soup = BeautifulSoup(next_page.text, 'lxml')

    crypto_data.to_csv('report/report.csv', index=False)
