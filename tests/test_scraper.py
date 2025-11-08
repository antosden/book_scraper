import pytest
from scraper import get_book_data, scrape_books

"""
TODO:
Создайте минимум три автотеста для ключевых функций парсинга — например, `get_book_data` и `scrape_books`. Идеи проверок (можете использовать свои):

* данные о книге возвращаются в виде словаря с нужными ключами;
* список ссылок или количество собранных книг соответствует ожиданиям;
* значения отдельных полей (например, `title`) корректны.

Оформите тесты в отдельном скрипте `tests/test_scraper.py`, используйте библиотеку `pytest`. Убедитесь, что тесты проходят успешно при запуске из терминала командой `pytest`.

Также выведите результат их выполнения в ячейке ниже.
"""

test_books = [
    {
        'url': 'https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html',
        'title': 'Tipping the Velvet',
        'amount': 20,
        'price': '£53.74',
        'rating': 1
    },
    {
        'url': 'https://books.toscrape.com/catalogue/rhythm-chord-malykhin_47/index.html',
        'title': 'Rhythm, Chord & Malykhin',
        'description': '\n    Twenty-six-year-old Gaby Barreto might be a lot of things (loyal, sarcastic, one of the '
                       'guys and a pain in the butt depending on which family member you ask), but dumb isn’t one of '
                       'them. When her twin brother invites her to go on tour as his band’s merch girl, '
                       'she isn’t exactly screaming at the top of her lungs with joy. With no job opportunities '
                       'pounding on her door, an e Twenty-six-year-old Gaby Barreto might be a lot of things (loyal, '
                       'sarcastic, one of the guys and a pain in the butt depending on which family member you ask), '
                       'but dumb isn’t one of them. When her twin brother invites her to go on tour as his band’s '
                       'merch girl, she isn’t exactly screaming at the top of her lungs with joy. With no job '
                       'opportunities pounding on her door, an ex-boyfriend she would still like to castrate, '
                       'and no end in sight to moving out of her parents’ house in Dallas… it would be dumb to say no '
                       'to the chance of a lifetime. Two bands, three continents, one tour. Spending the next '
                       'ninety-plus days with three beloved idiots and eight complete strangers shouldn’t be a big '
                       'deal, right? If only the singer of the headlining band didn’t have tattoos... a great '
                       'personality… a fantastic body… and if he wasn’t so funny…. Let’s be real: Gaby never had a '
                       'chance against Sacha Malykhin. ...more\n',

        'rating': 2
    },
    {
        'url': 'https://books.toscrape.com/catalogue/memoirs-of-a-geisha_477/index.html',
        'rating': 3
    },
    {
        'url': 'https://books.toscrape.com/catalogue/the-most-perfect-thing-inside-and-outside-a-birds-egg_938/'
               'index.html',
        'rating': 4
    },
    {
        'url': 'https://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html',
        'title': 'Sapiens: A Brief History of Humankind',
        'rating': 5
    }
]

test_result = scrape_books()


def test_book_fields():
    data = get_book_data("https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")
    assert isinstance(data, dict)
    assert {"title", "price", "rating", "amount", "description", "additional_info"} <= set(data.keys())


def test_book_rating():
    for book in test_books:
        book_data = get_book_data(book['url'])
        assert book_data['rating'] == book['rating']


def test_book_additional_info():
    for book in test_books:
        book_data = get_book_data(book['url'])
        assert list(book_data['additional_info'].keys()) == ['UPC', 'Product Type', 'Price (excl. tax)',
                                                             'Price (incl. tax)', 'Tax', 'Availability',
                                                             'Number of reviews']


def test_books_count():
    assert len(test_result) == 1000


def test_book_data():
    for test_book in test_books:
        book = get_book_data(test_book['url'])
        for key in test_book.keys():
            if key == 'url':
                continue
            test_book[key] = book[key]
