Описание модуля
===

Данный модуль предназначен для получения статистики по вакансиям с API сайтов [HeadHunter](https://hh.ru) и [Superjob](https://superjob.ru).
Модуль сделан в учебных целях.

Установка, подготовка к работе и запуск
---
Для корректной работы модуля необходимо установить используемые библиотеки из файла `requirements.txt`.
Это можно сделать командой `pip install -r requirements.txt`.

Так же необходимо получить секретный ключ на сайте [Superjob](https://superjob.ru). Затем нужно создать файл
`.env` и поместить туда ключ. Файл должен выглядеть так:

```dotenv
SUPERJOB_TOKEN = ваш_секретный_ключ
```

Запуск модуля осуществляется в терминале:
`C:\forstudy\jobs>python main.py`

Описание работы модуля и его функций.
---
Модуль последовательно создаёт две записи, содержащие статистику вакансий по должности "Программист" с сайта [HeadHunter](https://hh.ru) и [Superjob](https://superjob.ru).
Затем он выводит статистику в терминал в виде таблиц с разбивкой статистики по языкам программирования.

![](https://imgbb.com/Nn4dFfz)

def get_area_id_hh(country_name, area_name, region_name='')
---

Получает с API Headhunter id города, по которому проводится поиск. На вход принимает название страны, города и региона (необязательный параметр).

def make_terminal_table(table_params)
---

Выводит в терминал ascii таблицу. На вход принимает словарь со значениями для таблицы.

def get_vacancies_hh(prog_language)
---

Делает запрос вакансий на API Headhunter. Использует `get area id()`.
На вход принимает название языка программирования, который нужно добавить в параметры поиска, в виде строки.

Отдаёт 4 переменные: общее количество вакансий по запросу, вакансии в виде списка (не более 2000 - ограничение API), название города поиска, название сайта.
```python
return response.json()['found'], hh_vacancies, city, website
```

def get_vacancies_sj(prog_lang)
---
Функция поиска вакансий через API Superjob. Аналогична `get_vacancies_hh`. Вынесена в отдельную функцию из за существенных отличий в работе двух API.

def predict_salary(salary_from, salary_to)
---

Высчитывает среднюю зарплату на основании показателей "Зарплата от" и "Зарплата до". Работает даже в случае, если задан только один из этих показателей.

def predict_rub_salary_hh(vacancy)
---

Высчитывает среднюю зарплату по вакансиям с API Headhunter. Использует функцию `predict_salary`. На вход принимает одну вакансию.
Работает только с зарплатами в рублях.

def predict_rub_salary_sj(vacancy)
---

Высчитывает среднюю зарплату по вакансиям с API Headhunter. Использует функцию `predict_salary`. На вход принимает одну вакансию.
Работает только с зарплатами в рублях.

def vacancies_stats_by_language(language, vacancy_getter, salary_predicter)
---

формирует статистику по языкам программирования вакансий. Помимо статистики (Вакансий найдено, вакансий обработано, средняя зарплата),
возвращает название города по которому производился поиск и название сайта, с API которого проводилась работа. На вход принимает название языка программирования, функцию,
получающую вакансии через API и функцию, рассчитывающую среднюю зарплату.
