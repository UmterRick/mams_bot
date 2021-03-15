import requests
from bs4 import BeautifulSoup
from config import HEADERS
from config import DB_NAME
from database import db_add_course, db_add_category, db_read_topics


def get_html(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params)
    print('Wrong code status') if r.status_code != 200 else None
    return r


def get_topics(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    topics = soup.find_all('div', class_='short')
    counter = 1
    for topic in topics:
        db_add_category(DB_NAME, counter, topic.text)
        counter += 1
    return counter


def get_content(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    items = soup.find_all('div', class_='content')
    topics = db_read_topics(DB_NAME)
    courseID_dict = {}
    for block_id in range(len(topics)):
        names = items[block_id].find_all('p')
        links = items[block_id].find_all('a')
        course_id = 1
        for name in names:
            if str(name.text).startswith('ᐅ'):
                name = str(name.text).replace('ᐅ ', '')
                if '(' in name:
                    body = name[0:name.find('(')]
                    trainer = name[name.find('(') + 1:name.find(')')]
                else:
                    body = name[0:name.find('👉')]
                    trainer = '----'
                full_id = str(block_id + 1) + str(course_id)
                courseID_dict[full_id] = body
                if body == 'Програма підготовки дітей до школи Календарно-тематичний план':
                    db_add_course(DB_NAME, full_id, body, trainer, '_________', str(block_id + 1))
                else:
                    db_add_course(DB_NAME, full_id, body, trainer, links[course_id - 1].get('href'), str(block_id + 1))
                    course_id += 1
    return courseID_dict
