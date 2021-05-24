import asyncio
import logging
import time
import aiohttp
import requests
import random
from aiogram.types import InlineQueryResultArticle, InlineQuery, InputTextMessageContent, inline_keyboard
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, executor, types, exceptions
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

import src.keyboard as kb
import src.config as cfg

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('broadcast')

# Initialize bot and dispatcher
loop = asyncio.get_event_loop()
bot = Bot(token=cfg.TOKEN)
dp = Dispatcher(bot)
url = "https://likefilmdb.ru/"


async def get_html(url):
    timeout = aiohttp.ClientTimeout(total=30)
    ua = 'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers={'User-Agent': ua},
                                     timeout=timeout) as session:
        async with session.request('get', url) as responce:
            return await responce.content.read()


def get_html_selenium(url):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usag")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36")
    driver = Chrome(options=chrome_options)
    driver.get(url)
    html = driver.page_source
    select_play_button = driver.find_element_by_xpath('/html/body/div[4]/div[1]/div/div[1]/div[4]/a')
    select_play_button.send_keys('\n')
    time.sleep(4)
    select_youtube_button = driver.find_element_by_xpath('/html/body/div/div/div[31]/div[2]/div[2]/a')
    select_youtube_button.send_keys('\n')
    time.sleep(20)
    driver.close()
    driver.quit()

    return html


@dp.message_handler(commands=['start'])
async def welcome(message):
    await bot.send_message(message.chat.id,
                           f'Хеллоу, {message.from_user.first_name}!\n Я - бот для любителей кино',
                           parse_mode='html', reply_markup=kb.main_menu_ru)


@dp.message_handler(lambda message: message.text == 'Фильмы')
async def films(message):
    await bot.send_message(message.chat.id, 'Ура, вы нашли раздел с <b>Фильмами</b>', parse_mode='html',
                           reply_markup=kb.film_menu)


@dp.message_handler(lambda message: message.text == 'Сериалы')
async def films(message):
    await bot.send_message(message.chat.id, 'Ура, вы нашли раздел с <b>Сериалами</b>', parse_mode='html',
                           reply_markup=kb.series_menu)


@dp.inline_handler(lambda inline_query: inline_query.query.startswith('best_fil'))
async def bests_films_year(inline_query: InlineQuery):
    result = await get_inline_films_href('/service/movies/best/year/2020/')
    await bot.answer_inline_query(inline_query.id, results=result, cache_time=10)


@dp.inline_handler(lambda inline_query: inline_query.query.startswith('by-category_'))
async def bests_films_year(inline_query: InlineQuery):
    href = inline_query.query.split('_')[1]
    result = await get_inline_films_href(href)
    await bot.answer_inline_query(inline_query.id, results=result, cache_time=600)


@dp.inline_handler(lambda inline_query: inline_query.query.startswith('ser-category_'))
async def bests_films_year(inline_query: InlineQuery):
    href = inline_query.query.split('_')[1]
    result = await get_inline_series_href(href)
    await bot.answer_inline_query(inline_query.id, results=result, cache_time=600)


@dp.inline_handler(lambda inline_query: inline_query.query.startswith('best_serie'))
async def bests_films_year(inline_query: InlineQuery):
    result = await get_inline_series_href('/service/tv-series/best/year/2020/')
    await bot.answer_inline_query(inline_query.id, results=result, cache_time=600)


@dp.inline_handler(lambda inline_query: inline_query.query.startswith('similar_'))
async def add_order_to_db(inline_query: InlineQuery):
    href = inline_query.query.split('_')[1]
    result = await get_inline_films_href(href + 'similar/')
    await bot.answer_inline_query(inline_query.id, results=result, cache_time=600)


@dp.inline_handler(lambda inline_query: inline_query.query.startswith('similar-series_'))
async def add_order_to_db(inline_query: InlineQuery):
    href = inline_query.query.split('_')[1]
    result = await get_inline_series_href(href + 'pohozhie-serialy/')
    await bot.answer_inline_query(inline_query.id, results=result, cache_time=600)


@dp.callback_query_handler(lambda call: call.data.startswith('trailer_'))
async def get_trailer(call):
    href = call.data.split('_')[1]
    soup = BeautifulSoup(requests.get(url + href).text, 'lxml')
    tmp = soup.find('div', {'class': 'uiSectionV2Media'})
    play_button = tmp.find('a', {'href': '#'})
    trailer_link = str(play_button).split(',')[2].split('\'')[1][2:]
    await bot.send_message(call.from_user.id, trailer_link)


@dp.message_handler(lambda message: message.text == 'Я киноман?')
async def random_value(message):
    number = random.randint(1, 2)
    if number == 1:
        await bot.send_message(message.chat.id,
                               f'Я, как знаток в фильмах, а эьто знают <b>ВСЕ</b>, '
                               f'с уверенностью заявляю что киноман из тебя никакой\n\n В процентах: {number}',
                               parse_mode='html')
    if number == 2:
        await bot.send_message(message.chat.id,
                               'Я, как знаток в фильмах, а эьто знают <b>ВСЕ</b>, '
                               f'с уверенностью заявляю что киноман из тебя никакой ({number})',
                               parse_mode='html')


