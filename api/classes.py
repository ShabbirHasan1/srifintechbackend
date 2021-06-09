import datetime as dt
import io
import math
import os
import sys
import webbrowser
from configparser import ConfigParser

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlalchemy
import yfinance as yf
from flask import send_file
from kiteconnect import KiteConnect
from matplotlib.figure import Figure
from sqlalchemy import create_engine
from sqlalchemy import Table, MetaData
from collections import OrderedDict
from datetime import datetime,date,timedelta

import logging
from pprint import pformat


class KiteAuthentication:
    """
    This class performs Kite Authentication.  It reads api key, access token details from a file
    and sets access token to authenticate the apis.
    """

    def __init__(self, request_token=None):
        self.request_token = request_token
        self.debug = False
        self.api_key = 'ydq5afgjqoqvj0up'
        self.api_secret = 'mlwdiwz24dnwpsu9jtozht4n4c5zncjb'
        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token = ''
        self.access_details_json = dict()
        # self.access_details = []
        # self.temp_path = os.getcwd()
        self.new_path = r'C:\Users\skoppuravur6\Google Drive\Personal\AlgoTrading\Access Tokens'  # ==> This is the path for credentials
        self.file_name = 'access_token.txt'
        self.kiteauth_table_name = 'kiteauth'
        self.ticker = ''
        self.kite_login_success = False
        self.pg = None
        if self.request_token is None:
            self.read_access_details_usingdb()
        self.get_login()

    def read_access_details_usingdb(self):
        
        ####PLease uncomment here later###
        self.pg = PostgreSQLOperations()
        df = self.pg.get_postgres_data_df_with_condition(table_name=self.kiteauth_table_name) 
        self.access_token = df['access_token'].values[0]
        ###PLease uncomment here later###
        
        
        if self.debug:
            print("Access token fetched # ", self.access_token)

    def get_login(self):
        if self.debug:
            print('Authentication in progress with request token #', self.request_token)
            
        try:
            if self.debug:
                print(f'Trying with access token # {self.access_token}')
            self.kite.set_access_token(self.access_token)

            profile = self.kite.profile()
            print("Authentication successful for user: ", profile['user_name'])
            self.kite_login_success = True

        except Exception as e:
            print('But Failed with exception # ', e)
            if self.request_token is None:
                print('Opening the browser because request token is not there ')
                wb = webbrowser
                url = self.kite.login_url()
                print("[*] Generate Access Token: ", self.kite.login_url())
                wb.open(url)

            else:
                print('Generated request token # ', self.request_token)
                data = self.kite.generate_session(self.request_token, api_secret=self.api_secret)
                self.access_token = data['access_token']
                self.kite.set_access_token(self.access_token)
                if self.debug:
                    print('Access token generated Successfully # ', self.access_token)
                # self.access_details_json['access_token'] = self.access_token
                # self.write_access_token()
                # print("Access token for the day: ", self.access_token)
                # ***************Begin Update Heroku Database****************#

                # connection_string = 'postgres://udqyfefmncjjbd:799e85c504daf894d442a1f2b8d0714c6999fe740117fe45a52643f38e15b408@ec2-54-152-40-168.compute-1.amazonaws.com:5432/d74jj2uvqnspcb'
                connection_string = 'postgresql://doadmin:or5ka898vk8r1wdi@srifintech-db-do-user-8454140-0.b.db.ondigitalocean.com:25060/defaultdb'
                try:
                    db = create_engine(connection_string)
                    query = "UPDATE kiteauth SET access_token = " + "'" + str(self.access_token) + "'"
                    db.execute(query)
                    if self.debug:
                        print("Access token updated in Heroku DB")
                except Exception as e:
                    print('Access token update in Heroku DB failed # ', e)

                # ***************End Update Heroku Database****************#

    def set_access_token(self, request_token):
        self.request_token = request_token
        data = self.kite.generate_session(self.request_token, api_secret=self.api_secret)
        self.access_token = data['access_token']
        self.kite.set_access_token(self.access_token)
        if self.debug:
            print('Access token generated successfully # ', self.access_token)

        # ***************Begin Update Heroku Database****************#
 
        # connection_string = 'postgres://udqyfefmncjjbd:799e85c504daf894d442a1f2b8d0714c6999fe740117fe45a52643f38e15b408@ec2-54-152-40-168.compute-1.amazonaws.com:5432/d74jj2uvqnspcb'
        connection_string = 'postgresql://doadmin:or5ka898vk8r1wdi@srifintech-db-do-user-8454140-0.b.db.ondigitalocean.com:25060/defaultdb'
        try:
            db = create_engine(connection_string)
            query = "UPDATE kiteauth SET access_token = " + "'" + str(self.access_token) + "'"
            db.execute(query)
            if self.debug:
                print("Access token updated in Heroku DB")
        except Exception as e:
            print('Access token update in Heroku DB failed # ', e)

        # ***************End Update Heroku Database****************#


