
import config
import requests

def get_weather():
    '''
    OpenWeather api (https://openweathermap.org/current) を使って天気情報を取得
    '''
    # リクエストの作成
    url = 'http://api.openweathermap.org/data/2.5/forecast'
    params = {
        'q': 'Yokohama', # city name
        'appid': config.OPEN_WEATHER_MAP_API_KEY,
        'lang': 'ja',
        'units': 'metric',
    }

    # GET リクエストを送信し、html を取得
    data = requests.get(url, params).json()
    
    '''
    data の中身 (See. https://openweathermap.org/current#current_JSON)
    {
        'cod': '200',
        'message': 0, 
        'cnt': 40,
        'list': [{
            'dt': 1628575200,
            'main': {
                'temp': 35.77,
                'feels_like': 42.77,
                'temp_min': 33.1,
                'temp_max': 35.77, 
                'pressure': 998, 
                'sea_level': 998, 
                'grnd_level': 998,
                'humidity': 51, 
                'temp_kf': 2.67
            },
            'weather': [{
                'id':801, 
                'main': 'Clouds', 
                'description': '薄い雲',
                'icon': '02d'
            }], 
            'clouds': {'all': 20}, 
            'wind': {'speed': 4.57, 'deg': 234, 'gust': 7.9}, 
            'visibility': 10000, 
            'pop': 0,
            'sys': {'pod': 'd'}, 
            'dt_txt': '2021-08-10 06:00:00'
        }, ... ], 
        'city': {
            'id': 1848354, 
            'name': '横浜市', 
            'coord': {'lat': 35.4478, 'lon': 139.6425}, 
            'country': 'JP', 
            'population': 3574443, 
            'timezone': 32400, 
            'sunrise': 1628538999, 
            'sunset': 1628588228
        }
    }
    '''

    # データ整形
    '''
    整形後
    {  
        'date1': {
            'time1': { temp, weather }, 
            'time2': { temp, weather }, 
            ...,
        },
        'date2': {
            'time1': { temp, weather }, 
            'time2': { temp, weather }, 
            ...,
        },
        ...,
    }
    '''
    formated_data = {}
    for d in data['list']:
        # 日付と時刻の取得
        date, time = d['dt_txt'].split(' ')

        # 日付の変換 2021-01-01 -> 2021年1月1日
        year, month, day = date.split('-')
        date = str(year) + '年' + str(int(month)) + '月' + str(int(day)) + '日'

        # 時刻の変換 09:00:00 -> 9時
        time = str(int(time[:2])) + '時'

        # 日付毎にdictを作成
        if not date in formated_data:
            formated_data[date] = {}

        formated_data[date][time] = {
            'temp': d['main']['temp'],
            'weather': d['weather'][0]['description']
        }
    
    return {'city': data['city']['name'], 'data': formated_data}