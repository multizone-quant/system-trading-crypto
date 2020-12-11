import jwt
import time
from urllib.parse import urlencode

if __name__ == "__main__":
    from request_api import _send_get_request, _send_post_request, _send_delete_request
else :
    from pyupbit.request_api import _send_get_request, _send_post_request, _send_delete_request


def get_tick_size(price):
    if price >= 2000000:
        tick_size = round(price / 1000) * 1000
    elif price >= 1000000:
        tick_size = round(price / 500) * 500
    elif price >= 500000:
        tick_size = round(price / 100) * 100
    elif price >= 100000:
        tick_size = round(price / 50) * 50
    elif price >= 10000:
        tick_size = round(price / 10) * 10
    elif price >= 1000:
        tick_size = round(price / 5) * 5
    elif price >= 100:
        tick_size = round(price / 1) * 1
    elif price >= 10:
        tick_size = round(price / 0.1) * 0.1
    else:
        tick_size = round(price / 0.01) * 0.01
    return tick_size


class Upbit:
    def __init__(self, access, secret):
        self.access = access
        self.secret = secret

    def _request_headers(self, data=None):
        payload = {
            "access_key": self.access,
            "nonce": int(time.time() * 1000)
        }
        if data is not None:
            payload['query'] = urlencode(data)
        jwt_token = jwt.encode(payload, self.secret, algorithm="HS256").decode('utf-8')
        authorization_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorization_token}
        return headers

    # region balance
    def get_balance_all(self, contain_req=False):
        """
        전체 계좌 조회
        :param contain_req: Remaining-Req 포함여부
        :return: 내가 보유한 자산 리스트
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            url = "https://api.upbit.com/v1/accounts"
            headers = self._request_headers()
            result = _send_get_request(url, headers=headers)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x)
            print(x.__class__.__name__)
            return None

    # ticker == all이면 전체, 아니면 특정 ticker
    def get_balances(self, ticker="KRW", contain_req=False):
        """
        수정함
        특정 코인/원화의 잔고 조회
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 주문가능 금액/수량 (주문 중 묶여있는 금액/수량 제외)
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            ret = self.get_balance_all(contain_req=True)
            balances = ret[0]
            req = ret[1]

            result = []
            for x in balances:
                bal = {'ticker':x['currency'], 'total':float(x['locked'])+float(x['balance']), 'orderable':float(x['balance'])}
                if ticker == 'ALL' :
                    result.append(bal)
                elif x['currency'] == ticker:
                    result.append(bal)
                    break
            if contain_req:
                return result, req
            else:
                return result
        except Exception as x:
            print(x.__class__.__name__)
            return [{'error':{'message':'err get_balance'}}]
            

    def get_balance_t(self, ticker='KRW', contain_req=False):
        """
        특정 코인/원화의 잔고 조회(balance + locked)
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 주문가능 금액/수량 (주문 중 묶여있는 금액/수량 포함)
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            result = self.get_balances(contain_req=True)
            balances = result[0]
            req = result[1]

            for x in balances:
                if x['currency'] == ticker:
                    balance = float(x['balance'])
                    locked = float(x['locked'])
                    break
            if contain_req:
                return balance + locked, req
            else:
                return balance + locked
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def get_avg_buy_price(self, ticker='KRW', contain_req=False):
        """
        특정 코인/원화의 매수평균가 조회
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 매수평균가
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            result = self.get_balances(contain_req=True)
            balances = result[0]
            req = result[1]

            for x in balances:
                if x['currency'] == ticker:
                    avg_buy_price = float(x['avg_buy_price'])
                    break
            if contain_req:
                return avg_buy_price, req
            else:
                return avg_buy_price
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def get_amount(self, ticker, contain_req=False):
        """
        특정 코인/원화의 매수금액 조회
        :param ticker: 화폐를 의미하는 영문 대문자 코드 (ALL 입력시 총 매수금액 조회)
        :param contain_req: Remaining-Req 포함여부
        :return: 매수금액
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            result = self.get_balances(contain_req=True)
            balances = result[0]
            req = result[1]

            amount = 0
            for x in balances:
                if x['currency'] == 'KRW':
                    continue

                avg_buy_price = float(x['avg_buy_price'])
                balance = float(x['balance'])
                locked = float(x['locked'])

                if ticker == 'ALL':
                    amount += avg_buy_price * (balance + locked)
                elif x['currency'] == ticker:
                    amount = avg_buy_price * (balance + locked)
                    break
            if contain_req:
                return amount, req
            else:
                return amount
        except Exception as x:
            print(x.__class__.__name__)
            return None

    # endregion balance

    # region chance
    def get_chance(self, ticker, contain_req=False):
        """
        마켓별 주문 가능 정보를 확인.
        :param ticker:
        :param contain_req: Remaining-Req 포함여부
        :return: 마켓별 주문 가능 정보를 확인
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            url = "https://api.upbit.com/v1/orders/chance"
            data = {"market": ticker}
            headers = self._request_headers(data)
            result = _send_get_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    # endregion chance

    # region order
    def buy_limit_order(self, ticker, price, volume, contain_req=False):
        """
        지정가 매수
        :param ticker: 마켓 티커
        :param price: 주문 가격
        :param volume: 주문 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/orders"
            data = {"market": ticker,
                    "side": "bid",
                    "volume": str(volume),
                    "price": str(price),
                    "ord_type": "limit"}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__, x)
            return None

    def buy_market_order(self, ticker, price, contain_req=False):
        """
        시장가 매수
        :param ticker: ticker for cryptocurrency
        :param price: KRW
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/orders"
            data = {"market": ticker,  # market ID
                    "side": "bid",  # buy
                    "price": str(price),
                    "ord_type": "price"}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def sell_market_order(self, ticker, volume, contain_req=False):
        """
        시장가 매도 메서드
        :param ticker: 가상화폐 티커
        :param volume: 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/orders"
            data = {"market": ticker,  # ticker
                    "side": "ask",  # sell
                    "volume": str(volume),
                    "ord_type": "market"}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def sell_limit_order(self, ticker, price, volume, contain_req=False):
        """
        지정가 매도
        :param ticker: 마켓 티커
        :param price: 주문 가격
        :param volume: 주문 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/orders"
            data = {"market": ticker,
                    "side": "ask",
                    "volume": str(volume),
                    "price": str(price),
                    "ord_type": "limit"}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def cancel_order(self, uuid, contain_req=False):
        """
        주문 취소
        :param uuid: 주문 함수의 리턴 값중 uuid
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/order"
            data = {"uuid": uuid}
            headers = self._request_headers(data)
            result = _send_delete_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def get_order(self, ticker, state='wait', kind='normal', contain_req=False):
        """
        주문 리스트 조회
        :param ticker: market  수정함 'ALL' 추가
        :param state: 주문 상태(wait, done, cancel)
        :param kind: 주문 유형(normal, watch)
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        # TODO : states, uuids, identifiers 관련 기능 추가 필요
        try:
            url = "https://api.upbit.com/v1/orders"
            data = {
                    'state': state,
                    'kind': kind,
                    'order_by': 'desc'
                    }
            if ticker != 'ALL' :
                data['market'] = ticker

            headers = self._request_headers(data)
            result = _send_get_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None
    # endregion order