class KiteFunctions(KiteAuthentication):

    def __init__(self):
        #
        self.current_date = dt.datetime.now().date()
        self.ticker = ''
        self.instrument_token = 0
        self.master_instruments_url = 'https://api.kite.trade/instruments'
        self.ticker_df = pd.DataFrame()
        try:
            self.master_instruments_df = pd.read_csv(self.master_instruments_url)
        except Exception as e:
            print('cannot read master instruments.  Error # ', e)
        self.master_instruments_df['expiry'] = pd.to_datetime(self.master_instruments_df['expiry']).dt.date

        self.ka = KiteAuthentication()
        self.kite = KiteConnect(api_key=self.ka.api_key, access_token=self.ka.access_token)

        self.history_list = []
        self.debug = False
        self.nse_stocks_df = pd.DataFrame()
        self.fno_stocks_df = pd.DataFrame()
        self.fno_stock_list = list()
        self.nse_stocks_list = list()
        self.strikes_df = pd.DataFrame()
        self.history_df = pd.DataFrame()
        self.interval_1minute = 'minute'
        self.interval_day = 'day'
        self.interval_3minute = '3minute'
        self.interval_5minute = '5minute'
        self.interval_10minute = '10minute'
        self.interval_15minute = '15minute'
        self.interval_30minute = '30minute'
        self.interval_1hour = '60minute'

    def get_root_ticker_for_instrument_token(self, instrument_token):
        """
        Returns Underlying Root Ticker if Instrument Token is passed to this function
        :param instrument_token: Instrument token fetched from net / day positions in Kite.
        :return: Root Underlying Stock in String
        """
        return \
            self.master_instruments_df[self.master_instruments_df['instrument_token'] == instrument_token][
                'name'].values[0]

    def get_underlying_list_in_positions(self):
        """
        Gives underlying stocks list for all the open net positions
        :return: underlying stocks in list datatype
        """

        total_positions = self.ka.kite.positions()
        net_positions_list = total_positions['net']
        underlying_list = list()
        for position in net_positions_list:
            instrument_token = position['instrument_token']
            root_ticker = self.get_root_ticker_for_instrument_token(instrument_token=instrument_token)
            if self.debug:
                print(root_ticker)
            if root_ticker not in underlying_list:
                underlying_list.append(root_ticker)

        return underlying_list

    def get_pnl_for_underlying(self, underlying_ticker):
        pnl = 0
        total_positions = self.ka.kite.positions()
        net_positions_list = total_positions['net']

        for position in net_positions_list:
            position_ticker = self.get_root_ticker_for_instrument_token(instrument_token=position['instrument_token'])
            if underlying_ticker == position_ticker:
                pnl += position['unrealised']
                if self.debug:
                    print(position['tradingsymbol'], position['unrealised'])
        return np.round(pnl, decimals=2)

    def save_master_instruments_list(self, path):
        """
        Downloads the latest Master Instrument List in the specified path
        :param path: Path to store the MasterInstruments.csv File
        :return: None
        """
        file_name = 'MasterInstruments.csv'
        temp_path = os.getcwd()
        os.chdir(path=path)
        self.master_instruments_df.to_csv(file_name)
        os.chdir(temp_path)

    def get_oi_value(self, ticker, expiry_date, strike, call_or_put, end_date):
        if self.debug:
            print('\nIn get_oi_value function\n')
        
        if self.debug:
            print("Fetching the trading symbol for \nticker #{0} \nexpiry # {1} \nstrike # {2} \ninstrument Type # {3}".format(ticker, expiry_date, strike, call_or_put))
            print(type(strike))
        start_date=self.current_date - dt.timedelta(days=7)
        try:
            trading_symbol = self.master_instruments_df[
                                        (self.master_instruments_df['name']                 == ticker) &
                                        (self.master_instruments_df['expiry']               == expiry_date) &
                                        (self.master_instruments_df['strike']               == strike)
                                        & (self.master_instruments_df['instrument_type']    == call_or_put)
                            ]['tradingsymbol'].iloc[-1]

            try:
                oi_df = self.get_price_history( ticker=trading_symbol,
                                                start_date=start_date,
                                                end_date=end_date,
                                                oi=1)

                if oi_df.empty:
                    return 0
                else:
                    return oi_df['oi'].iloc[-1]

            except Exception as e:
                print("Encountered error when fetching price history for \nticker # {0}\nStart Date # {1}\nEnd Date # {2}".format(ticker, start_date, end_date))
        except Exception as e:
            print("Encountered error while Fetching the trading symbol for \nticker #{0} \nexpiry # {1} \nstrike # {2} \ninstrument Type # {3}".format(ticker, expiry_date, strike, call_or_put))
            print("Exception is # ", e)
            return 0


    def get_strike_prices(self, ticker, expiry_date):
        ticker = ticker.upper()
        if self.debug:
            print('Fetching Strike Prices for ticker # ', ticker)

        self.strikes_df = self.master_instruments_df[
            (self.master_instruments_df['name'] == ticker) &
            (self.master_instruments_df['expiry'] == expiry_date) &
            (self.master_instruments_df['strike'] > 0)
            ]

        strike_list = self.strikes_df['strike'].to_list()
        strike_list = list(dict.fromkeys(strike_list))
        strike_list.sort()
        if self.debug:
            print('\nStrike List for ticker # ', ticker)
            print(strike_list)
        return strike_list

    def get_instrument_token(self, ticker):
        if self.debug:
            print('In get_instrument_token method')
        ticker = ticker.upper()
        if self.debug:
            print('Fetching instrument token for ticker #', ticker)
        self.ticker_df = self.master_instruments_df[(self.master_instruments_df['tradingsymbol'] == ticker) &
                                                    #  ((self.master_instruments_df['instrument_type'] == 'EQ') | (self.master_instruments_df['instrument_type'] == 'FUT')) &
                                                    ((self.master_instruments_df['exchange'] == 'NSE') | (
                                                            self.master_instruments_df['exchange'] == 'NFO'))]

        if self.debug:
            print('Ticker list from Master Instruments')
            print(self.ticker_df)

        try:
            self.instrument_token = int(self.ticker_df['instrument_token'].values)
        except Exception as e:
            print('Problem fetching token for ticker {0} # {1}'.format(ticker, e))
            print('Unusual Abort', e)
            sys.exit()
        return self.instrument_token

    def get_instrument_token_mcx(self, ticker):
        ticker = ticker.upper()
        if self.debug:
            print('Fetching instrument token for ticker in mcx #', ticker)
        self.ticker_df = self.master_instruments_df[(self.master_instruments_df['tradingsymbol'] == ticker)
                                                    & (self.master_instruments_df['exchange'] == 'MCX')]

        if self.debug:
            print('Ticker list from Master Instruments')
            print(self.ticker_df)

        self.instrument_token = int(self.ticker_df['instrument_token'].values)

        return self.instrument_token

    def get_ltp(self, ticker):
        if ticker.upper() == "NIFTY":
            ticker = "NIFTY 50"
        elif ticker.upper() == "BANKNIFTY":
            ticker = "NIFTY BANK"
        elif ticker.upper() == "FINNIFTY":
            ticker = "NIFTY FIN SERVICE"
        else:
            ticker = ticker.upper()
        if self.debug:
            print('Fetching Last Traded Price for {0}'.format(ticker))

        self.instrument_token = self.get_instrument_token(ticker)

        ltp = self.ka.kite.ltp(self.instrument_token)[str(self.instrument_token)]['last_price']

        return ltp

    def get_ltp_mcx(self, ticker):

        if self.debug:
            print('Fetching Last Traded Price for {0}'.format(ticker))

        self.instrument_token = self.get_instrument_token_mcx(ticker)

        ltp = self.ka.kite.ltp(self.instrument_token)[str(self.instrument_token)]['last_price']

        return ltp

    def get_price_history(self, ticker, start_date, end_date, interval=None, oi=None, continuous=None):
        if interval is None:
            interval = 'day'

        if oi is None:
            oi = False
        
        if continuous is None:
            continuous = False

        self.instrument_token = self.get_instrument_token(ticker)

        if self.debug:
            print('Instrument token for ticker {0} is {1}'.format(ticker, self.instrument_token))

        self.history_list = self.ka.kite.historical_data(instrument_token=self.instrument_token,
                                                         from_date=start_date,
                                                         to_date=end_date,
                                                         interval=interval,
                                                         oi=oi,
                                                         continuous=continuous)

        self.history_df = pd.DataFrame(self.history_list)
        if self.debug:
            print('\nHistorical data for ticker {0} between {1} and {2}'.format(ticker, start_date, end_date))
            print(self.history_df)
        if not self.history_df.empty:
            self.history_df.set_index(keys='date', inplace=True)
        return self.history_df

    def get_price_history_mcx(self, ticker, start_date, end_date, interval=None, oi=None, continuous=None):
        if interval is None:
            interval = 'day'

        if oi is None:
            oi = False
        
        if continuous is None:
            continuous = False
        self.instrument_token = self.get_instrument_token_mcx(ticker)

        if self.debug:
            print(self.instrument_token)

        self.history_list = self.ka.kite.historical_data(instrument_token=self.instrument_token,
                                                         from_date=start_date,
                                                         to_date=end_date,
                                                         interval=interval,
                                                         oi=oi,
                                                         continuous=continuous)

        self.history_df = pd.DataFrame(self.history_list)
        if self.debug:
            print(self.history_df)
        if not self.history_df.empty:
            self.history_df.set_index(keys='date', inplace=True)
        return self.history_df

    def get_nse_stocklist(self):
        self.nse_stocks_df = self.master_instruments_df[
            (self.master_instruments_df['instrument_type'] == 'EQ') &
            (self.master_instruments_df['segment'] == 'NSE') &
            (self.master_instruments_df['exchange'] == 'NSE') &
            (self.master_instruments_df['name'] > '')
            ]
        if self.debug:
            print('\nStocks filtered from Master Instrument List url\n')
            print(self.nse_stocks_df)

        self.nse_stocks_list = self.nse_stocks_df['tradingsymbol'].to_list()
        # print(self.nse_stocks_list)
        return self.nse_stocks_list

    def get_master_instruments(self):
        return self.master_instruments_df

    def get_positions(self, positions_type=None):

        if positions_type is None:
            positions_type = 'net'
        else:
            positions_type = 'day'

        positions = self.ka.kite.positions()
        positions_df = pd.DataFrame(positions[positions_type])

        return positions_df

    def get_fno_stock_list(self):
        filter_fno = (
                (self.master_instruments_df['instrument_type'] == 'FUT')
                & (self.master_instruments_df['exchange'] == 'NFO')
                & (self.master_instruments_df['segment'] == 'NFO-FUT')
                & (self.master_instruments_df['name'] != 'BANKNIFTY')
                & (self.master_instruments_df['name'] != 'NIFTY')
                & (self.master_instruments_df['name'] != 'FINNIFTY')
                

        )
        self.fno_stocks_df = self.master_instruments_df[filter_fno]

        if self.debug:
            print('\nStocks filtered from Master Instrument List url\n')
            print(self.fno_stocks_df)

        self.fno_stock_list = self.fno_stocks_df['name'].to_list()
        self.fno_stock_list = list(dict.fromkeys(self.fno_stock_list))

        return self.fno_stock_list

    def get_last_traded_dates(self,ticker = 'NIFTY 50'):
        # ticker = 'NIFTY 50' if ticker.upper() == 'NIFTY' else ticker
        today_date = dt.datetime.now().date()
        start_date = today_date - dt.timedelta(days=7)
        end_date = today_date
        
        nifty_df = self.get_price_history(ticker=ticker,
                                        start_date=start_date, 
                                        end_date=end_date)

        last_traded_dates = dict()
        last_traded_dates['last_traded_date'] = nifty_df.index[-1].to_pydatetime().date()
        last_traded_dates['last_traded_date-1'] = nifty_df.index[-2].to_pydatetime().date()
        
        return last_traded_dates

    # Should add last traded date comparision ...
    def get_gainers_losers_close_df(self, gnlr_type, expiry_date=None,from_date=None,to_date=None):
        #**********************************************************************************************************
        #**********************************************************************************************************
        if (from_date is None) and (to_date is None):
            stock_df = None
            if gnlr_type == "STOCKS":
                stock_df = (
                    self.master_instruments_df[
                        self.master_instruments_df["segment"] == "NFO-FUT"
                    ]
                    .groupby("name")
                    .first()
                    .reset_index()
                )

                stock_df["exchange_tradingsymbol"] = stock_df.apply(
                    lambda x: "NSE:" + x["name"], axis=1
                )

            elif gnlr_type == "INDICES":
                stock_df = (
                    self.master_instruments_df[
                        (self.master_instruments_df["segment"] == "INDICES")
                        & (self.master_instruments_df["exchange"] == "NSE")
                        & ~(self.master_instruments_df["name"] == "NIFTY50 DIV POINT")
                    ]
                    .groupby("name")
                    .first()
                    .reset_index()
                )

                stock_df["exchange_tradingsymbol"] = stock_df.apply(
                    lambda x: "NSE:" + x["name"], axis=1
                )

            elif  gnlr_type == "FUTURES":
                stock_df = self.master_instruments_df[
                    (self.master_instruments_df["segment"] == "NFO-FUT")
                    & (self.master_instruments_df["expiry"] == expiry_date)
                    & ~(
                        self.master_instruments_df["name"].isin(
                            ["NIFTY", "BANKNIFTY", "FINNIFTY"]
                        )
                    )
                ]
                
                stock_df = pd.concat(
                    [
                        stock_df,
                        stock_df.loc[:, "tradingsymbol"].apply(lambda x: "NFO:" + x),
                    ],
                    axis=1,
                )
                stock_df.columns.values[-1] = "exchange_tradingsymbol"

            res_df = (
                pd.DataFrame(self.kite.quote(stock_df["exchange_tradingsymbol"].tolist()))
                .transpose()
                .apply(
                    lambda x: [
                        x["last_price"],
                        x["ohlc"]["close"],
                        x["last_price"] - x["ohlc"]["close"],
                        ((x["last_price"] - x["ohlc"]["close"]) / x["ohlc"]["close"]) * 100,
                    ]
                    if x["ohlc"]["close"] != 0
                    else [x["last_price"], x["ohlc"]["close"], None, None],
                    axis=1,
                )
            )

            res_df = pd.DataFrame(
                res_df.to_list(),
                index=res_df.index.to_series().apply(lambda x: x.split(":")[1]).tolist(),
                columns=["prev_close", "curr_close", "diff", "percent_diff"],
            )

            res_df.dropna(inplace=True)
            res_df.sort_values(by="percent_diff", ascending=False, inplace=True)
            res_df = res_df.round(2)
            
            return res_df

        #**********************************************************************************************************
        #**********************************************************************************************************

        elif (from_date is not None) and (to_date is not None):
            
            if to_date == date.today():
                if gnlr_type == "STOCKS":
                    res_df = self.ka.pg.get_postgres_data_df_with_condition(
                                table_name="stocks_fno_day",
                                where_condition="where CAST(date AS DATE) = '{}' ".format(
                                    from_date
                                ),
                            )
                    
                    res_df.index = res_df.apply(lambda x: "NSE:" + x["ticker"], axis=1)
                    
                    res_df = pd.concat(
                        [
                            res_df,
                            pd.DataFrame(
                                self.kite.quote(res_df.index.tolist())
                            ).transpose(),
                        ],
                        axis=1,
                    ).apply(
                        lambda x: [
                        x['close'],
                        x['last_price'],
                        x['last_price']-x['close'],
                        (x["last_price"]-x["close"]) / x["close"] * 100]
                        if x["close"] != 0
                        else [x["close"], x["last_price"], None, None],
                        axis=1,
                    )
                    
                    res_df = pd.DataFrame(
                        res_df.to_list(),
                        index=res_df.index.to_series().apply(lambda x: x.split(":")[1]).tolist(),
                        columns=["prev_close", "curr_close", "diff", "percent_diff"],
                    )
                    
                    res_df.dropna(inplace=True)
                    res_df.sort_values(by="percent_diff", ascending=False, inplace=True)
                    res_df = res_df.round(2)
                    
                    return res_df

                elif gnlr_type == "INDICES":
                    res_df = self.ka.pg.get_postgres_data_df_with_condition(
                                table_name="index_fno_day",
                                where_condition="where CAST(date AS DATE) = '{}' ".format(
                                    from_date
                                ),
                            )
                
                    res_df.index = res_df.apply(lambda x: "NSE:" + x["ticker"], axis=1)
                    
                    res_df = pd.concat(
                        [
                            res_df,
                            pd.DataFrame(
                                self.kite.quote(res_df.index.tolist())
                            ).transpose(),
                        ],
                        axis=1,
                    ).apply(
                        lambda x: [
                        x['close'],
                        x['last_price'],
                        x['last_price']-x['close'],
                        (x["last_price"]-x["close"]) / x["close"] * 100]
                        if x["close"] != 0
                        else [x["close"], x["last_price"], None, None],
                        axis=1,
                    )
                    
                    res_df = pd.DataFrame(
                        res_df.to_list(),
                        index=res_df.index.to_series().apply(lambda x: x.split(":")[1]).tolist(),
                        columns=["prev_close", "curr_close", "diff", "percent_diff"],
                    )
                    
                    res_df.dropna(inplace=True)
                    res_df.sort_values(by="percent_diff", ascending=False, inplace=True)
                    res_df = res_df.round(2)
                    
                    return res_df

                elif gnlr_type == "FUTURES": 
                    res_df = self.ka.pg.get_postgres_data_df_with_condition(
                                table_name="stock_futures_history_day",
                                where_condition="where CAST(date AS DATE) = '{}' ".format(
                                    from_date
                                )+
                                "and CAST(expiry_date as DATE) = '{}'".format(
                                    expiry_date
                                ),
                            )
                    
                    res_df.index = res_df.apply(lambda x: "NFO:" + x["ticker"], axis=1)
                    
                    res_df = pd.concat(
                        [
                            res_df,
                            pd.DataFrame(
                                self.kite.quote(res_df.index.tolist())
                            ).transpose(),
                        ],
                        axis=1,
                    ).apply(
                        lambda x: [
                        x['close'],
                        x['last_price'],
                        x['last_price']-x['close'],
                        (x["last_price"]-x["close"]) / x["close"] * 100]
                        if x["close"] != 0
                        else [x["close"], x["last_price"], None, None],
                        axis=1,
                    )
                    
                    res_df = pd.DataFrame(
                        res_df.to_list(),
                        index=res_df.index.to_series().apply(lambda x: x.split(":")[1]).tolist(),
                        columns=["prev_close", "curr_close", "diff", "percent_diff"],
                    )
                    
                    res_df.dropna(inplace=True)
                    res_df.sort_values(by="percent_diff", ascending=False, inplace=True)
                    res_df = res_df.round(2)
                    
                    return res_df
            else:

                if gnlr_type == "STOCKS":
                    res_df = self.ka.pg.get_postgres_data_df_with_condition(
                                table_name="stocks_fno_day",
                                where_condition="where CAST(date AS DATE) = '{}' ".format(
                                    from_date
                                ),
                            )
                    
                    res_df.columns.values[6] = "prev_close"
                    res_indx = res_df['ticker']
                    
                    res_df = pd.concat(
                    [
                        res_df,
                        self.ka.pg.get_postgres_data_df_with_condition(
                            table_name="stocks_fno_day",
                            where_condition="where CAST(date AS DATE) = '{}' ".format(
                                to_date
                            ),
                        ),
                    ],
                    axis=1,
                    ).apply(
                        lambda x: [
                        x['prev_close'],
                        x['close'],
                        x['close']-x['prev_close'],
                        (x["close"] - x["prev_close"]) / x["prev_close"] * 100]
                        if x["prev_close"] != 0
                        else [x["prev_close"], x["close"], None, None],
                        axis=1,
                    )
                    
                    res_df = pd.DataFrame(
                        res_df.to_list(),
                        index=res_indx,
                        columns=["prev_close", "curr_close", "diff", "percent_diff"],
                    )
                    
                    res_df.dropna(inplace=True)
                    res_df.sort_values(by="percent_diff", ascending=False, inplace=True)
                    res_df = res_df.round(2)
                    
                    return res_df

                elif gnlr_type == "INDICES":
                    res_df = self.ka.pg.get_postgres_data_df_with_condition(
                                table_name="index_fno_day",
                                where_condition="where CAST(date AS DATE) = '{}' ".format(
                                    from_date
                                ),
                            )
                    
                    res_df.columns.values[6] = "prev_close"
                    res_indx = res_df['ticker']
                    
                    res_df = pd.concat(
                    [
                        res_df,
                        self.ka.pg.get_postgres_data_df_with_condition(
                            table_name="index_fno_day",
                            where_condition="where CAST(date AS DATE) = '{}' ".format(
                                to_date
                            ),
                        ),
                    ],
                    axis=1,
                    ).apply(
                        lambda x: [
                        x['prev_close'],
                        x['close'],
                        x['close']-x['prev_close'],
                        (x["close"] - x["prev_close"]) / x["prev_close"] * 100]
                        if x["prev_close"] != 0
                        else [x["prev_close"], x["close"], None, None],
                        axis=1,
                    )
                    
                    res_df = pd.DataFrame(
                        res_df.to_list(),
                        index=res_indx,
                        columns=["prev_close", "curr_close", "diff", "percent_diff"],
                    )
                    
                    res_df.dropna(inplace=True)
                    res_df.sort_values(by="percent_diff", ascending=False, inplace=True)
                    res_df = res_df.round(2)
                    
                    return res_df

                elif gnlr_type == "FUTURES": # 7.32 secs number -> 5
                    res_df = self.ka.pg.get_postgres_data_df_with_condition(
                                table_name="stock_futures_history_day",
                                where_condition="where CAST(date AS DATE) = '{}' ".format(
                                    from_date
                                )+
                                "and CAST(expiry_date as DATE) = '{}'".format(
                                    expiry_date
                                ),
                            )
                    
                    res_df.columns.values[6] = "prev_close"
                    res_indx = res_df['ticker']
                    
                    res_df = pd.concat(
                    [
                        res_df,
                        self.ka.pg.get_postgres_data_df_with_condition(
                            table_name="stock_futures_history_day",
                            where_condition="where CAST(date AS DATE) = '{}' ".format(
                                to_date
                            )+
                            "and CAST(expiry_date as DATE) = '{}'".format(
                                expiry_date
                            ),
                        ),
                    ],
                    axis=1,
                    ).apply(
                        lambda x: [
                        x['prev_close'],
                        x['close'],
                        x['close']-x['prev_close'],
                        (x["close"] - x["prev_close"]) / x["prev_close"] * 100]
                        if x["prev_close"] != 0
                        else [x["prev_close"], x["close"], None, None],
                        axis=1,
                    )
                    
                    res_df = pd.DataFrame(
                        res_df.to_list(),
                        index=res_indx,
                        columns=["prev_close", "curr_close", "diff", "percent_diff"],
                    )
                    
                    res_df.dropna(inplace=True)
                    res_df.sort_values(by="percent_diff", ascending=False, inplace=True)
                    res_df = res_df.round(2)
                    
                    return res_df


        elif from_date is not None:
            if gnlr_type == "STOCKS":
                res_df = self.ka.pg.get_postgres_data_df_with_condition(
                            table_name="stocks_fno_day",
                            where_condition="where CAST(date AS DATE) = '{}' ".format(
                                from_date
                            ),
                        )
                
                res_df.index = res_df.apply(lambda x: "NSE:" + x["ticker"], axis=1)
                
                res_df = pd.concat(
                    [
                        res_df,
                        pd.DataFrame(
                            self.kite.quote(res_df.index.tolist())
                        ).transpose(),
                    ],
                    axis=1,
                ).apply(
                    lambda x: [
                        x['close'],
                        x['last_price'],
                        x['last_price']-x['close'],
                        (x["last_price"]-x["close"]) / x["close"] * 100]
                    if x["close"] != 0
                    else [x["close"], x["last_price"], None, None],
                    axis=1,
                )
                
                res_df = pd.DataFrame(
                    res_df.to_list(),
                    index=res_df.index.to_series().apply(lambda x: x.split(":")[1]).tolist(),
                    columns=["prev_close", "curr_close", "diff", "percent_diff"],
                )
                
                res_df.dropna(inplace=True)
                res_df.sort_values(by="percent_diff", ascending=False, inplace=True)
                res_df = res_df.round(2)
                
                return res_df

            elif gnlr_type == "INDICES":
                res_df = self.ka.pg.get_postgres_data_df_with_condition(
                            table_name="index_fno_day",
                            where_condition="where CAST(date AS DATE) = '{}' ".format(
                                from_date
                            ),
                        )
                
                res_df.index = res_df.apply(lambda x: "NSE:" + x["ticker"], axis=1)
                
                res_df = pd.concat(
                    [
                        res_df,
                        pd.DataFrame(
                            self.kite.quote(res_df.index.tolist())
                        ).transpose(),
                    ],
                    axis=1,
                ).apply(
                    lambda x: [
                        x['close'],
                        x['last_price'],
                        x['last_price']-x['close'],
                        (x["last_price"]-x["close"]) / x["close"] * 100]
                    if x["close"] != 0
                    else [x["close"], x["last_price"], None, None],
                    axis=1,
                )
                
                res_df = pd.DataFrame(
                    res_df.to_list(),
                    index=res_df.index.to_series().apply(lambda x: x.split(":")[1]).tolist(),
                    columns=["prev_close", "curr_close", "diff", "percent_diff"],
                )
                
                res_df.dropna(inplace=True)
                res_df.sort_values(by="percent_diff", ascending=False, inplace=True)
                res_df = res_df.round(2)
                
                return res_df

            elif gnlr_type == "FUTURES": 
                res_df = self.ka.pg.get_postgres_data_df_with_condition(
                            table_name="stock_futures_history_day",
                            where_condition="where CAST(date AS DATE) = '{}' ".format(
                                from_date
                            )+
                            "and CAST(expiry_date as DATE) = '{}'".format(
                                expiry_date
                            ),
                        )
                
                res_df.index = res_df.apply(lambda x: "NFO:" + x["ticker"], axis=1)
                
                res_df = pd.concat(
                    [
                        res_df,
                        pd.DataFrame(
                            self.kite.quote(res_df.index.tolist())
                        ).transpose(),
                    ],
                    axis=1,
                ).apply(
                    lambda x: [
                        x['close'],
                        x['last_price'],
                        x['last_price']-x['close'],
                        (x["last_price"]-x["close"]) / x["close"] * 100]
                    if x["close"] != 0
                    else [x["close"], x["last_price"], None, None],
                    axis=1,
                )
                
                res_df = pd.DataFrame(
                    res_df.to_list(),
                    index=res_df.index.to_series().apply(lambda x: x.split(":")[1]).tolist(),
                    columns=["prev_close", "curr_close", "diff", "percent_diff"],
                )
                
                res_df.dropna(inplace=True)
                res_df.sort_values(by="percent_diff", ascending=False, inplace=True)
                res_df = res_df.round(2)
                
                return res_df

        #**********************************************************************************************************
        #**********************************************************************************************************


        

