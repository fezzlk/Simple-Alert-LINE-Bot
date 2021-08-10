import requests
import re

def scrape_trains_delay_info(train_id):
    # html の取得
    html = requests.get(f'https://transit.yahoo.co.jp/traininfo/detail/{train_id}/0/').text
    
    # 取得したHTMLから運行情報を切り出し
    '''
	<dd>タグにカッコまれた要素を取得(class="trouble"は何かしらの遅延が発生)
	'''
    pattern = re.compile(r'<dd class="trouble">([.\s\S]*?)</dd>')	# 正規オブジェクトの生成
    result = pattern.findall(html)
    print('result:::', result)
    if result is None or len(result) == 0:
        return '遅延はありません。'
	
    # 遅延情報を整形
    pattern = re.compile(r'<p>(.*?)<span>(.*?)</span></p>')
    result = pattern.findall(result)
    print(result)
    return '遅延あり'
    # return result[0][1] + result[0][2] # 遅延情報詳細 + 掲載日時

def get_trains_delay_info():
    '''
	https://transit.yahoo.co.jp/traininfo/top より各路線の運行情報が記載されたページのhtmlを取得し、
    運行情報を返す
    '''
    return {
        '京浜東北線': scrape_trains_delay_info('22'), 
        '横須賀線': scrape_trains_delay_info('29'),
    }    
