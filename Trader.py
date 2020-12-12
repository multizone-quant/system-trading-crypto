# upbit websocket을 이용한 실제 매매 예제
#
# 보다 자세한 내용을 아래 tistory 참고
# https://money-expert.tistory.com/41
#


import json
import csv
from  datetime import datetime
import time

from my_util import *
from jpy_upbit import *
from TR_FOLLOW import *

class sim_stat :
    def __init__(self, init_seed) :
        self.init_seed = init_seed
        self.num_trading = 0
        self.total_profit = 0
        self.total_fee = 0
        self.num_winning = 0
        self.num_losing = 0
        self.max_loss = 0
        self.max_gain = -10000000
        self.mdd = 0

    def get_profit_percent(self) :
        return self.total_profit / self.init_seed  * 100

    def update_stat(self, profit) :
        self.total_profit += profit # 누적 수익
        if profit > 0 :
            self.num_winning += 1
        else :
            self.num_losing += 1

        # 최대 손실, 최고 이익 값 update
        if self.max_loss > self.total_profit :
            self.max_loss = self.total_profit
        if self.max_gain < self.total_profit :
            self.max_gain = self.total_profit
                    
        # draw down 계산
        if self.max_gain == 0 :
            dd = 0
        else :
            dd = 100.0 * (self.max_gain - self.total_profit) / (self.init_seed + self.max_gain)
        if dd > self.mdd :
            self.mdd = dd  # mdd 계산
        return dd

class Trader() :
    def __init__(self, exchange, ticker, tr_logic, seed) : 
        self.exchange = exchange
        self.ticker = ticker
        self.init_seed = seed   # 1회 최대 매수액
        self.balance = seed   # 현재 잔고

        self.trading_fee = 0.0005  # 매매 수수료

        self.tr_logic = tr_logic # trading logic
        self.stat = sim_stat(seed)   # 통계 변수용 class

        self.buying_order_info = {}  #매수 중인 주문정보        
        self.pre_tick_info = {} # 최근 tick info

    def handle_fee(self, price, qty) :
        fee = qty * price * self.trading_fee
        self.stat.total_fee += fee
        self.balance -= fee

    # info에 있는 ticker에 대하여 처리한다.
    def do_trading(self, info) :
        self.pre_tick_info = info
        self.tr_logic.add_tick(info)

        if self.buying_order_info == {} : # 매수 대기 중
            buy_price = self.tr_logic.is_enter_condition(info) 
            if buy_price > 0 : # 매수조건임
                amount = min(self.balance, self.init_seed)

                # 살 수량 결정
                buying_vol = amount / buy_price    # 매수 주수
                if buying_vol > 10 :    #10개 보다 크면 소숫점 0
                    buying_vol = int(buying_vol)
                elif buying_vol > 0 :   #0개 보다 크면 소숫점 2
                    buying_vol = float(format(buying_vol,'.2f'))
                else :                  #0개 적으면 크면 소숫점 4
                    buying_vol = float(format(buying_vol,'.4f'))

                self.do_new_order('buy', buy_price, buying_vol)

        else : # 이미 매수함
            sell_price, losscut = self.tr_logic.is_exit_condition(info)  #
            if sell_price > 0 : # 매도 조건
                # 매도 주문 
                # 매도 가격 : tr_logic에서 결정한 값, 
                # 매도 수량 : 매수 수량
                self.do_new_order('sell', sell_price, self.buying_order_info['org_qty'])

    def buy_done(self, uuid, price, qty) :
        self.buying_order_info = {'uuid' : uuid, 'bid_ask': 'buy', 'status': 1, 'org_qty' : qty, 'done_qty' : '0.0', 'price':price}
        self.handle_fee(price, qty) # 매수 수수료
        # update statistics
        self.stat.num_trading += 1  # 매수한 주문 수
            
    def sell_done(self, price, qty) :
        profit = (price - self.buying_order_info['price']) * qty
        self.balance += profit

        # 3. 매도 수수료
        self.handle_fee(price, qty) # 매도 수수료

        # 4. update statistics
        dd = self.stat.update_stat(profit)
                
        print('profit : ', profit, 'total_profit : ', self.stat.total_profit)

        self.buying_order_info = {} # 매수한 것이 없음

    # bid_ask : 'buy' or 'sell'                    
    def do_new_order(self, bid_ask, price, qty) :
        ss = "["+self.ticker+'] ' + get_time_str() + " " + bid_ask + ' [ ' + str(price) + ' , ' +str(qty) + ' ] '
        if bid_ask == 'sell' :
            result = self.exchange.sell_limit_order(self.ticker, price, qty)
            if 'uuid' in result[0] : # 매도 주문 성공
                print('sell order ok', ss)
                self.sell_done(price, qty)
            else :
                print('sell order err', ss)
                ss = "     " + result[0]['error']['message']
                print(ss)

        if bid_ask == 'buy' :
            result = self.exchange.buy_limit_order(self.ticker, price, qty)
            if 'uuid' in result[0] : # 매수 주문 성공
                uuid = result[0]['uuid']
                self.buy_done(uuid, price, qty)
                print('buy  order ok', ss)
            else :
                print('buy  order err', ss)
                ss = "     " + result[0]['error']['message']
                print(ss)


if __name__ == '__main__':
    
    print('Trader')
