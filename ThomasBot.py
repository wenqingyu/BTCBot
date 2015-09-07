__author__ = 'Thomas Yu'

from time import sleep
import pprint

from api.tradeapi import BTCChina
from settings import *


class Bot:
    def __init__(self,tradeType):
        self.trader = BTCChina(API_ACCESS, API_SECRET,tradeType)
        self.portfolio = []
        self.profit = 0

    def get_lowest_market_ask(self, market_depth):
        return float(market_depth['market_depth']['ask'][0]['price'])

    def get_highest_market_bid(self, market_depth):
        return float(market_depth['market_depth']['bid'][0]['price'])

    def should_buy(self, lowest_ask, highest_bid):
        return lowest_ask - highest_bid > DIFFERENCE_STEP

    def get_orders(self):
        orders = None

        if DEBUG_MODE:
            print '---'
            print 'Attempting to get orders'

        for trial in xrange(MAX_TRIAL):
            response = self.trader.get_orders()

            if not response is None:
                orders = response['order']
                if DEBUG_MODE:
                    print 'Received order information'

                break

        return orders

    def cancel_order(self, order_id):
        if DEBUG_MODE:
            print '---'
            print 'Attempting to cancel order', order_id

        ret = None

        for trial in xrange(MAX_TRIAL):
            ret = self.trader.cancel(order_id)
            if not ret is None:
                if DEBUG_MODE:
                    print'Canceled order', order_id

                break

        return ret

    def reset(self):
        if CANCEL_ALL_ON_STARTUP:
            if DEBUG_MODE:
                print '---'
                print 'Attempting to cancel over night orders'

            orders = self.get_orders()
            while len(orders) > 0:
                if orders is None:
                    exit(1)

                for order in orders:
                    if self.cancel_order(order['id']) is None:
                        exit(1)
                orders = self.get_orders()

    def get_market_depth(self):
        market_depth = None

        for trial in xrange(MAX_TRIAL):
            market_depth = self.trader.get_market_depth({'limit': 1})
            if market_depth:
                break

        return market_depth

    def get_num_open_bids(self, orders):
        bid_count = 0
        if orders is None:
            return None

        for order in orders:
            if order['type'] == 'bid':
                bid_count += 1
        return bid_count

    def get_num_open_asks(self, orders):
        ask_count = 0
        if orders is None:
            return None

        for order in orders:
            if order['type'] == 'ask':
                ask_count += 1
        return ask_count

    def get_num_portfolio_bids(self):
        bid_count = 0
        for order in self.portfolio:
            if order['status'] == 'buy':
                bid_count += 1
        return bid_count

    def get_num_portfolio_asks(self):
        ask_count = 0
        for order in self.portfolio:
            if order['status'] == 'sell':
                ask_count += 1
        return ask_count

    def get_highest_bid(self):
        highest_bid = None
        highest_bid_price = -1
        for order in self.portfolio:
            if order['status'] == 'buy' and order['bid'] > highest_bid_price:
                highest_bid_price = order['bid']
                highest_bid = order
        return highest_bid

    def get_lowest_bid(self):
        lowest_bid = None
        lowest_bid_price = float('inf')
        for order in self.portfolio:
            if order['status'] == 'buy' and float(order['bid']) < lowest_bid_price:
                lowest_bid_price = float(order['bid'])
                lowest_bid = order
        return lowest_bid

    def get_lowest_ask(self):
        lowest_ask = None
        lowest_ask_price = float('inf')
        for order in self.portfolio:
            if order['status'] == 'sell' and float(order['ask']) < lowest_ask_price:
                lowest_ask_price = float(order['ask'])
                lowest_ask = order
        return lowest_ask

    def get_highest_bid_id(self, orders):
        highest_bid_id = None
        highest_bid_price = -1
        for order in orders:
            if order['type'] == 'bid' and float(order['price']) > highest_bid_price:
                highest_bid_price = float(order['price'])
                highest_bid_id = order['id']
        return highest_bid_id

    def get_lowest_bid_id(self, orders):
        lowest_bid_id = None
        lowest_bid_price = float('inf')
        for order in orders:
            if order['type'] == 'bid' and float(order['price']) < lowest_bid_price:
                lowest_bid_price = float(order['price'])
                lowest_bid_id = order['id']
        return lowest_bid_id

    def bid_filled(self, bid):
        for trial in xrange(MAX_TRIAL):
            response = self.trader.sell('{0:.2f}'.format(bid['ask']), BTC_AMOUNT)
            if response is True:
                bid['status'] = 'sell'

                if DEBUG_MODE:
                    print 'will sell at', bid['ask']

                break
            else:
                if DEBUG_MODE:
                    print 'Sell failed:', response

    def highest_bid_filled(self):
        highest_bid = self.get_highest_bid()

        if highest_bid is None:
            return

        if DEBUG_MODE:
            print '---'
            print 'Bid at', highest_bid['bid'], 'filled'
            print 'Attempting to put sell order at', highest_bid['ask']

        self.bid_filled(highest_bid)

    def lowest_ask_filled(self):
        lowest_ask = self.get_lowest_ask()

        if lowest_ask is None:
            return

        self.profit += (lowest_ask['ask'] - lowest_ask['bid']) * BTC_AMOUNT
        self.portfolio.remove(lowest_ask)

        if DEBUG_MODE:
            print '---'
            print 'Ask at', lowest_ask['ask'], 'filled, bought at', lowest_ask['bid']
            print 'current profit:', '\033[93m', self.profit, '\033[0m'

    def update_portfolio(self, check_old_orders=False):
        orders = self.get_orders()
        if orders is None:
            return None

        num_open_bids = self.get_num_open_bids(orders)
        num_open_asks = self.get_num_open_asks(orders)
        num_port_bids = self.get_num_portfolio_bids()
        num_port_asks = self.get_num_portfolio_asks()

        if DEBUG_MODE:
            print '---'
            print 'I have', num_port_asks - num_open_asks, 'asks filled'
            print 'I have', num_port_bids - num_open_bids, 'bids filled'

        for num_asks_filled in xrange(num_port_asks - num_open_asks):
            self.lowest_ask_filled()

        for num_bids_filled in xrange(num_port_bids - num_open_bids):
            self.highest_bid_filled()

        if check_old_orders:
            if len(self.portfolio) < MAX_OPEN_ORDERS:
                return orders

            lowest_bid_id = self.get_lowest_bid_id(orders)
            if lowest_bid_id is None:
                return orders

            my_lowest_bid = self.get_lowest_bid()
            my_lowest_bid_price = my_lowest_bid['bid']
            market_highest_bid = self.get_highest_market_bid(self.get_market_depth())

            if market_highest_bid - my_lowest_bid_price >= REMOVE_THRESHOLD:
                response = self.cancel_order(lowest_bid_id)
                if response is True:
                    self.portfolio.remove(my_lowest_bid)

        return orders

    def loop_body(self):
        orders = self.update_portfolio()
        if orders is None:
            return

        if DEBUG_MODE:
            print '---'
            print 'I recorded', self.get_num_portfolio_bids(), 'open bids,', self.get_num_portfolio_asks(), 'asks.'
            print 'API shows', self.get_num_open_bids(orders), 'open bids,', self.get_num_open_asks(orders), 'asks.'

        if len(self.portfolio) >= MAX_OPEN_ORDERS and REMOVE_UNREALISTIC:
            self.update_portfolio(True)

        if len(self.portfolio) >= MAX_OPEN_ORDERS:
            if DEBUG_MODE:
                print '---'
                print 'Too many open orders, sleep for', TOO_MANY_OPEN_SLEEP, 'seconds.'

            if GET_INFO_BEFORE_SLEEP:
                print '---'
                print 'I have', self.get_num_portfolio_bids(), 'open bids,', self.get_num_portfolio_asks(), 'asks.'
                print 'Total profit', '\033[93m', self.profit, '\033[0m'

            sleep(TOO_MANY_OPEN_SLEEP)
            return

        market_depth = self.get_market_depth()
        if not market_depth:
            return

        highest_bid = self.get_highest_market_bid(market_depth)
        lowest_ask = self.get_lowest_market_ask(market_depth)

        if not self.should_buy(lowest_ask, highest_bid):
            if DEBUG_MODE:
                print '---'
                print 'Market spread:', str(lowest_ask - highest_bid)
                print 'Nothing interesting, sleep for', NO_GOOD_SLEEP, 'seconds.'

            if GET_INFO_BEFORE_SLEEP:
                print '---'
                print 'I have', self.get_num_portfolio_bids(), 'open bids,', self.get_num_portfolio_asks(), 'asks.'
                print 'Total profit', '\033[93m', self.profit, '\033[0m'

            sleep(NO_GOOD_SLEEP)
            return

        my_bid_price = highest_bid + CNY_STEP
        my_ask_price = my_bid_price + MIN_SURPLUS

        if DEBUG_MODE:
            print '---'
            print 'Attempting to bid at', my_bid_price

        for trial in xrange(MAX_TRIAL):
            if self.trader.buy('{0:.2f}'.format(my_bid_price), BTC_AMOUNT):
                if DEBUG_MODE:
                    print 'I ordered', BTC_AMOUNT, 'bitcoins at', my_bid_price
                    print 'will sell at', my_ask_price

                self.portfolio.append(
                    {'bid': my_bid_price, 'ask': my_ask_price, 'status': 'buy'})
                break

    def start(self):
        self.reset()
        while True:
            self.loop_body()