class Charting:
    def __init__(self):
        self.filename = ''
        self.image = io.BytesIO()

    def plotly_goscatter_chart_with_secondary(self, df, title=None, xlabel=None, ylabel=None, secondary_plot=None):

        fig = go.Figure()
        for column in df.columns:
            if column != secondary_plot:

                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode='lines',
                    name=column,
                    yaxis='y1',
                    customdata=[column],
                    hovertemplate='OI: %{y} <br>Time: %{x}'
                )
                )
            else:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode='markers+lines',
                    line=go.scatter.Line(color="black"),
                    name=column,
                    yaxis='y2',
                    hovertemplate='Price: %{y} <br> Time: %{x}'
                )
                )

        fig.update_layout(yaxis2=dict(
            #title=column,
            anchor='x',
            overlaying='y',
            side='right'
        ))

        fig.update_layout(
            xaxis_title=xlabel,
            yaxis_title=ylabel,
            legend_title='Legend',
            font=dict(
                color="Black"
            )
            # ,plot_bgcolor='White'
        )
        fig.update_layout(title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'}
        )

        # fig.update_layout(hovermode="x")
        fig.update_xaxes(showspikes=True)
        fig.update_yaxes(showspikes=True)
        fig.update_xaxes(showline=True, linewidth=2, linecolor='black', mirror=True)
        fig.update_yaxes(showline=True, linewidth=2, linecolor='black', mirror=True)

        fig.update_layout(height=500, paper_bgcolor='white', plot_bgcolor='white')

        # Return Figure to the main module
        return fig

    def plotly_line_chart(self, df, title=None, xlabel=None, ylabel=None, secondary_plot=None):

        fig = px.line(df, x=df.index, y=df.columns)

        fig.update_layout(
            xaxis_title=xlabel,
            yaxis_title=ylabel,
            legend_title='Legend',
            font=dict(
                color="Blue"
            )
        )

        fig.update_layout(title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'}
        )
        return fig

    def get_line_chart_png(self, df, suptitle=None, title=None, xlabel=None, ylabel=None, imagetype=None):
        if imagetype is None:
            imagetype = 'png'
        else:
            imagetype = imagetype

        fig = Figure(figsize=(18, 10))
        axis = fig.add_subplot(111)
        fig.subplots_adjust(top=0.85)

        if suptitle is not None:
            fig.suptitle(suptitle, fontsize=20, fontweight='bold')

        for col in df.columns:
            axis.plot(df.index, df[col], label=col)
        axis.legend(loc='upper left', frameon=False)

        if xlabel is not None:
            axis.set(xlabel=xlabel)
        if ylabel is not None:
            axis.set(ylabel=ylabel)
        if title is not None:
            axis.set(title=title)

        fig.savefig(self.image)
        self.image.seek(0)
        mimetype = 'image/' + imagetype
        return send_file(self.image, mimetype=mimetype)


