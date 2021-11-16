import requests
import re


class TrainService:
    def scrape_trains_delay_info(self, train_id: str):

        # html の取得
        html = requests.get(
            f'https://transit.yahoo.co.jp/traininfo/detail/{train_id}/0/'
        ).text

        # 取得したHTMLから運行情報を切り出し
        # <dd>タグにカッコまれた要素を取得(class="trouble"は何かしらの遅延が発生)
        pattern = re.compile(
            r'<dd class="trouble">([.\s\S]*?)</dd>'  # 正規オブジェクトの生成
        )
        result = pattern.findall(html)
        if len(result) == 0:
            return '遅延はありません。'

        # 遅延情報を整形
        pattern = re.compile(r'<p>(.*?)<span>(.*?)</span></p>')
        result = pattern.findall(result[0])
        # 遅延情報詳細 + 掲載日時
        return result[0][0] + result[0][1]

    def get_trains_delay_info(self):
        '''
        https://transit.yahoo.co.jp/traininfo/top より各路線の運行情報が記載されたページのhtmlを取得し、
        運行情報を返す
        '''
        return {
            '京浜東北線': self.scrape_trains_delay_info('22'),
            '横須賀線': self.scrape_trains_delay_info('29'),
        }