if __name__ == '__main__':

    print "INITIALIZING ..."
    tradeType = "BTCCNY"
    b2cBot = Bot(tradeType)
    tradeType = "LTCCNY"
    l2cBot = Bot(tradeType)
    tradeType = "LTCBTC"
    l2bBot = Bot(tradeType)

    while(1 == 1):
        print "getting b2c"
        b2c_mkt_depth = b2cBot.get_market_depth()
        print "getting l2c"
        l2c_mkt_depth = l2cBot.get_market_depth()
        print "getting l2b"
        l2b_mkt_depth = l2bBot.get_market_depth()

        print "BTC to CNY"
        print "------------------------"
        print "ASK: "
        b2cAsk = b2cBot.get_lowest_market_ask(b2c_mkt_depth)
        print b2cAsk
        print "BID: "
        b2cBid = b2cBot.get_highest_market_bid(b2c_mkt_depth)
        print b2cBid

        print "LTC to CNY"
        print "------------------------"
        print "ASK: "
        l2cAsk = l2cBot.get_lowest_market_ask(l2c_mkt_depth)
        print l2cAsk
        print "BID: "
        l2cBid = l2cBot.get_highest_market_bid(l2c_mkt_depth)
        print l2cBid

        print "LTC to BTC"

        print "------------------------"
        print "ASK: "
        l2bAsk = l2bBot.get_lowest_market_ask(l2b_mkt_depth)
        print l2bAsk
        print "BID: "
        l2bBid = l2bBot.get_highest_market_bid(l2b_mkt_depth)
        print l2bBid
        print "------------------------"
        print "------------------------"

        print "P Simulation Start:"
        print "CNY -> BTC -> LTC -> CNY : Start with CNY: 10000"
        print "------------------------"
        print "After Balance: "
        pBalance = 10000.00 / b2cAsk / l2bAsk * l2cBid
        print pBalance

        print "N Simulation Start:"
        print "CNY -> BTC -> LTC -> CNY : Start with CNY: 10000"
        print "------------------------"
        print "After Balance: "
        nBalance = 10000.00 * b2cBid * l2bBid / l2cAsk
        print pBalance

        if(pBalance > 10000 or nBalance > 10000):
            print "HAHA"
            break