async def get_inline_films_href(href):
    soup = BeautifulSoup(requests.get(url + href).text, 'lxml')
    best_films = soup.find_all('div', 'uiSectionV8Content')
    result = []
    counter = 0
    for film in best_films:
        if counter == 12:
            break
        film = film.find('a', 'uiH2')
        film_href = film.get('href')
        try:
            item_desctiption, film_image = get_film_content(film_href, counter)
        except Exception as e:
            print(e)
            continue
        message = InputTextMessageContent(item_desctiption, parse_mode='html')
        film_insert = film.next
        keyboard = kb.generate_film_keyboard(film_href)
        result.append(
            InlineQueryResultArticle(
                id=str(counter),
                title=film_insert,
                thumb_url=film_image,
                thumb_height=500, thumb_width=500,
                input_message_content=message,
                reply_markup=keyboard
            )
        )
        counter += 1
    return result


async def get_inline_series_href(href):
    soup = BeautifulSoup(requests.get(url + href).text, 'lxml')
    best_films = soup.find_all('div', 'uiSectionV8Content')
    result = []
    counter = 0
    for film in best_films:
        if counter == 12:
            break
        film = film.find('a', 'uiH2')
        film_href = film.get('href')
        try:
            item_desctiption, film_image = get_film_content(film_href, counter)
        except Exception as e:
            print(e)
            continue
        message = InputTextMessageContent(item_desctiption, parse_mode='html')
        film_insert = film.next
        keyboard = kb.generate_series_keyboard(film_href)
        result.append(
            InlineQueryResultArticle(
                id=str(counter),
                title=film_insert,
                thumb_url=film_image,
                thumb_height=500, thumb_width=500,
                input_message_content=message,
                reply_markup=keyboard
            )
        )
        counter += 1
    return result


@dp.callback_query_handler(lambda call: call.data.startswith('categories_'))
async def get_films_categories(call):
    tel_id = call.from_user.id
    current_pos = int(call.data.split('_')[1])
    href = 'service/movies/what-to-see/'
    soup = BeautifulSoup(requests.get(url + href).text, 'lxml')
    film_categories = soup.find_all('div', {'class': 'simpleMovie'})
    k = inline_keyboard.InlineKeyboardMarkup()
    counter = current_pos
    while counter <= len(film_categories):
        if counter == current_pos + 8 or counter == len(film_categories):
            break
        category_href = film_categories[counter].find('a').get('href')
        category_name = film_categories[counter].find('img').get('alt')
        k.add(inline_keyboard.InlineKeyboardButton(str(counter + 1) + ') ' + category_name,
                                                   switch_inline_query_current_chat='by-category_{0}'.format(
                                                       category_href)))
        counter += 1
    if current_pos >= 8:
        call_data_previous = 'categories_{0}'.format(current_pos - 8)
        k.add(inline_keyboard.InlineKeyboardButton('Previous⬅️', callback_data=call_data_previous))
    if len(film_categories) > current_pos + 8:
        call_data_more = 'categories_{0}'.format(current_pos + 8)
        k.add(inline_keyboard.InlineKeyboardButton('Next \U000027a1', callback_data=call_data_more))
    await bot.edit_message_text('Выберите категорию фильмов', tel_id, call.message.message_id, reply_markup=k)


@dp.callback_query_handler(lambda call: call.data.startswith('categories-series'))
async def get_films_categories(call):
    tel_id = call.from_user.id
    current_pos = int(call.data.split('_')[1])
    href = 'service/tv-series/what-to-see/'
    soup = BeautifulSoup(requests.get(url + href).text, 'lxml')
    film_categories = soup.find_all('div', {'class': 'simpleMovie'})
    k = inline_keyboard.InlineKeyboardMarkup()
    counter = current_pos
    while counter <= len(film_categories):
        if counter == current_pos + 8 or counter == len(film_categories):
            break
        category_href = film_categories[counter].find('a').get('href')
        category_name = film_categories[counter].find('img').get('alt')
        k.add(inline_keyboard.InlineKeyboardButton(str(counter + 1) + ') ' + category_name,
                                                   switch_inline_query_current_chat='ser-category_{0}'.format(
                                                       category_href)))
        counter += 1
    if current_pos >= 8:
        call_data_previous = 'categories-series_{0}'.format(current_pos - 8)
        k.add(inline_keyboard.InlineKeyboardButton('Previous⬅️', callback_data=call_data_previous))
    if len(film_categories) > current_pos + 8:
        call_data_more = 'categories-series_{0}'.format(current_pos + 8)
        k.add(inline_keyboard.InlineKeyboardButton('Next \U000027a1', callback_data=call_data_more))
    await bot.edit_message_text('Выберите категорию сериалов', tel_id, call.message.message_id, reply_markup=k)


def get_film_content(href, offset):
    link = url + href
    soup = BeautifulSoup(requests.get(link).text, 'lxml')
    film_title = soup.find('a', {'class': 'uiH2'}).text
    text = f'<b>{film_title}</b>\n\n'
    try:
        film_content = soup.find_all('div', 'uiSectionV8Content')[offset].find('p').text
        print(film_content)
    except Exception as e:
        print(e)
    text += 'Cюжет\n'
    text += film_content
    text += '\n\n'
    film_image = url + soup.find_all('div', 'uiSectionV8Media')[offset].find('div',
                                                                             {'class': 'uiMediaOnClickElement'}).find(
        'img', {'class': 'uiLazyLoadElement'}).get('data-src')
    print(film_image)
    film_table = soup.find('table', {'class': 'uiStandartVarListWidth30S70'}).find_all('tr')
    table_rows = ''
    for row in film_table:
        table_rows += row.find_all('td')[0].text + ' '
        table_rows += row.find_all('td')[1].text + '\n'
    text += table_rows
    text += f'''<a href="{film_image}">Photo</a>'''
    return text, film_image


if __name__ == '__main__':
    executor.start_polling(dp)
