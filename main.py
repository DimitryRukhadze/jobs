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
        table_row = [param]

        for lang_info in table_params[param].values():
            table_row.append(lang_info)

        table_data.append(table_row)

    table = AsciiTable(table_data, title)
    print(table.table)


def get_vacancies_from_hh(prog_language, city):

    vacancies_url = 'https://api.hh.ru/vacancies'
    search_area_id = get_area_id_from_hh(city)

    params = {
        'per_page': 100,
        'text': f'Программист {prog_language}',
        'area': search_area_id,
    }

    response = requests.get(vacancies_url, params=params)
    response.raise_for_status()

    response_stats = response.json()
    all_salaries = []

    for page in range(response_stats['pages']):

        params['page'] = page

        page_response = requests.get(vacancies_url, params=params)
        page_response.raise_for_status()

        new_vacancies = page_response.json()['items']

        for vacancy in new_vacancies:
            salary = predict_rub_salary_for_hh(vacancy)
            if salary:
                all_salaries.append(salary)

        lang_stats = {
            'vacancies found': response_stats['found'],
            'vacancies processed': len(all_salaries),
            'average salary': int(sum(all_salaries)/len(all_salaries))
        }

    return lang_stats


def get_vacancies_from_sj(prog_lang, city, secret_key=''):

    auth_url = 'https://api.superjob.ru/2.0/vacancies/'

    auth_header = {
        'X-Api-App-Id': secret_key
    }

    search_params = {
        'count': 100,
        'town': city,
        'catalogues': 48,
        'keyword': f'Программист {prog_lang}',
    }

    city = search_params['town']

    response = requests.get(
        auth_url,
        headers=auth_header,
        params=search_params
        )
    response.raise_for_status()

    vacancies_found = response.json()['total']
    all_salaries = []

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
            salary = predict_rub_salary_for_sj(vacancy)
            if salary:
                all_salaries.append(salary)

        lang_stats = {
            'vacancies found': vacancies_found,
            'vacancies processed': len(all_salaries),
            'average salary': int(sum(all_salaries) / len(all_salaries))
        }

    return lang_stats


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


if __name__ == '__main__':

    load_dotenv()
    sj_key = environ.get('SUPERJOB_TOKEN')

    langs_template = [
        'Javascript',
        'Java',
        'Python',
        'Ruby',
        'PHP',
        'C++',
        'C#',
        'Go'
    ]

    hh_jobs = {}
    hh_city = 'Москва'
    hh_website = 'HeadHunter'

    try:
        for lang in langs_template:
            lang_statistics = get_vacancies_from_hh(lang, hh_city)
            hh_jobs[lang] = lang_statistics

    except requests.HTTPError():
        print(
            '''Headhunter server unavailable.
            You may have exceeded the number of requests.'''
            )
        raise

    sj_jobs = {}
    sj_city = 'Москва'
    sj_website = 'SuperJob'

    try:
        for lang in langs_template:
            lang_statistics = get_vacancies_from_sj(lang, sj_city, sj_key)
            sj_jobs[lang] = lang_statistics
    except requests.HTTPError:
        print(
            '''Superjob server unavailable.
            You may have exceeded the number of requests.'''
            )
        raise

    print_terminal_table(hh_jobs, hh_city, hh_website)
    print_terminal_table(sj_jobs, sj_city, sj_website)
