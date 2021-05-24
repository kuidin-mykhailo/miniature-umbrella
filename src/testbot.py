import requests
from bs4 import BeautifulSoup
url = "https://likefilmdb.ru/"

data = requests.get(url)
html = data.text
soup = BeautifulSoup(html, 'lxml')


def main(soup):

    result = [(section.text,
               [
                   link['href'] for link in section.find_parents()[1].find_all('a', 'thumb')
               ]
               )
              for section in soup.find_all('div', 'simpleMovie')]


    tmp = soup.find('div', 'uiStandartContentMaximum')
    tmp = tmp.find_all('a', 'thumb')
    #for item in tmp:
       # print(item.find('img').get('alt'))
       # print(item.get('href'))

    soup = BeautifulSoup(requests.get(url + '/service/movies/best/year/2020/').text, 'lxml')
    film_marvel = soup.find_all('div', 'uiSectionV8Wrapper')
    for film in film_marvel:
        film.find('a', 'uiH2')
        print(film.next.text)
        # print(result)

    return result


main(soup)