class OIAnalysis:
    def __init__(self):
        self.ticker_list = list()
        self.ticker_dict = dict()
        self.strike_list_final = list()
        self.strike_list = list()
        self.master_instruments_df = pd.DataFrame()
        self.final_df_with_oi = pd.DataFrame()

        self.ticker_name = ''
        self.base_ticker = ''
        self.debug = False
        self.intraday = True
        self.kf = KiteFunctions()
        self.ticker = ''
        self.start_date = dt.date(2020, 1, 1)
        self.end_date = dt.date(2020, 1, 1)
        self.expiry_date = dt.date(2020, 1, 1)

        self.interval = self.kf.interval_5minute
        self.oi_img = io.BytesIO()

    def get_multistrike_oi_df(self, ticker, strike_list, start_date, end_date, expiry_date, intraday=True):
        if self.debug:
            print('Intraday inside the class is # ', intraday)
        # ****************Input Parameters****************#
        self.ticker_name = ticker.upper()
        self.strike_list = strike_list
        self.start_date = start_date
        self.end_date = end_date
        self.expiry_date = expiry_date
        # ****************Input Parameters****************#

        # Change the ticker according to
        if self.ticker_name.upper() == 'NIFTY':
            self.base_ticker = 'NIFTY 50'
        elif self.ticker_name.upper() == 'BANKNIFTY':
            self.base_ticker = 'NIFTY BANK'
        elif self.ticker_name.upper() == "FINNIFTY":
            self.base_ticker = "NIFTY FIN SERVICE"
        else:
            self.base_ticker = self.ticker_name.upper()

        print("Intraday indicator # ", intraday)
        # if intraday is not None:
        #     self.intraday = False
        #     self.interval = self.kf.interval_day

        if intraday is False:
            self.interval = self.kf.interval_day

        self.master_instruments_df = self.kf.get_master_instruments()

        if self.debug:
            print('Passed strike list # ', self.strike_list)

        # for strike in strike_list:
        for strike in self.strike_list:

            if strike.isnumeric():
                ce_strike_str = str(strike) + 'CE'
                pe_strike_str = str(strike) + 'PE'
                self.strike_list_final.append(ce_strike_str)
                self.strike_list_final.append(pe_strike_str)
            else:
                self.strike_list_final.append(strike.upper())

        if self.debug:
            print("Final strike list after modification # ", self.strike_list_final)

        for strike in self.strike_list_final:

            strike_int = int(''.join(filter(str.isdigit, strike)))
            strike_str = ''.join(filter(str.isalpha, strike))

            if self.debug:
                print('Processing strike # ', strike)
                print('Ticker # {0} Expiry # {1}, Strike # {2}, Instrument Type # {3}'.
                format(self.ticker_name, self.expiry_date, strike_int, strike_str))
            df = self.master_instruments_df[
                (self.master_instruments_df['name'] == self.ticker_name)
                & (self.master_instruments_df['expiry'] == self.expiry_date)
                & (self.master_instruments_df['strike'] == strike_int)
                & (self.master_instruments_df['instrument_type'] == strike_str)
                ]

            if self.debug:
                print('Instrument for Strike {0}\n'.format(strike_int))
                print(df)
            if not df.empty:
                self.ticker_dict[strike] = df['tradingsymbol'].iloc[0]
            else:
                print('Instrument name not fetched from Master Instruments for strike # ', strike)
                return self.final_df_with_oi

        if self.debug:
            print('Final Ticker Df # ')
            print(self.ticker_list)
            print('Final Ticker Dict # ')
            print(self.ticker_dict)

        for ticker_key in self.ticker_dict:
            ticker_value = self.ticker_dict[ticker_key]

            # for ticker in self.ticker_list:

            df = self.kf.get_price_history(
                ticker=ticker_value,
                start_date=self.start_date,
                end_date=self.end_date,
                interval=self.interval,
                oi=True
            )

            if df.empty:
                print('Not fetched for # ', ticker_value)
            else:
                df.drop(columns=['open', 'high', 'low', 'close', 'volume'], inplace=True)
                df.rename(columns={'oi': ticker_key}, inplace=True)

                if self.final_df_with_oi.empty:
                    self.final_df_with_oi = df.copy()
                else:
                    self.final_df_with_oi = pd.concat([df, self.final_df_with_oi], axis=1, join='inner')

        ticker_df = self.kf.get_price_history(ticker=self.base_ticker,
                                              start_date=self.start_date,
                                              end_date=self.end_date,
                                              interval=self.interval)
        if not ticker_df.empty:
            ticker_df.drop(columns=['open', 'high', 'low', 'volume'], inplace=True)
            ticker_df.rename(columns={'close': self.ticker_name}, inplace=True)
        else:
            print('Data for Base ticker is not fetched...')

        self.final_df_with_oi = pd.concat([self.final_df_with_oi, ticker_df], axis=1, join='inner')
        if self.debug:
            print('Here is final Dataframe with OpenInterest and Underlying Price.')
            print(self.final_df_with_oi)
        return self.final_df_with_oi

    def get_maxpain(self, ticker, expiry_date):

        print('\nMax pain calculation started at # {0} for ticker {1} and expiry {2}'.format(dt.datetime.now(), ticker, expiry_date))

        if self.debug:
            print('\nIn get_maxpain Routine\n')

        maxpain_df_columns = ['strike', 'calloi', 'putoi']
        maxpain_df = pd.DataFrame(columns=maxpain_df_columns)
        maxpain_df.set_index(keys='strike', inplace=True)
        
        last_traded_date = self.kf.get_last_traded_dates()['last_traded_date']
        today_date = dt.datetime.now().date()
        
        if last_traded_date == today_date:
            maxpain_df = self.get_oi_df_today(ticker=ticker, expiry_date=expiry_date) 
        else:
            maxpain_df = self.get_oi_df_anyday( ticker=ticker,
                                                expiry_date=expiry_date,
                                                date=last_traded_date)
        
        if self.debug:
            print("OpenInterest  DF here ...")
            print(maxpain_df)
        maxpain_df['cum_call'] = 0
        maxpain_df['cum_put'] = 0
        maxpain_df['total_value'] = 0

        for strike in maxpain_df.index:
            if self.debug:
                print('Calculating for strike # ', strike)
            call_value = 0
            put_value = 0
            for inner_strike in maxpain_df.index:
                if strike > inner_strike:
                    call_value += (strike - inner_strike) * maxpain_df['calloi'][inner_strike]
                else:
                    put_value += (inner_strike - strike) * maxpain_df['putoi'][inner_strike]
            maxpain_df['cum_call'][strike] = call_value
            maxpain_df['cum_put'][strike] = put_value

        maxpain_df['total_value'] = maxpain_df['cum_call'] + maxpain_df['cum_put']

        if self.debug:
            print('\nMax pain DataFrame:')
            print(maxpain_df)

        maxpain_df['total_value'] = pd.to_numeric(maxpain_df['total_value'], errors='coerce').fillna(0,
                                                                                                     downcast='infer')
        maxpain_value = maxpain_df[['total_value']].idxmin().iloc[-1]
        if self.debug:
            print('Maxpain # ', maxpain_value)

        return maxpain_df

    def get_multistrike_oichange_df(self, ticker, strike_list, start_date, end_date, expiry_date, intraday=True):
        if self.debug:
            print('Intraday inside the class is # ', intraday)
        # ****************Input Parameters****************#
        self.ticker_name = ticker.upper()
        self.strike_list = strike_list
        self.start_date = start_date
        self.end_date = end_date
        self.expiry_date = expiry_date
        # ****************Input Parameters****************#

        # Change the ticker according to
        if self.ticker_name.upper() == 'NIFTY':
            self.base_ticker = 'NIFTY 50'
        elif self.ticker_name.upper() == 'BANKNIFTY':
            self.base_ticker = 'NIFTY BANK'
        elif self.ticker_name.upper() == "FINNIFTY":
            self.base_ticker = "NIFTY FIN SERVICE"
        else:
            self.base_ticker = self.ticker_name.upper()

        print("Intraday indicator # ", intraday)

        if intraday is False:
            self.interval = self.kf.interval_day

        self.master_instruments_df = self.kf.get_master_instruments()

        if self.debug:
            print('Passed strike list # ', self.strike_list)

        # for strike in strike_list:
        for strike in self.strike_list:

            if strike.isnumeric():
                ce_strike_str = str(strike) + 'CE'
                pe_strike_str = str(strike) + 'PE'
                self.strike_list_final.append(ce_strike_str)
                self.strike_list_final.append(pe_strike_str)
            else:
                self.strike_list_final.append(strike.upper())

        if self.debug:
            print("Final strike list after modification # ", self.strike_list_final)

        for strike in self.strike_list_final:

            strike_int = int(''.join(filter(str.isdigit, strike)))
            strike_str = ''.join(filter(str.isalpha, strike))

            if self.debug:
                print('\nProcessing strike # ', strike)
                print('Ticker # {0} Expiry # {1}, Strike # {2}, Instrument Type # {3}'.
                format(self.ticker_name, self.expiry_date, strike_int, strike_str))
            df = self.master_instruments_df[
                (self.master_instruments_df['name'] == self.ticker_name)
                & (self.master_instruments_df['expiry'] == self.expiry_date)
                & (self.master_instruments_df['strike'] == strike_int)
                & (self.master_instruments_df['instrument_type'] == strike_str)
                ]

            if self.debug:
                print('Instrument for Strike {0}'.format(strike_int))
                print(df)
            if not df.empty:
                self.ticker_dict[strike] = df['tradingsymbol'].iloc[0]
            else:
                print('Instrument name not fetched from Master Instruments for strike # ', strike)
                return self.final_df_with_oi

        if self.debug:
            print('\n\nFinal Ticker Dict # ')
            print(self.ticker_dict)

        for ticker_key in self.ticker_dict:
            ticker_value = self.ticker_dict[ticker_key]

            # for ticker in self.ticker_list:

            df = self.kf.get_price_history(
                ticker=ticker_value,
                start_date=self.start_date,
                end_date=self.end_date,
                interval=self.interval,
                oi=True
            )

            if df.empty:
                print('Not fetched for # ', ticker_value)
            else:
                col_name = ticker_key
                df[col_name] = df['oi'] - df['oi'].shift(1)
                df.drop(columns=['open', 'high', 'low', 'close', 'volume', 'oi'], inplace=True)
                # df.rename(columns={'oi': ticker_key}, inplace=True)

                if self.final_df_with_oi.empty:
                    self.final_df_with_oi = df.copy()
                else:
                    self.final_df_with_oi = pd.concat([df, self.final_df_with_oi], axis=1, join='inner')

        ticker_df = self.kf.get_price_history(ticker=self.base_ticker,
                                              start_date=self.start_date,
                                              end_date=self.end_date,
                                              interval=self.interval)
        if not ticker_df.empty:
            ticker_df.drop(columns=['open', 'high', 'low', 'volume'], inplace=True)
            ticker_df.rename(columns={'close': self.ticker_name}, inplace=True)
        else:
            print('Data for Base ticker is not fetched...')

        self.final_df_with_oi = pd.concat([self.final_df_with_oi, ticker_df], axis=1, join='inner')
        if self.debug:
            print('Here is final Dataframe with OpenInterest and Underlying Price.')
            print(self.final_df_with_oi)
        return self.final_df_with_oi
        
    def get_oi_df_anyday(self, ticker, expiry_date, date):
        #############Input Parameters##############
        self.ticker             = ticker.upper()
        self.expiry_date        = expiry_date
        self.date               = date
        #############Input Parameters##############
        db_location             = 'srifintech-database'
        pg = PostgreSQLOperations(db_location=db_location)

        if (self.ticker == 'NIFTY' or 
            self.ticker == 'BANKNIFTY' or 
            self.ticker == 'FINNIFTY'):
            table_name = 'index_option_history_day'
        else:
            table_name = 'stock_option_history_day'
            
        where_condition = "where underlying = '{}' and expiry_date = '{}' and date(date) = '{}'".format(self.ticker, 
                                                                                                        self.expiry_date,
                                                                                                        date)
        query_df = pg.get_postgres_data_df_with_condition(table_name=table_name, where_condition=where_condition)
        query_df.drop(columns=['date', 'ticker', 'open', 'high', 'low', 'close', 'volume', 'last_update'], inplace=True)
        print(query_df)
        
        #Get Unique Strikes in to a List
        strikes = list(OrderedDict.fromkeys(list(query_df['strike'])))
        
        oi_data = []

        for strike in strikes:
            
            put_oi = query_df[(query_df['strike']==strike) & (query_df['instrument_type']=="PE")] # querying as per requirement !
            
            if put_oi.empty:
                if self.debug:
                    print("Empty oi encountered for  # ", strike)
                empty_row = {'strike': strike, 
                             'instrument_type': 'CE', 
                             'expiry_date': expiry_date, 
                             'oi': 0,
                             'underlying' : 'something'}
                put_oi = put_oi.append(empty_row, ignore_index=True)
            
            if self.debug:
                print(put_oi)    
            
            call_oi = query_df[(query_df['strike']==strike) & (query_df['instrument_type']=="CE")]
            if call_oi.empty:
                if self.debug:
                    print("Empty oi encountered for  # ", strike)
                empty_row = {'strike': strike, 
                             'instrument_type': 'CE', 
                             'expiry_date': expiry_date, 
                             'oi': 0,
                             'underlying' : 'something'}
                call_oi = call_oi.append(empty_row, ignore_index=True)
                
            if self.debug:
                print(call_oi)                
            oi_data.append([strike , int(call_oi['oi']) , int(put_oi['oi'])])

        oi_df = pd.DataFrame(oi_data , columns=['strike' , 'calloi' , 'putoi'])
        oi_df.set_index(keys='strike', inplace=True)
        
        return oi_df
        
    def get_oi_df(self, ticker, expiry_date, end_date):

        #############Input Parameters##############
        self.ticker               = ticker.upper()
        self.expiry_date          = expiry_date
        self.end_date             = end_date
        #############Input Parameters##############
        if self.debug:
            print("\nInside get_oi_df method...")
            print(self.ticker)
            print(self.expiry_date)
                    
        # strikes_df = self.kf.master_instruments_df[
        #         (self.kf.master_instruments_df['name']          == self.ticker_name)
        #         & (self.kf.master_instruments_df['expiry']      == self.expiry_date)
        #         & (self.kf.master_instruments_df['segment']     == 'NFO-OPT')
        #         & (self.kf.master_instruments_df['exchange']    == 'NFO')
        #         ]
        
        oi_df_columns = ['strike', 'calloi', 'putoi']
        oi_df = pd.DataFrame(columns=oi_df_columns)
        strike_list = self.kf.get_strike_prices(ticker, expiry_date)
        
        if self.debug:
            print("Strike list for the ticker {0} is here...".format(self.ticker))
            print(strike_list)

        if len(strike_list) == 0:
            print('Strikes are not retrieved for the ticker {0} on  expiry date {1}'.format(ticker, expiry_date))
            return "Error retrieving the strike list  for the ticker!"

        oi_df['strike'] = strike_list
        oi_df.set_index(keys='strike', inplace=True)

        for strike in oi_df.index:
            if self.debug:
                print('Fetching Open Interest for strike # {0} and for date # {1}'.format(strike, end_date))
            call_oi_value = int(self.kf.get_oi_value(ticker=ticker,
                                            expiry_date=expiry_date,
                                            strike=strike,
                                            call_or_put='CE',
                                            end_date=end_date))
            
            put_oi_value = int(self.kf.get_oi_value(ticker=ticker,
                                           expiry_date=expiry_date,
                                           strike=strike,
                                           call_or_put='PE',
                                           end_date=end_date))
            

            oi_df['calloi'][strike] = call_oi_value
            oi_df['putoi'][strike] = put_oi_value
            
        if self.debug:
            print("\n\nOpen Interest DF for strike {0} is here...".format(self.ticker))
            print(oi_df)
        
        
        return oi_df


    def get_oi_df_today(self, ticker, expiry_date):
        self.ticker         = ticker.upper()
        self.expiry_date    = expiry_date
        filter_df = self.kf.master_instruments_df[
            (self.kf.master_instruments_df['name']        == self.ticker)
          & (self.kf.master_instruments_df['expiry']      == self.expiry_date)
          & (self.kf.master_instruments_df['segment']     == 'NFO-OPT')
        ]

        filter_instruments_df = filter_df[['instrument_token', 'strike', 'tradingsymbol', 'instrument_type']].copy()
        filter_instruments_df.reset_index(drop=True, inplace=True)
        filter_instruments_df.sort_values(by=['strike'], inplace=True)
        instruments_list = filter_instruments_df['instrument_token'].to_list()

        if self.debug:
            print("Here are instruments List to fetch OI... ")
            print(instruments_list)

        quote = self.kf.ka.kite.quote(instruments_list)
        oi_df = pd.DataFrame(columns=['strike', 'calloi', 'putoi'])
        oi_df['strike'] = self.kf.get_strike_prices(ticker=ticker, expiry_date=expiry_date)
        oi_df['calloi'] = 0
        oi_df['putoi'] = 0
        oi_df.set_index(keys='strike', inplace=True)

        for index in filter_instruments_df.index:
            
            instrument_token = str(filter_instruments_df['instrument_token'][index])
            strike_price = filter_instruments_df['strike'][index]
            oi_value = quote[instrument_token]['oi']
            if filter_instruments_df['instrument_type'][index] == "CE":
                oi_df['calloi'][strike_price] = oi_value
            else:
                oi_df['putoi'][strike_price] = oi_value

        if self.debug:
            print("\n\nHere is final dataframe...")
            print(oi_df)
        
        return oi_df

