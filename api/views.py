# import sys
# sys.path.append('.')
from django.shortcuts import render
import logging
from pprint import pformat
import datetime as dt
from datetime import datetime
from pychartjs import BaseChart, ChartType, Color, Options   
from sqlalchemy import create_engine

from api.classes import KiteAuthentication, KiteFunctions, MonteCarlo_Simulation, OIAnalysis, PostgreSQLOperations
from api.chartjs_classes import *
from api.implied_vol import implied_volatility
import pandas as pd

from rest_framework.views import APIView
from rest_framework.response import Response
import json
import math
from pytz import timezone
from django.http import HttpResponse
import numpy as np
import sys


def functions_initializer():
    kf =  KiteFunctions()
    oi =  OIAnalysis()
    po =  PostgreSQLOperations()
    return kf,oi,po

def Home(request):
    return render(request , 'index.html')

class Open_Interst_Chart_API_View(APIView):
    # renderer_classes = [JSONRenderer]
    def post(self , request):
        logging.debug(pformat('\n\nBeginning of OpenInterest api with new quote logic...'))
        ticker = request.data.get('ticker')
        expiry_date_str = request.data.get('expiry_date')
        
        print('\t\t\t' + ticker)
        print('\t\t\t' + expiry_date_str)

        logging.debug(pformat("Data in Post is # "))
        logging.debug(pformat(request.data))

        ##################Input parameters #####################
        # ticker = content['ticker']
        # expiry_date_str = content['expiry_date']
        # intraday_ind = contenct['intraday_ind']
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        display_strikes_count = 15
        # ticker = 'NIFTY'
        # expiry_date = dt.date(2020,12,31)
        
        ##################Input parameters #####################

        kf,oi,po = functions_initializer()

        last_traded_day = kf.get_last_traded_dates()['last_traded_date']
        today_date = dt.datetime.now()
        if today_date == last_traded_day:
            oi_df1 = oi.get_oi_df_today(ticker=ticker,
                                        expiry_date=expiry_date)
        else: 
            oi_df1 = oi.get_oi_df_anyday(ticker=ticker,
                                        expiry_date=expiry_date,
                                        date=last_traded_day)

        logging.debug(pformat('\n\nHere is the Final OpenInterest Dataframe...'))
        logging.debug(pformat(oi_df1))
        ltp = oi.kf.get_ltp(ticker=ticker)
        annotation_label = "Spot Price: " + str(ltp)
        strike_list = oi_df1.index.to_list()
        absolute_difference_function = lambda list_value : abs(list_value - ltp)
        closest_strike = min(strike_list, key=absolute_difference_function)
        logging.debug(pformat("Closest Strike is # ", closest_strike))
        row_num = oi_df1.index.get_loc(closest_strike)
        logging.debug(pformat("Row Num of closest strike # ", row_num))
        oi_df = oi_df1.iloc[row_num - display_strikes_count :  row_num + display_strikes_count]
        logging.debug(pformat(oi_df))
        

        
        ####################### chartjs ########################

        openinterest_newbardata = oichange_newbardata
        openinterest_bargraph = oichange_bargraph

        NewChart = openinterest_bargraph(closest_strike=closest_strike,
            annotation_label=annotation_label)()
        
        NewChart.labels.xaxis_labels    = oi_df.index.to_list()
        NewChart.data.bardata1.data     = oi_df["calloi"].to_list()
        NewChart.data.bardata2.data     = oi_df["putoi"].to_list()

        ChartJSON_str = NewChart.get()


        logging.debug(pformat("\n\nHere is the chartjson..."))
        logging.debug(pformat(ChartJSON_str))

        ####################### chartjs ########################
        
        print(ChartJSON_str)

        ChartJSON_json = json.loads(ChartJSON_str)
      
        return Response(ChartJSON_json)

        # return ChartJSON_str
    
    def get(self , request):
        return Response({"ticker":"NIFTY","expiry_date":"2021-05-27"})
         
