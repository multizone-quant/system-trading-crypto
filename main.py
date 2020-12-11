# upbit websocket을 이용한 실제 매매 예제
#
# 보다 자세한 내용을 아래 tistory 참고
# https://money-expert.tistory.com/41
#

import json
import csv
from  datetime import datetime
import time
#from myplot import *

from TR_FOLLOW import *
from Trader import *
from jpy_upbit import *

import websockets
import asyncio
import json

UPBIT_WEB_SOCKET_ADD = 'wss://api.upbit.com/websocket/v1'


def make_info_from_upbit_real(data) :
    info = {}
    info['ticker'] = data['code']
    info['date'] = data['trade_date']
    info['time'] = data['trade_time']
    info['ask_bid'] = 'sell'
    if data['ask_bid'] == 'BID' :
        info['ask_bid'] = 'buy'
    info['open'] = data['trade_price']
    info['high'] = data['trade_price']
    info['low'] = data['trade_price']
    info['close'] = data['trade_price']
    info['qty'] = data['trade_volume']
    return info


recv_cnt = 0
async def my_connect(real, ticker, show) :
    global recv_cnt
    async with websockets.connect(UPBIT_WEB_SOCKET_ADD) as websocket:
        cmd = '[{"ticket":"test1243563478"},{"type":"trade","codes":["' + ticker + '"]}]'
        await websocket.send(cmd)
        print('upbit connected', recv_cnt)
        recv_cnt = 0
        while(1) :
            data_rev = await websocket.recv()
            my_json = data_rev.decode('utf8').replace("'", '"')
            data = json.loads(my_json)
            if show :
                print(data['code'], data['trade_time'], data['ask_bid'], data['trade_price'], data['trade_volume'])
            if 'type' in  data :
                if data['type'] == 'trade' :
                    info = make_info_from_upbit_real(data)
                    real.do_trading(info)
            recv_cnt += 1


if __name__ == '__main__':
    access = 'my acess'
    secret = 'my secret'

    upbit = MyUpbit(access, secret)
    # 상승 따라가기
    tr_logic = TR_FOLLOW_TREND('min', 1) # candle정보는 무시

    ticker = 'KRW-LBC'
    seed = 1000
    buy_perc = 0.01  # 시작가 대비 3% 오르면 매수
    sell_perc = 0.01 # 매수가 대비 10% 오르면 매도(익절)
    losscut = 0.01   # 매수가 대비 losscut 내리면 매도(손절)
    tr_logic.init_set(buy_perc, sell_perc, losscut)

    start_price = 102 # 시작가, 로직에 따라 시초가일 수도 있고, 이전 30분 candle의 open 가격일 수 있음.
    tr_logic.set_start_price(start_price)

    trader = Trader(upbit, ticker, tr_logic, seed)
    display_web_socket_recv = 0
    while(1) :
        try :
            asyncio.get_event_loop().run_until_complete(my_connect(trader, ticker, display_web_socket_recv))
        except Exception as x: 
            print('websocket error : ', x)

        time.sleep(10)