class PostgreSQLOperations:
    def __init__(self, db_location=None):
        self.debug = False
        self.config_filename = os.path.join(os.path.dirname(__file__), 'config.ini')
        self.postgres_config_details = {}
        # self.db_location = 'heroku-database'
        if db_location is None:
            self.db_location = 'srifintech-database'
        else:
            self.db_location = db_location
        self.access_details = ''
        self.postgres_user = ''
        self.user = ''
        self.password = ''
        self.host = ''
        self.port = ''
        self.database = ''
        self.config = ConfigParser()
        self.read_postgresql_configuration()
        self.df = pd.DataFrame()

    def read_postgresql_configuration(self):
        self.config.read(self.config_filename)
        if self.debug:
            print('Configuration path# ', self.config_path)
            print('Sections in config # ', self.config.sections())
            print('DB Location # ', self.db_location)
        self.user = self.config[self.db_location]['user']
        self.password = self.config[self.db_location]['password']
        self.host = self.config[self.db_location]['host']
        self.port = self.config[self.db_location]['port']
        self.database = self.config[self.db_location]['database']

    def close_postgres_database(self):
        try:
            conn.close()
            print("Connection close successfully")
        except Exception as e:
            print("Failed to close the connection # ", e)

    def connect_postgres_table(self, table_name):
        conn = None
        if self.debug:
            print('Inside PostgreSQLOperations Class insert_df_postgresql_table method')

        connection_string = 'postgresql://' + \
                            self.user + ':' + \
                            self.password + '@' + \
                            self.host + ':' + \
                            self.port + '/' + \
                            self.database

        try:

            if self.debug:
                print('Trying to insert into table {0}'.format(table_name))
            engine = sqlalchemy.create_engine(connection_string,poolclass=sqlalchemy.pool.NullPool)

            conn = engine.connect()
            print('Connected to database @ ' + self.db_location)

            if self.debug:
                print(engine.table_names())
                
        except Exception as e:
            pass
        
    def insert_df_postgres(self, df, table_name):
        try:
            table_name = table_name
            df.to_sql(table_name,
                      conn,
                      if_exists='append',
                      index=False)
            return True
        
        except Exception as e:
            print("Error insertig in to table # ", e)

    def insert_df_postgresql_table(self, df, table_name):
        conn = None
        if self.debug:
            print('Inside PostgreSQLOperations Class insert_df_postgresql_table method')

        connection_string = 'postgresql://' + \
                            self.user + ':' + \
                            self.password + '@' + \
                            self.host + ':' + \
                            self.port + '/' + \
                            self.database

        try:
            if self.debug:
                print('Trying to insert into table {0}'.format(table_name))
            engine = sqlalchemy.create_engine(connection_string,poolclass=sqlalchemy.pool.NullPool)
            #    'postgresql://postgres:postgres@localhost/postgres'

            conn = engine.connect()
            print('Connected to database @ ' + self.db_location)

            if self.debug:
                print(engine.table_names())

            table_name = table_name
            df.to_sql(table_name,
                      conn,
                      if_exists='append',
                      index=False)

            conn.close()
            return True
            
        except Exception as e:
            print('Encountered exception while inserting data into table {0}'.format(table_name))
            print('Exception # ', e)
            conn.close()
            return False

    def get_postgres_data_df_with_condition(self, table_name, where_condition = ""):
        # global read_conn
        read_conn = None
        result_df = pd.DataFrame()
        logging.debug('Inside PostgreSQLOperations Class get_postgres_data_df method')

        connection_string = 'postgresql://' + \
                            self.user + ':' + \
                            self.password + '@' + \
                            self.host + ':' + \
                            self.port + '/' + \
                            self.database
        try:
            logging.debug('Trying to read from table {0}'.format(table_name))
            engine = sqlalchemy.create_engine(connection_string,
                                poolclass=sqlalchemy.pool.NullPool)
            # breakpoint()
            read_conn = engine.connect()
            logging.info('Connected to database @ ' + self.database)

            logging.debug(engine.table_names())

        except Exception as e:
            logging.debug('Failed to establish the connection', e)
            read_conn.close()
            
            
        query = ('SELECT * FROM ' + table_name + ' ' + where_condition)
        logging.debug('\n\nBelow is the query')
        # logging.debug(pformat(query))
        
            
        try:
            result_df = pd.read_sql(sql=query, con=read_conn)
            logging.debug("after result_df")
            logging.debug('Read success for table # '+ table_name)
            logging.debug(result_df)
            read_conn.close()
        except Exception as e:
            logging.debug('Read failed # ', e)
            read_conn.close()
        return result_df

       
    def delete_rows_postgresql_table(self, table_name, where_condition = None,is_text=False):
        global conn
        if self.debug:
            print('Inside PostgreSQLOperations Class delete_df_postgresql_table method')

        connection_string = 'postgresql://' + \
                            self.user + ':' + \
                            self.password + '@' + \
                            self.host + ':' + \
                            self.port + '/' + \
                            self.database

        try:
            if self.debug:
                print('Trying to upsert into table {0}'.format(table_name))
            engine = sqlalchemy.create_engine(connection_string)
            #    'postgresql://postgres:postgres@localhost/postgres'

            conn = engine.connect()
            print('Connected to database @ ' + self.db_location)

            if self.debug:
                print(engine.table_names())

            meta = MetaData()
            table_name = Table(table_name, meta)
            if where_condition is None:
                del_stmt = table_name.delete()
            else:
                if not is_text:
                    del_stmt = table_name.delete().where(where_condition)
                else:
                    del_stmt = table_name.delete().where(text(where_condition))
            # del_stmt = table_name.delete()
            if self.debug:
                print('Now executing the Delete query # ', del_stmt)
            conn.execute(del_stmt)
            conn.close()
            return True

        except Exception as e:
            print('Encountered exception while deleting data from table {0}'.format(table_name))
            print('Exception # ', e)
            conn.close()
            return False

