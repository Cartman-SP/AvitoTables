import requests
from datetime import datetime, timedelta
def get_access(client_id,client_secret):
    auth_url = "https://api.avito.ru/token"

    # Данные для получения токена доступа
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    # Выполняем запрос на получение токена доступа
    response = requests.post(auth_url, data=auth_data)
    # Проверяем успешность запроса
    if response.status_code == 200:
        return response.json().get('access_token')


def get_user_id(client_id,client_secret):
    access_token = get_access(client_id, client_secret)
    info_url = "https://api.avito.ru/core/v1/accounts/self"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(info_url, headers=headers)
    return response.json()['id']

def get_avance(client_id, client_secret):
    access_token = get_access(client_id, client_secret)
    balance_url = f"https://api.avito.ru/cpa/v2/balanceInfo"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.post(balance_url, headers=headers, json={})  
    if response.status_code == 200:
        balance_data = response.json()
        return balance_data['result']['balance']//100

def extract_ids(data):
    print(data)
    ids = [item['id'] for item in data['items']]
    return ','.join(ids)
def extract_avito_ids(data):
    avito_ids = [item['avito_id'] for item in data]
    return avito_ids
def merge_arrays(array1, array2):
    # Создание словаря для быстрого доступа по 'ad_id'
    ad_id_to_avito_id = {item['ad_id']: item['avito_id'] for item in array2}
    
    # Создание нового массива с объединенными данными
    result = [{'avito_id': ad_id_to_avito_id[item['id']], 'row': item['row']} for item in array1]
    
    return result
def get_date_range():
    # Получаем текущую дату
    today = datetime.today()
    
    # Завтрашняя дата
    tomorrow = today + timedelta(days=1)
    
    # Дата 250 дней назад от завтрашнего дня
    past_date = tomorrow - timedelta(days=250)
    
    # Форматируем даты в формате YYYY-MM-DD
    date_to = tomorrow.strftime('%Y-%m-%d')
    date_from = past_date.strftime('%Y-%m-%d')
    
    return {"dateTo": date_to, "dateFrom": date_from}
    

def merge_arrays2(array1, array2):
    result = []
    # Создаем словарь для быстрого доступа к элементам второго массива по ключу itemId
    stats_dict = {item['itemId']: item['stats'] for item in array2}
    
    for item1 in array1:
        avito_id = item1['avito_id']
        row = item1['row']
        status = item1['status']
        # Ищем элемент второго массива по avito_id в первом массиве
        if avito_id in stats_dict:
            stats = stats_dict[avito_id]
            uniqContacts = sum(stat.get('uniqContacts', 0) for stat in stats)
            uniqViews = sum(stat.get('uniqViews', 0) for stat in stats)
        else:
            uniqContacts = 0
            uniqViews = 0
        
        result.append({
            'row': row,
            'uniqContacts': uniqContacts,
            'uniqViews': uniqViews,
            'status': status
        })
    
    return result



def get_avito_ids(client_id, client_secret,cells):
    access_token = get_access(client_id, client_secret)
    info_url = "https://api.avito.ru/autoload/v2/items/avito_ids"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    print(cells)
    ids = extract_ids(cells)
    params = {
        'query': ids
    }
    response = requests.get(info_url, headers=headers, params=params)

    data = response.json()['items']
    data2 = cells['items']
    data3 = merge_arrays(data2,data)
    user_id = get_user_id(client_id,client_secret)
    itemIds = extract_avito_ids(data3)
    statistic_url = f"https://api.avito.ru/stats/v1/accounts/{user_id}/items"
    dates = get_date_range()
    dateFrom = dates['dateFrom']
    dateTo = dates['dateTo'] 
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': "application/json",
    }
    params={
        'dateFrom':dateFrom,
        'dateTo':dateTo,
        'itemIds':itemIds,
    }
    response = requests.post(statistic_url, headers=headers,json=params)
    answer = response.json()
    for i in range(len(data3)):
        item_id = data3[i]['avito_id']
        url = f"https://api.avito.ru/core/v1/accounts/{user_id}/items/{item_id}/"
        response = requests.get(url,headers=headers,)
        data3[i]['status'] = response.json()['status']
    result = merge_arrays2(data3,answer['result']['items'])
    return result



def get_balance(client_id, client_secret):
    access_token = get_access(client_id, client_secret)
    user_id = get_user_id(client_id,client_secret)

    balance_url = f"https://api.avito.ru/core/v1/accounts/{user_id}/balance/"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Source': 'Tester'
    }
    response = requests.get(balance_url, headers=headers)
    if response.status_code == 200:
        balance_data = response.json()
        return balance_data

