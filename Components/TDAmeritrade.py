import os
import math
import json
import tdameritrade
from tdameritrade import auth
import requests
from dotenv import load_dotenv,find_dotenv

load_dotenv(find_dotenv())

#TODO Create decorator for client session
class TDAmeritrade:

    def __init__(self):
        self.td_client = None
        self.access_token = None

    def get_client_session(self):
        return self.td_client

    def start_client_session(self):
        self.get_ameritrade_access_token_from_refresh_token()
        self.td_client = tdameritrade.TDClient(self.access_token)

    def get_ameritrade_access_token(self):
        # TODO copy chromedriver to "/usr/local/bin/chromedriver" if doesn't exist
        consumer_key=os.getenv("TDAMERITRADE_CLIENT_ID")
        uri = os.getenv("TDAMERITRADE_URI")
        response = auth.authentication(consumer_key, uri, os.getenv("TDAMERITRADE_USERNAME"), os.getenv("TDAMERITRADE_PASSWORD"))
        self.access_token = response['access_token']
        return self.access_token

    def get_ameritrade_access_token_from_refresh_token(self):
        REFRESH_TOKEN = os.getenv('TDAMERITRADE_REFRESH_TOKEN')
        CONSUMER_KEY = os.getenv('TDAMERITRADE_CLIENT_ID')
        ACCESS_TOKEN_ENDPOINT = os.getenv('ACCESS_TOKEN_ENDPOINT')
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': REFRESH_TOKEN,
            'client_id': CONSUMER_KEY
        } #TODO try except catch block incase error
        response = requests.post(url=ACCESS_TOKEN_ENDPOINT, data=payload, verify=True)
        self.access_token = response.json()['access_token']
        return self.access_token

    def get_stock_quote(self, symbol):
        """
        Get the stock Quote with the given symbol
        :param symbol:
        :return:
        """
        self.start_client_session()
        quote = self.td_client.quote(symbol)

        if quote:
            return quote[symbol]
        else:
            return {}

    def get_orders(self):
        result = self.td_client.accounts(orders=True)
        return result

    def buy_stock_with_cash_limit(self, symbol, cash_limit):
        """
        Buys as many stock as possible with the given cash limit at market value
        :param symbol: the stock symbol
        :param cash_limit: cash limit as float
        :return: stock order quantity placed or False if order not placed
        """
        quote = self.get_stock_quote(symbol)
        ask_price = quote["askPrice"]
        stock_order_quantity = math.floor(cash_limit / ask_price)
        if stock_order_quantity:
            try:
                self.place_stock_order(symbol, stock_order_quantity, "Buy")
                return stock_order_quantity
            except Exception as e:
                print(e)
                return False
        else:
            return False

    def place_stock_order(self, symbol, quantity, instructions):
        """
        places an order with the given symbol. For more details visits:
        https://developer.tdameritrade.com/content/place-order-samples
        :param symbol: the company symbol
        :param quantity: how many stock to place in the order
        :param instructions: Buy or Sell
        :return: True or False if order was placed
        """
        self.start_client_session()
        accountId = os.getenv('TDAMERITRADE_ACCOUNT_ID')
        order = {
              "orderType": "MARKET",
              "session": "NORMAL",
              "duration": "DAY",
              "orderStrategyType": "SINGLE",
              "orderLegCollection": [
                {
                  "instruction": instructions,
                  "quantity": quantity,
                  "instrument": {
                    "symbol": symbol,
                    "assetType": "EQUITY"
                  }
                }
              ]
        }
        url = f"https://api.tdameritrade.com/v1/accounts/{accountId}/orders"
        headers = {'Authorization': 'Bearer ' + self.access_token, "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=order)
        if not response.status_code == 201:
            print("Order Status Not Complete. Status Code: {}".format(response.status_code))
            return False
        return True

    def get_all_positions(self):
        """
        Gets all positions currently in account
        :return: dict of all positions found
        """
        act = self.td_client.accounts(positions=True)
        positions = act[list(act.keys())[0]]['securitiesAccount']['positions']
        return positions

    def get_single_position(self, symbol):
        """
        Gets a single given position from the account
        :return: the position if found else empty dict
        """
        all_positions = self.get_all_positions()
        found_position = {}
        if not all_positions:
            return found_position
        for position in all_positions:
            if position['instrument']['symbol'] == symbol:
                found_position = position
                break
        return found_position

if __name__ == '__main__':
    my_tdameritrade = TDAmeritrade()
    quote = my_tdameritrade.get_stock_quote("LK")
    positions = my_tdameritrade.get_all_positions()
    position = my_tdameritrade.get_single_position("CCL")
    print(position)
    # order = my_tdameritrade.place_stock_order("CCL", position['longQuantity'], "Sell")
    # print(order)

