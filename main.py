# upbit websocket을 이용한 실제 매매 예제
#
# 보다 자세한 내용을 아래 tistory 참고
# https://money-expert.tistory.com/41 : upbit websocket을 이용한 실제 매매 예제
# https://money-expert.tistory.com/42 : upbit 시세 주기적으로 받아서 매매 예제

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

# websocket으로 받은 시세를 처리하는 구조로 변환
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

# upbit api로 받은 시세를 처리하는 구조로 변환
def make_info_from_upbit_tickers(data) :
    info = {}
    info['ticker'] = data['market']
    info['date'] = data['trade_date_kst']
    info['time'] = data['trade_time_kst']
    info['ask_bid'] = ''
    info['open'] = float(data['opening_price'])  # 일봉 기준 시작가
    info['high'] = float(data['high_price'])
    info['low'] = float(data['low_price'])
    info['close'] = float(data['trade_price'])     # 최근 가격
    info['vol'] = float(data['trade_volume'])

    # change로 +/- 구분 change_rate : %
    info['change_rate'] = float(data['change_rate'])
    info['change'] = data['change'] # FALL or RISE
    info['acc_trade_qty_24h'] = float(data['acc_trade_volume_24h'])

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

    ticker = 'KRW-SBD'
    seed = 1000
    buy_perc = 0.03  # 시작가 대비 3% 오르면 매수
    sell_perc = 0.08 # 매수가 대비 8% 오르면 매도(익절)
    losscut = 0.03   # 매수가 대비 3% 내리면 losscut 매도(손절)
    tr_logic.init_set(buy_perc, sell_perc, losscut)

    # 새로 추가함.
    # 오늘 시초가를 받아온다. 
    # get_cur_price_all 함수를 사용하여 현재 가격을 받아온다. 여기에 opening_price가 오늘 시작가
    info = upbit.get_cur_price_all([ticker])
    if 'error' not in info[0] :
        start_price = info[0]['KRW-SBD']['opening_price']
    else :
        quit(0)
    
    tr_logic.set_start_price(start_price)

    trader = Trader(upbit, ticker, tr_logic, seed)
    
    # websocket을 이용하는 경우에는 1, 아니면 0
    USING_WEBSOCKET = 0
    # websocket 실간 시세를 이용하여 자동매매하기
    if USING_WEBSOCKET :
        display_web_socket_recv = 0
        while(1) :
            try :
                asyncio.get_event_loop().run_until_complete(my_connect(trader, ticker, display_web_socket_recv))
            except Exception as x: 
                print('websocket error : ', x)

            time.sleep(10)
    else :
        # 10초에 한번씩 최근 거래 값을 받아서 자동매매
        target_coins = [ticker] 
        while(1) :
            prices = upbit.get_cur_price_all(target_coins) # 
            if 'error' not in prices :
                ticker = target_coins[0]
                info = make_info_from_upbit_tickers(prices[0][ticker])
                trader.do_trading(info)

            time.sleep(10)
        