class MonteCarlo_Simulation:

    def __init__(self):
        self.ticker_raw = ''
        self.ticker = ''
        self.predict_days = 30
        self.history_days = 3600
        self.end_date = ''
        self.start_date = ''
        self.live_price_ind = 'N'
        self.debug = False
        self.data = pd.DataFrame()
        self.mean = 0
        self.std_dev = 0
        self.var = 0
        self.drift = 0
        self.upper_boundary = 0
        self.lower_boundary = 0
        self.chart = False
        self.chartjson = False
        self.simulations = 1000
        self.img = io.BytesIO()
        self.df = pd.DataFrame()
        self.upper_boundary = 0
        self.lower_boundary = 0

    def get_data_yfinance(self):

        self.end_date = dt.datetime.now().date()
        self.start_date = self.end_date - dt.timedelta(days=self.history_days)

        self.data = yf.download(self.ticker, start=self.start_date, end=self.end_date)

        if self.debug:
            print(self.data)

        print('Successfully downloaded {0} data from {1} to {2}...'.format(self.ticker, self.start_date, self.end_date))

        return self.data

    def perform_calculations(self):

        # Step1 : Calculate the Log Returns
        self.df['log_returns'] = np.log(self.df.Close) - np.log(self.df.Close.shift(1))

        # Step2 : Calculate the Mean(Average)
        self.mean = self.df['log_returns'].mean()
        if self.debug:
            print('Mean value is {0}'.format(self.mean))

        # Step3 : Calculate the STD_DEV
        self.std_dev = self.df['log_returns'].std()
        if self.debug:
            print('Standard Deviation value is {0}'.format(self.std_dev))

        # Step 4 : Calculate the Variance
        self.var = self.df['log_returns'].var()
        if self.debug:
            print('Variance value is {0}'.format(self.var))

        # Step 5 : Calculate Drift
        self.drift = (self.mean - (self.var / 2))
        if self.debug:
            print('Drift value is {0}'.format(self.drift))

    def perform_predictions(self):
        suptitle = 'Prediction for ' + self.ticker_raw + ' with ' + \
                   str(self.history_days) + ' days of past returns'
        fig = Figure()
        fig.suptitle(suptitle, fontsize=14, fontweight='bold')

        axis = fig.add_subplot(111)
        # axis = plt.subplots()
        axis.legend(loc='right')

        fig.subplots_adjust(top=0.85)
        # fig.tight_layout(rect=[0, 0.03, 1, 0.95])

        T = self.predict_days

        if self.debug:
            print('Predicting for {0}'.format(T))

        # choose number of runs to simulate - I have chosen 1000
        print('Monte Carlo Simulation in progress for 1000 samples with historic returns of {0} days.....'.format(
            self.history_days))
        
        self.simulations_df = pd.DataFrame()
        for i in range(self.simulations):
            # create list of daily returns using random normal distribution
            self.daily_returns = np.random.normal(self.mean / T, self.std_dev / math.sqrt(T), T) + 1
            # set starting price and create price series generated by above random daily returns
            self.price_list = [self.ltp]

            for x in self.daily_returns:
                self.price_list.append(self.price_list[-1] * x)

            self.simulations_df[i] = self.price_list
            # plot data from each individual run which we will plot at the end
            if self.chart:
                axis.plot(self.price_list)
                
            if max(self.price_list) > self.upper_boundary:
                self.upper_boundary = max(self.price_list)

            if self.lower_boundary == 0:
                self.lower_boundary = min(self.price_list)
            elif min(self.price_list) < self.lower_boundary:
                self.lower_boundary = min(self.price_list)

        self.upper_boundary = int(np.round(self.upper_boundary, 0))
        self.lower_boundary = int(np.round(self.lower_boundary, 0))
        if self.debug:
            print('Upper value is ', self.upper_boundary)
            print('Lower value is ', self.lower_boundary)
        
        if self.debug:
            print("\n\n")
            max_value = self.simulations_df.max().max()
            min_value = self.simulations_df.min().min()
            print("Upper Boundary from Dataframe # ", max_value)
            print("Lower Boundary from Dataframe # ", min_value)
            print(self.simulations_df)
        
        # show the plot of multiple price series created above
        if self.chart:
            title = 'Upper Range: ' + str(self.upper_boundary) + '\n' + 'Lower Range: ' + str(self.lower_boundary)
            xlabel = 'Days of Prediction # ' + str(self.predict_days)
            ylabel = 'Price Range'
            axis.set(xlabel=xlabel,
                     ylabel=ylabel,
                     title=title)

            self.img = io.BytesIO()
            fig.savefig(self.img)
            self.img.seek(0)

    def monte_carlo_prediction(self, ticker, predict_days, history_days, live_price_ind, chart=None,chartjson = None):
        self.chart = chart
        self.ticker = ticker
        self.chartjson = chartjson
        if chart is None:
            self.chart = False
        print('Chart Attribute is # ', self.chart)

        if self.ticker.upper() == 'NIFTY':

            self.ticker = '^NSEI'
            self.ticker_raw = 'NIFTY'
        elif self.ticker.upper() == 'BANKNIFTY':
            self.ticker = '^NSEBANK'
            self.ticker_raw = 'BANKNIFTY'
        else:
            self.ticker_raw = ticker.upper()
            self.ticker = ticker.upper() + '.NS'

        self.predict_days = predict_days
        self.history_days = history_days
        self.df = self.get_data_yfinance()
        self.live_price_ind = live_price_ind

        if self.live_price_ind == 'Y':
            # kf = KiteFunctions()
            # self.ltp = kf.get_ltp(ticker=self.ticker)
            print('Live price fetched for ticker {0} is # {1}'.format(ticker, self.ltp))

        else:
            self.ltp = self.df['Adj Close'][-1]
            last_date = self.df.index[-1].date()
            print('Last prices is {0} for the date {1}'.format(self.ltp, last_date))

        self.perform_calculations()
        self.perform_predictions()
        result_dict = {
            'ticker': self.ticker,
            'history days': self.history_days,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'upper value': self.upper_boundary,
            'lower value': self.lower_boundary,
            'simulations_count': self.simulations
        }
        print('Monte Carlo Data \n')
        print(result_dict)

        if self.chartjson:
            return self.simulations_df
        if self.chart:
            return send_file(self.img, mimetype='image/png')
        else:
            print('returning the dict')
            return result_dict
class Notifications:
    def __init__(self):
        self.debug = False
        self.toaster = ToastNotifier()

        # Telegram Access Details
        self.telegram_file_name = 'telegram_token.txt'
        self.temp_path = r'C:\Users\skoppuravur6\Google Drive\Personal\AlgoTrading\Access Tokens'  # ==> This is the path for Telegram ids.
        self.access_details = []
        self.bot_token = ''
        self.bot_chatID = ''
        self.read_telegram_access_details()
        self.response = requests.Response()

    def send_windows_notification(self, message):
        self.toaster.show_toast(message)

    def read_telegram_access_details(self):
        current_path = os.getcwd()
        os.chdir(path=self.temp_path)
        with open(self.telegram_file_name) as f:
            json_data = json.load(f)

        self.bot_token = json_data['bot_token']
        self.bot_chatID = json_data['bot_chatID']
        os.chdir(path=current_path)

    def send_telegram_notification(self, message):
        send_text = 'https://api.telegram.org/bot' + self.bot_token + '/sendMessage?chat_id=' + self.bot_chatID + '&parse_mode=Markdown&text=' + message

        self.response = requests.get(send_text)

        # print(self.response)
        # return self.response.json()
        return self.response