class MaxPain_History_Chart_API_View(APIView):
    # renderer_classes = [JSONRenderer]
    def post(self , request):
        ticker = request.data.get('ticker')
        expiry_date_str = request.data.get('expiry_date')
        print('\t\t\t' + ticker)
        print('\t\t\t' + expiry_date_str)

        logging.debug(pformat("Data in Post is # "))
        logging.debug(pformat(request.data))
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        
        connection_string = 'postgresql://doadmin:or5ka898vk8r1wdi@srifintech-db-do-user-8454140-0.b.db.ondigitalocean.com:25060/defaultdb'

        db = create_engine(connection_string)


        today = dt.datetime.now().date()
        from_date = today - dt.timedelta(10)

        print(from_date)

        kf,oi,po = functions_initializer()

        # expiry_date = dt.date(2021,7,29)

        ltd = kf.get_last_traded_dates()['last_traded_date']

        data = list()


        query_op = db.execute("select * from maxpain_history where date(expiry_date)='{}' and  date(date) >='{}' and ticker='{}' order by date desc".format(expiry_date , from_date , ticker)).fetchall()


        def get_data_db():
            data_temp = list()
            for i in range(len(query_op)):
                max_pain_value = query_op[i]['maxpain_value']
                spot_price = query_op[i]['spot_price']
                data_temp.append([query_op[i]['date'] , max_pain_value , spot_price])
            return data_temp


        if ltd == query_op[0]['date']:
            data = get_data_db()
        else:
            max_pain_df =oi.get_maxpain(ticker , expiry_date)
            max_pain_value = max_pain_df[['total_value']].idxmin().iloc[-1] 
            spot_price = kf.get_ltp(ticker)
            data.append([today , max_pain_value , spot_price])
            data_temp = get_data_db()
            data += data_temp
        
        data_final = data[::-1]

        main_df = pd.DataFrame(data = data_final , columns=['date','maxpain_value','price'])

        print(main_df)

        ####################### chartjs ########################
        NewChart = maxpain_linegraph(label_ticker=ticker,scale_label_str="Maxpain")()
        NewChart.labels.xaxis_labels = main_df['date'].apply(lambda x:x.strftime("%b-%d")).to_list()
        NewChart.data.linedata1.data = main_df['maxpain_value'].to_list()
        NewChart.data.linedata2.data = main_df['price'].to_list()
        ChartJSON_json = json.loads(NewChart.get())
        # chart = ChartJSON_json
        print(ChartJSON_json)
        return Response(ChartJSON_json)
             
        ####################### chartjs ########################

        # return ChartJSON_str
    
    def get(self , request):
        return Response({"ticker":"NIFTY","expiry_date":"2021-07-29"})

class PCR_Day_API_View(APIView):
    def post(self , request):
        ticker = request.data.get('ticker')
        expiry_date_str = request.data.get('expiry_date')
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        date = request.data.get('date')
        print(date)
        OI = OIAnalysis()
        if date:
            oi_df = OI.get_oi_df_anyday(ticker , expiry_date , date)
        else:
            oi_df = OI.get_oi_df_today(ticker , expiry_date ) 
    
        call_oi  = oi_df['calloi'].sum()
        put_oi = oi_df['putoi'].sum()
        
        # pcr value zero if put_oi/call_oi is 0 (handeling ZeroDivisionError Exception)
        if put_oi == 0 or call_oi == 0:
            pcr = 0   
        else: 
            pcr = round(float(put_oi / call_oi),2)

        return Response(pcr)
    def get(self , request):
        return Response({"ticker":"NIFTY","expiry_date":"2021-05-27"})

class PCR_History_Chart_API_View(APIView):
    def post(self , request):
        ticker = request.data.get('ticker')
        expiry_date_str = request.data.get('expiry_date')
        print('\t\t\t' + ticker)
        print('\t\t\t' + expiry_date_str)

        logging.debug(pformat("Data in Post is # "))
        logging.debug(pformat(request.data))
       
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()

        connection_string = 'postgresql://doadmin:or5ka898vk8r1wdi@srifintech-db-do-user-8454140-0.b.db.ondigitalocean.com:25060/defaultdb'
        db = create_engine(connection_string)

        kf,oi,po = functions_initializer()

        today = dt.datetime.now().date()
        from_date = today - dt.timedelta(10)
        ltd = kf.get_last_traded_dates()['last_traded_date']

        
        query_op = db.execute("select * from maxpain_history where date(expiry_date)='{}' and  date(date) >='{}' and ticker='{}' order by date desc".format(expiry_date , from_date , ticker)).fetchall()
        data = list()

        def get_data_db():
            data_temp = list()
            for i in range(len(query_op)):
                pcr_value = round(float(query_op[i]['pcr']),2)
                spot_price = query_op[i]['spot_price']
                data_temp.append([query_op[i]['date'] , pcr_value , spot_price])
            return data_temp


        if ltd == query_op[0]['date']:
            data = get_data_db()
        else:
            oi_df = oi.get_oi_df_today(ticker , expiry_date )
            call_oi  = oi_df['calloi'].sum()
            put_oi = oi_df['putoi'].sum()
            
            # pcr value zero if put_oi/call_oi is 0 (handeling ZeroDivisionError Exception)
            if put_oi == 0 or call_oi == 0:
                pcr = 0   
            else: 
                pcr = round(float(put_oi / call_oi),2)
            spot_price = kf.get_ltp(ticker)
            data.append([today ,pcr , spot_price])
            data_temp = get_data_db()
            data += data_temp

        data_final = data[::-1]
        
        main_df = pd.DataFrame( data = data_final , columns=['date','pcr_value','price'])

        print(main_df)
        NewChart = pcr_linegraph(label_ticker=ticker,scale_label_str="PCR")()
        NewChart.labels.xaxis_labels = main_df['date'].apply(lambda x:x.strftime("%b-%d")).to_list()
        NewChart.data.linedata1.data = main_df['pcr_value'].to_list()
        NewChart.data.linedata2.data = main_df['price'].to_list()
        ChartJSON_json = json.loads(NewChart.get())
       
        return Response(ChartJSON_json)

        

    def get(self , request):
        return Response({"ticker":"NIFTY","expiry_date":"2021-05-27"})

