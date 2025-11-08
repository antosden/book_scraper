import time
import re
import json
import logging
from concurrent.futures import ThreadPoolExecutor, wait
from queue import Queue, Empty
import requests
import schedule
from bs4 import BeautifulSoup

# Ссылка на каталог, где %d - номер страницы
catalog_url = 'https://books.toscrape.com/catalogue/page-%d.html'
# Ссылка на страницу с книгой, где %s - relative URL книги
book_url = 'https://books.toscrape.com/catalogue/%s'

SCHEDULE_TIME = "0:10"


def get_book_data(book_url: str) -> dict:
    """
    Посылает GET запрос по URL адресу страницы с книгой.
    Возвращает информацию о странице с типом объекта BeautifulSoup

    Args:
        book_url (str): URL адрес страницы с книгой
    Returns:
        book (dict): Информация о книге: название, цена, рейтинг,
        количество в наличии, описание и дополнительные характеристики
    """

    # НАЧАЛО ВАШЕГО РЕШЕНИЯ
    book = {
        'title': '',
        'price': 0,
        'rating': 0,
        'amount': 0,
        'description': '',
        'additional_info': {}
    }
    logging.debug(f"Fetching book page: {book_url}")
    soup = BeautifulSoup(requests.get(book_url, timeout=10).content, 'html.parser')

    # Название
    if soup.find('h1'):
        book['title'] = soup.find('h1').text
        logging.debug(f"Parsed title: {book['title']}")
    else:
        logging.debug("Title not found on page.")

    # Цена
    if soup.find('p', class_='price_color'):
        book['price'] = soup.find('p', class_='price_color').text
        logging.debug(f"Parsed price: {book['price']}")
    else:
        logging.debug("Price not found on page.")

    # Количество
    if soup.find('p', class_='instock availability'):
        # Извлекаем количество в числовом формате из строки "In stock ({amount} available)"
        amount = re.findall(r'\d+', soup.find('p', class_='instock availability').text)[0]
        book['amount'] = int(amount) if amount else 0
        logging.debug(f"Parsed amount available: {book['amount']}")
    else:
        logging.debug("Amount not found on page.")

    # Рейтинг
    # Значение рейтинга хранится в классе после класса 'star-rating'
    rating = soup.find("p", attrs={'class': 'star-rating'}).get("class")[1]
    if rating:
        # Получаем числовое значение рейтинга
        book['rating'] = {
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5
        }.get(rating)
        logging.debug(f"Parsed rating: {book['rating']}")
    else:
        logging.debug("Rating not found on page.")

    # Описание
    description = soup.find('meta', {'name': 'description'})
    if description:
        book['description'] = description['content']
        logging.debug(f"Parsed description: {book['description']}")
    else:
        logging.debug("Description not found on page.")

    # Дополнительные характеристики
    additional_info = soup.find('table', class_='table table-striped')
    info_table = additional_info.find_all('tr')
    if info_table:
        logging.debug("Parsing additional info...")
        for row in info_table:
            book['additional_info'][row.th.text] = row.td.text
            logging.debug(f"{row.th.text}: {row.td.text}")
        logging.debug("Finished parsing additional info...")
    else:
        logging.debug("Additional info not found on page.")
    return book
    # КОНЕЦ ВАШЕГО РЕШЕНИЯ


def books_url_producer(queue: Queue, pages_count: int):
    """
        Producer: собирает с каждой страницы каталога URL книг
        и добавляет в очередь для Consumer для последующего парсинга

        queue (Queue): Очередь, которая заполняется URL адресами книг
        pages_count (int): Количество страниц в каталоге
    """
    logging.debug('URL producer started...')
    # Получаем информацию о книгах с каждой страницы каталога
    for i in range(1, pages_count + 1):
        logging.debug(f'Catalog: Page №{i}')
        soup = BeautifulSoup(requests.get(catalog_url % i, timeout=10).content, 'html.parser')
        books = soup.find_all('article', class_='product_pod')
        # Формируем ссылки по каждой книге и добавляем в очередь
        for book in books:
            logging.debug(f'Got book ref source: {book.a['href']}')
            queue.put(book_url % book.a['href'])


