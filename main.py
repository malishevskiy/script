import requests
import json
import gspread
import config

subdomain = 'andmal1986'  # String shall be replaced with a valid link
link = f'https://{subdomain}.amocrm.ru'
headers = {'Authorization': f'Bearer {config.access_token}'}
command = '/api/v4/events'  # An HTTP request to the system of AmoCRM


# First entering into the system
def first_auth():
    client_id = input('Введите ID интеграции: ')
    secret_code = input('Введите секретный ключ: ')
    auth_code = input('Введите код авторизации: ')
    param = {
        'client_id': client_id,
        'client_secret': secret_code,
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': 'https://localhost.com'
    }
    resp = requests.post(f'https://{subdomain}.amocrm.ru/oauth2/access_token',
                         data=param)
    print(resp.text)
    return resp


# Refreshing of access token
def ref_token():
    client_id = input('Введите ID интеграции: ')
    secret_code = input('Введите секретный ключ: ')
    param = {
        'client_id': client_id,
        'client_secret': secret_code,
        'grant_type': 'refresh_token',
        'refresh_token': config.refresh_token,
        'redirect_uri': 'https://localhost.com'
    }
    resp = requests.post(f'https://{subdomain}.amocrm.ru/oauth2/access_token',
                         data=param)
    if resp.status_code == 200:
        data = resp.text
        save_tokens(data)
        print('Токен доступа обновлен. Перезапустите приложение.')
    else:
        print('Ошибка. Необходимо обновить refresh token или заново создать '
              'интеграцию.')
        return
    return


# Receipt of data from AmoCRM
def get_data():
    data_to_gsheets = list()
    print('Получение данных...')
    resp = requests.get(f'{link}{command}', headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        for i in data['_embedded']['events']:
            data_to_gsheets.append(i['type'])
        prep_data = '\n'.join(data_to_gsheets)
        save_data(prep_data)
        return
    if resp.status_code == 401:
        ref_token()
        return


# Saving of tokens in a config file
def save_tokens(data):
    token_list = json.loads(data)
    access_token = token_list['access_token']
    refresh_token = token_list['refresh_token']
    with open('config.py', 'w') as file:
        file.write(f"access_token = '{access_token}'\n"
                   f"refresh_token = '{refresh_token}'\n")
    return


# Checking for an empty cell in the column and saving of data in GS.
# File creds.json shall be replaced with a valid one.
# SheetsTest shall be referenced to a valid file
def save_data(data):
    cell_line = 1
    gc = gspread.service_account(filename='creds.json')
    sh = gc.open("SheetsTest")
    worksheet = sh.get_worksheet(0)
    while True:
        val = worksheet.cell(cell_line, 1).value
        if not val:
            worksheet.update_cell(cell_line, 1, data)
            print('Данные успешно сохранены.')
            return
        cell_line += 1


# Main function
def run_script():
    while True:
        reply = input('Код авторизации уже вводился (1 - да, 2 - нет)? ')
        if reply == '1':
            get_data()
            break
        if reply == '2':
            resp = first_auth()
            if resp.status_code == 200:
                data = resp.text
                save_tokens(data)
                print('Перезапустите приложение.')
                break
            if resp.status_code != 200:
                print('Ошибка. Проверьте данные авторизации.')
                break


if __name__ == '__main__':
    run_script()