class Login(APIView):
    def get(self , request):
        request_token = request.GET.get("request_token")
        print(request_token)

        if request_token is None:
            # login_url = 'http://127.0.0.1:5000/kitelogin'
            login_url='https://kite.trade/connect/login?api_key=ydq5afgjqoqvj0up'
            context = {
                'login_url':login_url
            }
            return render(request , 'login_index.html', context)

class Kite_Login(APIView):
    def get(self , request):
        request_token = request.GET.get("request_token")
        if request_token is None:
            ka = KiteAuthentication()
            ka.debug=True
            if ka.kite_login_success:
                # return 'Success'
                return Response('success')
        else:
            logging.info('I received request token # ', request_token)
            ka = KiteAuthentication(request_token=request_token)

            if ka.kite_login_success:
                return Response('success')

                # return 'Success'
            current_time = dt.datetime.now().astimezone(timezone('Asia/Kolkata')).strftime('%H:%M')
            # return_text = 'Session established for today @ ' + str(current_time) + \
            return_text = 'Session established with access token # ' + ka.kite.access_token
            return Response(return_text)

class Get_MonteCarlo_Simulation(APIView):
    def post(self , request):
        logging.debug(pformat("Beginning of the MonteCarlo Simulation..."))
        logging.debug(pformat("Data in Post is # "))
        logging.debug(pformat(request.data))

        ##################Input parameters #####################
        ticker = request.data.get('ticker')
        simulation_days = int(request.data.get('simulation_days'))
        returns_from = request.data.get('returns_from')
        start_date = datetime.strptime(returns_from, '%Y-%m-%d').date()
        ##################Input parameters #####################
        todays_date = dt.datetime.now().date()
        logging.debug(pformat("\nTicker # {0}\nSimulation Days # {1}\nReturns Start Date # {2}".format(ticker, simulation_days, start_date)))
        predict_days = simulation_days
        history_days = (todays_date - start_date).days
        live_price_ind = 'N'
        mc = MonteCarlo_Simulation()
        montecarlo_result_df = mc.monte_carlo_prediction(ticker=ticker, predict_days=predict_days, history_days=history_days,
                                                    live_price_ind=live_price_ind,chartjson=True)

        upper_boundary = montecarlo_result_df.max().max()
        lower_boundary = montecarlo_result_df.min().min()
        upper_boundary = int(np.round(upper_boundary, 0))
        lower_boundary = int(np.round(lower_boundary, 0))

        
        logging.debug(pformat("\n"))
        logging.debug(pformat("Upper Boundary from Dataframe # ", upper_boundary))
        logging.debug(pformat("Lower Boundary from Dataframe # ", lower_boundary))
            
        

        
        ####################### chartjs ########################
        title1 = "Simulation for " + ticker 
        title2 = "Upper Boundary : " + str(upper_boundary) + "      Lower Boundary : " + str(lower_boundary)
        color_palette = [
                            Color.Red,
                            Color.Blue,
                            Color.Purple,
                            Color.Maroon,
                            Color.Magenta,
                            Color.Teal,
                            Color.Navy,
                            Color.Orange,
                            Color.Cyan,
                            Color.Lime,
                            Color.Olive,
                            Color.Brown, 
                            Color.Pink,
                            Color.Lavender,
                            Color.Mint,
                            Color.Apricot,
                            Color.Beige,
                            Color.Yellow,
                            Color.White

        ]
        color_count = predict_days

        def get_random_hexcolor():
            return '#{:06x}'.format(randint(0, 256**3))


        # LineData  
        class NewLineData: 
            def __init__(self, data, fill, label, yAxisID,borderColor=None): 
                self.data           = data
                self.fill           = fill
                self.label          = label
                self.yAxisID        = yAxisID
                #Border properties
                self.borderColor    = borderColor
                self.borderWidth    = 2
                self.lineTension    = 0
                #Point Properties
                self.pointRadius    = 1

        class LineGraph(BaseChart):

            type = ChartType.Line
            
            class labels:
                xaxis_labels = list()

            class data:
                class linedata:
                    label           = ticker
                    data            = []
                    #Border properties
                    borderColor     = Color.Black
                    borderColor     = Color.Hex("#7A9B0E")
                    borderWidth     = 3
                    
                    fill            = False
                    yAxisID         = 'y1'
                    lineTension     = 0
                    pointStyle = 'triangle'
                    borderDash      = [3, 1] 
                    #Point Properties
                    pointRadius     = 1


            class options:
                responsive = True
                
                title = {
                                "display"       : True,
                                "text"          : [title1, title2],
                                "fontSize"      : 18,
                                "fontColor"     : Color.Black,
                                "padding"       : 0
                }
                tooltips = {    
                                "enabled"       : False,
                                "intersect"     : False,
                }
                legend = {
                                "display"       : False,
                                'position'      : 'top', 
                                'labels'        : {
                                'fontColor'     : Color.Black, 
                                "boxWidth"      : 35,
                                "fontSize"      : 10,
                                "fontStyle"     : "bold"
                            }
                }
                
                layout = {
                            "padding"   :  {
                                            "left"    : 0,
                                            "right"   : 0,
                                            "top"     : 0,
                                            "bottom"  : 20
                        }
                }


                scales = {

                    "xAxes": [
                            {   
                                "scaleLabel": {
                                                "display"       : True,
                                                "labelString"   : "Days",
                                                "fontColor"     : Color.Black,
                                                "fontSize"      : 14,
                                                "fontStyle"     : "bold"
                                }, 
                                "display"           : True,
                                "gridLines"         : {
                                    "display"       : False,
                                    "drawBorder"    : True
                                }, 
                                
                        }
                    ],
                    "yAxes": [
                            {
                                "scaleLabel": {
                                                "display"       : True,
                                                "labelString"   : "Price",
                                                "fontColor"     : Color.Black,
                                                "fontSize"      : 14,
                                                "fontStyle"     : "bold"
                                }, 
                                "id"            : "y1",
                                "position"      : "left",
                                "display"       : True,
                                "gridLines"     : {
                                                    "display"     : False
                            }
                        }
                        # {
                        #     "scaleLabel": {
                        #                         "display"       : True,
                        #                         "labelString"   : "Price",
                        #                         "fontColor"     : Color.Black
                        #     }, 
                        #     "id"            : "y2",
                        #     "position"      : "left",
                        #     "gridLines"     : {
                        #                     "display"       : True
                        #     }
                        # }
                    ]
                }


        NewChart = LineGraph()
        NewChart.labels.xaxis_labels = montecarlo_result_df.index.to_list()
        # NewChart.data.linedata.data = montecarlo_result_df[ticker].to_list()
        ChartJSON_json = json.loads(NewChart.get())

        i = 0
        for day in range(mc.simulations):
            ###Adding New Line
            newline = NewLineData(  data=montecarlo_result_df[day].to_list(), 
                                    fill=False, 
                                    label=day, 
                                    yAxisID="y1", 
                                    # borderColor=color_palette[i % color_count]
                                    borderColor=Color.Hex(get_random_hexcolor())
            )
            newline_json = json.loads(json.dumps(newline.__dict__))
            ChartJSON_json['data']['datasets'].append(newline_json)
            i += 1
        

        # ChartJSON_str = json.dumps(ChartJSON_json) 
        # logging.debug(pformat("Rendering chartjson string..."))
        # ####################### chartjs ########################

        return Response(ChartJSON_json)
    def get(self , request):
        return Response({"ticker":"NIFTY","simulation_days":30,"returns_from":"2010-01-01"})

