import requests


from dotenv import load_dotenv
from os import environ
from terminaltables import AsciiTable


def get_area_id_from_hh(country_name, area_name, region_name=''):

    area_url = 'https://api.hh.ru/areas'

    response = requests.get(area_url)
    response.raise_for_status()

    countries = response.json()

    regions = list(*[
        country['areas']
        for country in countries
        if country['name'] == country_name
        ])

    if not region_name:
        area_id = str(*[
            region['id']
            for region in regions
            if region['name'] == area_name
            ])

    return area_id


def get_city_name_from_sj(town_id):

    city_url = 'https://api.superjob.ru/2.0/towns/'

    city_response = requests.get(city_url)
    city_response.raise_for_status()

    cities_info = city_response.json()['objects']

    city = ''

    for town in cities_info:
        if town['id'] == town_id:
            city = town['title']

    return city


def print_terminal_table(table_params):

    title = f"{table_params['website']} {table_params['city']}"
    table_data = [
        [
            'Язык программирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата'
            ]
        ]

    for param in table_params.keys():
        if isinstance(table_params[param], dict):
            table_row = [param]
            [
                table_row.append(lang_info)
                for lang_info in table_params[param].values()
                ]
            table_data.append(table_row)

    table = AsciiTable(table_data, title)
    print(table.table)


def get_vacancies_from_hh(prog_language):

    vacancies_url = 'https://api.hh.ru/vacancies'
    country = 'Россия'
    city = 'Москва'
    website = 'HeadHunter'
    search_area_id = get_area_id_from_hh(country, city)

    params = {
        'per_page': 100,
        'text': f'Программист {prog_language}',
        'area': search_area_id,
    }

    response = requests.get(vacancies_url, params=params)
    response.raise_for_status()

    hh_vacancies = []

    for page in range(response.json()['pages']):

        params['page'] = page

        page_response = requests.get(vacancies_url, params=params)
        page_response.raise_for_status()

        new_vacancies = page_response.json()['items']

        for vacancy in new_vacancies:
            hh_vacancies.append(vacancy)

    return response.json()['found'], hh_vacancies, city, website


def get_vacancies_from_sj(prog_lang, secret_key=''):

    auth_url = 'https://api.superjob.ru/2.0/vacancies/'

    auth_header = {
        'X-Api-App-Id': secret_key
    }

    search_params = {
        'count': 100,
        'town': 4,
        'catalogues': 48,
        'keyword': f'Программист {prog_lang}',
    }

    city = get_city_name_from_sj(search_params['town'])

    website = 'SuperJob'

    response = requests.get(
        auth_url,
        headers=auth_header,
        params=search_params
        )
    response.raise_for_status()

    sj_vacancies = []

    for page in range(5):
        search_params['page'] = page

        page_response = requests.get(
            auth_url,
            headers=auth_header,
            params=search_params
            )
        page_response.raise_for_status()

        new_vacancies = page_response.json()['objects']

        for vacancy in new_vacancies:
            sj_vacancies.append(vacancy)

    return response.json()['total'], sj_vacancies, city, website


def predict_salary(salary_from, salary_to):

    if salary_from and salary_to:
        return sum([salary_from, salary_to])/2
    elif not salary_to and salary_from:
        return salary_from*1.2
    elif not salary_from and salary_to:
        return salary_to*0.8


def predict_rub_salary_for_hh(vacancy):
    if vacancy['salary'] and vacancy['salary']['currency'] == 'RUR':
        salary_from = vacancy['salary']['from']
        salary_to = vacancy['salary']['to']
        medium_salary = predict_salary(salary_from, salary_to)

        return medium_salary


def predict_rub_salary_for_sj(vacancy):
    if vacancy['currency'] == 'rub':
        salary_from = vacancy['payment_from']
        salary_to = vacancy['payment_to']
        medium_salary = predict_salary(salary_from, salary_to)

        if medium_salary:
            return medium_salary


def make_vacancies_stats_by_lang(language, vacancy_getter, salary_predicter, key_for_getter=''):

    lang_stats={}

    if vacancy_getter == get_vacancies_from_sj:
        jobs_found, language_jobs, city, website = vacancy_getter(language, key_for_getter)

    else:
        jobs_found, language_jobs, city, website = vacancy_getter(language)

    all_salaries = [
        salary_predicter(job)
        for job in language_jobs
        if salary_predicter(job)
    ]

    if all_salaries:
        lang_stats = {
            'vacancies found': jobs_found,
            'vacancies processed': len(all_salaries),
            'average salary': int(sum(all_salaries)/len(all_salaries)),
        }

    return [lang_stats, city, website]


def make_dict_of_jobs(dict_tempate, job_getter, salary_predicter, secret_key=''):
    langs = dict_tempate.copy()

    if job_getter == get_vacancies_from_sj:
        for lang in langs.keys():
            stats = make_vacancies_stats_by_lang(
                lang,
                job_getter,
                salary_predicter,
                key_for_getter = secret_key
                )

            if lang == 'city':
                langs[lang] = stats[1]
            elif lang == 'website':
                langs[lang] = stats[2]
            else:
                langs[lang] = stats[0]
    else:
        for lang in langs.keys():
            stats = make_vacancies_stats_by_lang(
                lang,
                job_getter,
                salary_predicter
                )

            if lang == 'city':
                langs[lang] = stats[1]
            elif lang == 'website':
                langs[lang] = stats[2]
            else:
                langs[lang] = stats[0]

    return langs


if __name__ == '__main__':

    load_dotenv()
    sj_key = environ.get('SUPERJOB_TOKEN')

    stats_template = {
        'Javascript': 0,
        'Java': 0,
        'Python': 0,
        'Ruby': 0,
        'PHP': 0,
        'C++': 0,
        'C#': 0,
        'Go': 0,
        'city': '',
        'website': '',
    }

    try:
        hh_jobs = make_dict_of_jobs(
            stats_template,
            get_vacancies_from_hh,
            predict_rub_salary_for_hh
            )
    except requests.HTTPError():
        print(
            '''Headhunter server unavailable.
            You may have exceeded the number of requests.'''
            )
        raise

    try:
        sj_jobs = make_dict_of_jobs(
            stats_template,
            get_vacancies_from_sj,
            predict_rub_salary_for_sj,
            sj_key
            )
    except requests.HTTPError:
        print(
            '''Headhunter server unavailable.
            You may have exceeded the number of requests.'''
            )
        raise

    print_terminal_table(hh_jobs)
    print_terminal_table(sj_jobs)

