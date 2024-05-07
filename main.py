# 楽天モバイルのプラチナバンド免許を取得

import json
import os
import ssl
from urllib import request, parse

import pandas as pd
import plotly.figure_factory as ff
import tweepy

Rakuten = {
    # 1:免許情報検索  2: 登録情報検索
    'ST': 1,
    # 詳細情報付加 0:なし 1:あり
    'DA': 1,
    # スタートカウント
    'SC': 1,
    # 取得件数
    'DC': 2,
    # 出力形式 1:CSV 2:JSON 3:XML
    'OF': 2,
    # 無線局の種別 基地局(PHS除く)
    'OW': 'FB',
    # 所轄総合通信局
    'IT': '',
    # 都道府県/市区町村
    'HCV': '',
    # 免許人名称/登録人名称
    'NA': '楽天モバイル',
    # 周波数(始)
    'FF' : 700,
    # 周波数(終)
    'TF' : 799,
    # 周波数(単位) # 1:kHz 2:MHz 3:GHz
    'HZ' : 2
}

def musen_api(d):

    params = parse.urlencode(d, encoding='shift-jis')

    req = request.Request(f'https://www.tele.soumu.go.jp/musen/list?{params}')

    ctx = ssl.create_default_context()

    ctx.options |= 0x4

    with request.urlopen(req, context=ctx) as res:
        return json.loads(res.read())
    
data = musen_api(Rakuten)

data_list = list()

for v in data['musen']:

    temp_dic = dict()

    temp_dic['交付日'] = v['listInfo']['licenseDate'].replace('-', '/')

    temp_dic['設置場所'] = v['listInfo']['tdfkCd']

    # 電波の型式、周波数及び空中線電力のデータを整形
    radioSpec_list = v['detailInfo']['radioSpec1'].split('\\t')

    # 各要素から空白文字を削除する
    radioSpec_list = [''.join(item.split()) for item in radioSpec_list]

    temp_dic['電波の型式'] = radioSpec_list[0]

    temp_dic['周波数'] = radioSpec_list[1]

    temp_dic['空中線電力'] = radioSpec_list[2]

    data_list.append(temp_dic)

# 前回データを読み込み
with open('data/data.json', 'r') as f:
    previous_data = json.load(f)

# 差分抽出(前回更新データと比較)
diff_list = [item for item in data_list if item not in previous_data]


if len(diff_list) != 0:
    
    # print('更新データあり')

    df = pd.json_normalize(data_list, )

    fig = ff.create_table(df)

    # scale=10だと400 Bad Request
    fig.write_image('data/diff.png', engine='kaleido', scale=1)

    # 最新データ保存
    with open('data/data.json', 'w') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)

    # SNS送信用テキスト
    text = f'プラチナバンドの免許が {len(diff_list)}件 追加されました\n#楽天モバイル #bot'

    # Twitter
    api_key = os.environ['API_KEY']
    api_secret = os.environ['API_SECRET_KEY']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    client = tweepy.Client(consumer_key = api_key, consumer_secret = api_secret, access_token = access_token, access_token_secret = access_token_secret,)

    media_ids = []
    res_media_ids = api.media_upload('data/diff.png')
    media_ids.append(res_media_ids.media_id)
    client.create_tweet(text = text, media_ids=media_ids)