class Get_KiteAuth(APIView):
    def get(self , request):
        logging.debug(pformat('Authentication in progress...'))
        ka = KiteAuthentication()
        user_profile = ka.kite.profile()
        logging.debug(pformat(user_profile))
        ######## converting object to json########
        user_profile_json_str = json.dumps(user_profile)
        user_pofile_json = json.loads(user_profile_json_str)
        ######## converting object to json########

        return Response(user_pofile_json)

class Get_ltp_ticker(APIView):
    def post(self , request):
        logging.debug(pformat("Fetching Last Traded price..."))
        logging.debug(pformat("Data in Post is # "))
        logging.debug(pformat(request.data))

        ##################Input parameters #####################
        ticker = request.data.get('ticker')
        ticker = ticker.upper()
        ##################Input parameters #####################

        try:
            kf = KiteFunctions()
        except Exception as e:
            return_text = 'Error encountered # ' + e
            return return_text
        ltp = kf.get_ltp(ticker=ticker)

        return Response(str(ltp))
    
    def get(self , request):
        return Response({'ticker':'NIFTY'})


class Option_Chain(APIView):
    def post(self, request):
        # ********************************* INPUT PARAMS *******************************************
        try:
            ticker = [
                request.data.get("ticker", None),
            ]
            expiry = [
                datetime.strptime(
                    request.data.get("expiry_date", None), "%Y-%m-%d"
                ).date(),
            ]
        except Exception as e:
            return "Error encountered while reading input request:\n" + str(e)

        # ********************************** INPUT PARAMS ******************************************

        kf = KiteFunctions()
        interval = 450

        df1 = kf.master_instruments_df[
            (kf.master_instruments_df["exchange"] == "NFO")
            & (kf.master_instruments_df["segment"] == "NFO-OPT")
            & (kf.master_instruments_df["name"].isin(ticker))
            & (kf.master_instruments_df["expiry"].isin(expiry))
        ]
        # breakpoint()
        df1 = pd.concat(
            [df1, df1.loc[:, "tradingsymbol"].apply(lambda x: "NFO:" + x)], axis=1
        )

        df1.columns.values[-1] = "exchange_tradingsymbol"

        df1.reset_index(drop=True, inplace=True)

        def roundup(x):
            return int(math.ceil(x / 1000.0)) * 1000

        def final_func(param):
            return param

        out_df = pd.DataFrame()

        for i in range(interval, roundup(len(df1.index)), interval):
            print(str(i - interval) + " - " + str(i))
            try:
                out_df = pd.concat(
                    [
                        out_df,
                        pd.DataFrame(
                            kf.kite.quote(
                                df1.iloc[i - interval : i][
                                    "exchange_tradingsymbol"
                                ].tolist()
                            )
                        ).transpose(),
                    ]
                )
            except Exception as e:
                return "Error encountered while getting quote():\n" + str(e)

            if i > len(df1.index):
                break

        # breakpoint()
        out_df.reset_index(inplace=True)

        out_df.columns.values[0] = "exchange_tradingsymbol"

        out_df.columns.values[4] = "ltp"

        out_df = df1.merge(
            out_df.loc[
                :, ["exchange_tradingsymbol", "volume", "oi", "ohlc", "ltp", "depth"]
            ],
            on="exchange_tradingsymbol",
            how="inner",
        ).drop(
            [
                "instrument_token",
                "exchange_token",
                "last_price",
                "tick_size",
                "lot_size",
                "segment",
                "exchange",
                "exchange_tradingsymbol",
                "tradingsymbol",
                "name",
                "expiry",
            ],
            axis=1,
        )

        underlying_details = kf.kite.quote(["NSE:" + i for i in ticker])[
            ["NSE:" + i for i in ticker][0]
        ]

        days = (expiry[0] - dt.date.today()).days

        out_df = pd.concat(
            [
                out_df,
                pd.DataFrame(
                    out_df.apply(
                        lambda x: [
                            x["ltp"] - x["ohlc"]["close"],
                            x["depth"]["buy"][0]["quantity"],
                            x["depth"]["buy"][0]["price"],
                            x["depth"]["sell"][0]["price"],
                            x["depth"]["sell"][0]["quantity"],
                            implied_volatility(
                                x["instrument_type"],
                                underlying_details["last_price"],
                                x["strike"],
                                days,
                                0.04,
                                x["ltp"],
                            ),
                        ],
                        axis=1,
                    ).tolist(),
                    columns=[
                        "chng",
                        "bid qty",
                        "bid price",
                        "ask price",
                        "ask qty",
                        "iv",
                    ],
                ),
            ],
            axis=1,
        ).drop(["depth", "ohlc"], axis=1)

        def func(var):
            if var in [float("inf"), float("-inf")]:
                return None
            x = "%.2f" % var
            if len(str(x)) > 7:
                return None
            else:
                return x

        out_df["iv"] = out_df["iv"].apply(lambda var: func(var))

        out_df.set_index(["strike", "instrument_type"], inplace=True)

        return Response(
            out_df.fillna("-")
            .round(2)
            .groupby(level=0)
            .apply(lambda df: df.xs(df.name).to_dict("index"))
            .to_dict()
        )