if __name__ == "__main__":
    with open("..\\upbit.txt") as f:
        lines = f.readlines()
        access = lines[0].strip()
        secret = lines[1].strip()

    # Upbit
    upbit = Upbit(access, secret)

    # 모든 잔고 조회
    # print(upbit.get_balances())

    # 잔고 조회
    print('== balance ex == ')
    bals = upbit.get_balances(ticker="KRW") # 원화 잔고
    bal = bals[0]
    if 'error' in bal :
        print(bal['error']['message']) 
    else :
        print(bal['ticker'], bal['total'], bal['orderable'])

    bals = upbit.get_balances(ticker="KRW-STEEM") # 특정 코인
    bal = bals[0]
    if 'error' in bal :
        print(bal['error']['message']) 
    else :
        print(bal['ticker'], bal['total'], bal['orderable'])

    bals = upbit.get_balances(ticker="ALL") # 모든 잔고
    bal = bals[0]
    if 'error' in bal :
        print(bal['error']['message']) 
    else :
        for bal in bals :
            print(bal['ticker'], bal['total'], bal['orderable'])

    if 0: # not supported right now
        print(upbit.get_amount('ALL'))  
        print(upbit.get_chance('KRW-HBAR'))

    print('-- get_order --')
    orders = upbit.get_order('KRW-BTC')
    if 'error' in orders :
        print(bal['error']['message']) 
    else :
        print (orders[0])
        for ord in orders :
            print(ord['market'], ord['uuid'], ord['side'], ord['price'], ord['remaining_volume'])
    if 0:
        #매도
        print(upbit.sell_limit_order("KRW-XRP", 1000, 20))

        # 매수
        print(upbit.buy_limit_order("KRW-XRP", 200, 20))

        # 주문 취소
        print(upbit.cancel_order('82e211da-21f6-4355-9d76-83e7248e2c0c'))

        # 시장가 주문 테스트
        upbit.buy_market_order("KRW-XRP", 10000)

        # 시장가 매도 테스트
        upbit.sell_market_order("KRW-XRP", 36)