def book_data_consumer(queue: Queue, result_list: list):
    """
    Consumer: берет URL из очереди и возвращает информацию о книге
    через get_book_data

    Args:
        queue (Queue): Очередь URL адресов книг
        result_list (list): Список для записи результата парсинга книг
    """
    logging.debug('Book consumer started...')
    try:
        while True:
            # Парсим книги по ссылкам из очереди пока она не пуста (ожидаем до 5 секунд)
            url = queue.get(timeout=5)
            if url is None:
                break
            book_data = get_book_data(url)
            result_list.append(book_data)
            logging.debug(f'Consumer processed: {url}')

    except Empty:
        logging.debug('Consumer: queue empty, finishing...')
    except Exception as e:
        logging.error(f"Consumer error: {e}")


def scrape_books(is_save=False) -> list:
    """
    Посылает GET запрос по URL адресу страницы с каталогом.
    Получает информацию о количестве страниц в каталоге.
    Запускает books_url_producer для сохранения ссылок на книги в очередь
    и book_data_consumer для парсинга книг через очередь из ссылок

    Сохраняет результат парсинга в файл books_data.txt

    Args:
        is_save (bool): Флаг сохранения результата в файл books_data.txt
    Returns:
        result (list): Список информации о книгах на сайте:
        название, цена, рейтинг, количество в наличии, описание и
        дополнительные характеристики
    """
    result = []
    # НАЧАЛО ВАШЕГО РЕШЕНИЯ
    logging.info('Scraping books from books.toscrape.com ...')

    # Получаем информацию о количестве страниц в каталоге через пейджер
    soup = BeautifulSoup(requests.get(catalog_url % 1).content, 'html.parser')
    pages_count = int(re.findall(r'Page 1 of\s+(\d+)', soup.find('ul', class_='pager').li.text)[0])
    books_url_queue = Queue()

    with ThreadPoolExecutor(max_workers=11) as executor:
        producer_future = executor.submit(books_url_producer, books_url_queue, pages_count)
        consumer_futures = [
            executor.submit(book_data_consumer, books_url_queue, result)
            for _ in range(10)
        ]
        producer_future.result()
        logging.info('Producer finished')
        for _ in range(10):
            books_url_queue.put(None)
        wait(consumer_futures)

    logging.info('Scraping finished')
    if is_save:
        # Сохраняем результат в books_data.txt
        with open('books_data.txt', 'w', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=4)
            logging.info('Data successfully saved to books_data.txt')
    return result
    # КОНЕЦ ВАШЕГО РЕШЕНИЯ


def scraper():
    # Расписание
    SCHEDULE_TIME = '19:00'

    # Сброс предыдущих задач
    schedule.clear()

    # Для удобства отладки и демонастрации результата добавлено логгирование
    # Сброс старых хендлеров логгирования
    for h in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(h)

    # Настройка логгирования
    logging.basicConfig(
        level=logging.DEBUG,
        filename='../scrape_books.log',
        filemode='a',
        encoding='utf-8',
        format='%(asctime)s [%(levelname)s] %(message)s',
        force=True)

    # Вывод логгирования в консоль
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logging.getLogger().addHandler(console)

    # Расписание запуска джобы вынесено в SCHEDULE_TIME
    job = schedule.every().day.at(SCHEDULE_TIME).do(scrape_books, is_save=True)
    logging.info(f"Scheduler initialized. Job will run daily at {SCHEDULE_TIME}.")

    try:
        logging.info(f"Next run scheduled for {job.next_run.strftime('%Y-%m-%d %H:%M')}")
    except Exception:
        logging.debug("Job registered")

    while True:
        schedule.run_pending()
        time.sleep(60)
    # КОНЕЦ ВАШЕГО РЕШЕНИЯ


if __name__ == '__main__':
    scraper()
