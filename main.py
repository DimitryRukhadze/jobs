import requests


from dotenv import load_dotenv
from os import environ
from terminaltables import AsciiTable


def get_area_id_from_hh(area_name):

    area_url = 'https://api.hh.ru/areas'

    response = requests.get(area_url)
    response.raise_for_status()

    countries = response.json()

    for country in countries:
        if area_name in country.values():
            return country['id']
        for region in country['areas']:
            if area_name in region.values():
                return region['id']
            for city in region['areas']:
                if area_name in city.values():
                    return city['id']


def print_terminal_table(table_params, header_website, header_city):

    title = f"{header_website} {header_city}"
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

            for lang_info in table_params[param].values():
                table_row.append(lang_info)

            table_data.append(table_row)

    table = AsciiTable(table_data, title)
    print(table.table)


def get_vacancies_from_hh(prog_language):

    vacancies_url = 'https://api.hh.ru/vacancies'
    city = 'Москва'
    website = 'HeadHunter'
    search_area_id = get_area_id_from_hh(city)

    params = {
        'per_page': 100,
        'text': f'Программист {prog_language}',
        'area': search_area_id,
    }

    response = requests.get(vacancies_url, params=params)
    response.raise_for_status()

    hh_vacancies = []

    response_stats = response.json()

    for page in range(response_stats['pages']):

        params['page'] = page

        page_response = requests.get(vacancies_url, params=params)
        page_response.raise_for_status()

        new_vacancies = page_response.json()['items']

        for vacancy in new_vacancies:
            hh_vacancies.append(vacancy)

    return response_stats['found'], hh_vacancies, city, website


def get_vacancies_from_sj(prog_lang, secret_key=''):

    auth_url = 'https://api.superjob.ru/2.0/vacancies/'

    auth_header = {
        'X-Api-App-Id': secret_key
    }

    search_params = {
        'count': 100,
        'town': 'Москва',
        'catalogues': 48,
        'keyword': f'Программист {prog_lang}',
    }

    city = search_params['town']

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
    elif salary_from:
        return salary_from*1.2
    elif salary_to:
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

    lang_stats = {}

    if vacancy_getter == get_vacancies_from_sj:
        jobs_found, language_jobs, city, website = vacancy_getter(
            language,
            key_for_getter
            )

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


def make_dict_of_jobs(dict_tempate, headers_template, job_getter, salary_predicter, secret_key=''):
    langs = dict_tempate.copy()
    headers = headers_template.copy()

    if job_getter == get_vacancies_from_sj:
        for lang in langs.keys():
            stats = make_vacancies_stats_by_lang(
                lang,
                job_getter,
                salary_predicter,
                key_for_getter=secret_key
                )

            langs[lang] = stats[0]
            if not headers['city']:
                headers['city'] = stats[1]
            if not headers['website']:
                headers['website'] = stats[2]
    else:
        for lang in langs.keys():
            stats = make_vacancies_stats_by_lang(
                lang,
                job_getter,
                salary_predicter
                )

            langs[lang] = stats[0]

            if not headers['city']:
                headers['city'] = stats[1]
            if not headers['website']:
                headers['website'] = stats[2]

    return langs, headers


if __name__ == '__main__':

    load_dotenv()
    sj_key = environ.get('SUPERJOB_TOKEN')

    langs_template = {
        'Javascript': 0,
        'Java': 0,
        'Python': 0,
        'Ruby': 0,
        'PHP': 0,
        'C++': 0,
        'C#': 0,
        'Go': 0,
    }

    table_headers_template = {
        'city': '',
        'website': '',
    }

    try:
        hh_jobs, hh_headers = make_dict_of_jobs(
            langs_template,
            table_headers_template,
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
        sj_jobs, sj_headers = make_dict_of_jobs(
            langs_template,
            table_headers_template,
            get_vacancies_from_sj,
            predict_rub_salary_for_sj,
            sj_key
            )
    except requests.HTTPError:
        print(
            '''Superjob server unavailable.
            You may have exceeded the number of requests.'''
            )
        raise

    print_terminal_table(hh_jobs, hh_headers['city'], hh_headers['website'])
    print_terminal_table(sj_jobs, sj_headers['city'], sj_headers['website'])
