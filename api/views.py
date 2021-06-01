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
import pandas as pd

from rest_framework.views import APIView
from rest_framework.response import Response
import json
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

class Get_Straddle_Prices(APIView):
    def post(self, request):
        logging.debug(pformat('Beginning of straddle api...'))

        content = request.data
        logging.debug(pformat("Data in Post for /straddleprices is # "))
        logging.debug(pformat(content))

        ####################### Input parameters #####################
        try:
            ticker = content.get("ticker", None).upper()
            expiry_date = datetime.strptime(
                content.get("expiry_date", None), "%Y-%m-%d"
            ).date()

        except Exception as e:
            return "Error encountered while reading input request:\n" + e
        straddle_strike_list = content.get('strikes_list',[])
        intraday_ind = content.get('intraday_ind',True)
        ####################### Input parameters #####################

        kf = KiteFunctions()
        days = 10
        today_date = dt.datetime.now().date()
        if intraday_ind:
            start_date = kf.get_last_traded_dates()['last_traded_date']
            interval = kf.interval_5minute
        else:
            start_date = dt.datetime.now().date() - dt.timedelta(days=days)
            interval = kf.interval_day
            
        end_date = today_date

        logging.debug(pformat("\n\nTicker # {0}\nExpiry Date # {1}\nStraddle List # {2}\nIntraday Indicator # {3}\nStart Date # {4}\nEnd Date # {5}".format(ticker, expiry_date, straddle_strike_list, intraday_ind,
                                                                                                                                            start_date,end_date)))

        
        final_straddle_df = pd.DataFrame()
        for strike in straddle_strike_list:
            filter_df = kf.master_instruments_df[
                                                    (kf.master_instruments_df['name']      == ticker)
                                                & (kf.master_instruments_df['strike']    == strike)
                                                & (kf.master_instruments_df['expiry']    == expiry_date)
                                                ]

            logging.debug(pformat(filter_df))

            straddle_list = filter_df['tradingsymbol'].to_list()

            logging.debug(pformat("Straddle List {0} for strike {1}".format(straddle_list, strike)))

            straddle_prices_df = pd.DataFrame()
            for straddle_instrument in straddle_list:
                price_df = kf.get_price_history(    ticker=straddle_instrument,
                                                    start_date=start_date,
                                                    end_date=end_date,
                                                    interval=interval)
                price_df[straddle_instrument] = price_df['close']        
                price_df.drop(columns=['open','low','high','close', 'volume'], inplace=True)

                if straddle_prices_df.empty:
                    straddle_prices_df = price_df.copy()
                else:
                    straddle_prices_df = pd.concat([price_df, straddle_prices_df], axis=1, join='inner')

            straddle_prices_df[strike] = straddle_prices_df.sum(axis=1)

            if final_straddle_df.empty:
                final_straddle_df = straddle_prices_df.copy()
            else:
                final_straddle_df = pd.concat([final_straddle_df, straddle_prices_df], axis=1, join='inner')

        if ticker.upper() == "NIFTY":
            base_ticker = "NIFTY 50"
        elif ticker.upper() == "BANKNIFTY":
            base_ticker = "NIFTY BANK"
        else:
            base_ticker = ticker.upper()   

        ticker_df = kf.get_price_history(   ticker=base_ticker,
                                            start_date=start_date,
                                            end_date=end_date,
                                            interval=interval)

        if not ticker_df.empty:
            ticker_df.drop(columns=['open', 'high', 'low', 'volume'], inplace=True)
            ticker_df.rename(columns={'close': ticker}, inplace=True)
        else:
            logging.debug(pformat('Data for Base ticker is not fetched...'))

        final_straddle_df = pd.concat([final_straddle_df, ticker_df], axis=1, join='inner')
        final_straddle_df = final_straddle_df.apply(lambda x:round(x,2),axis=1)


        # straddle_prices_df.reset_index(inplace=True)

        logging.debug(pformat("-****************************************"))
        logging.info(pformat(final_straddle_df))

        if intraday_ind is True:
            final_straddle_df.index = final_straddle_df.index.strftime("%H:%M")
        else:
            final_straddle_df.index = final_straddle_df.index.strftime("%b-%d")

        ############################ chartjs ##########################
        straddle_linegraph = strangle_linegraph
        straddle_newline = strangle_newline

        NewChart = straddle_linegraph(label_ticker=ticker,scale_label_str="Straddle Prices")()
        NewChart.labels.xaxis_labels = final_straddle_df.index.to_list()
        NewChart.data.linedata.data = final_straddle_df[ticker].to_list()
        ChartJSON_json = json.loads(NewChart.get())

        color_count = len(straddle_strike_list)

        for ind,strike_item in enumerate(straddle_strike_list):
            ###Adding New Line
            newline = straddle_newline(  data=final_straddle_df[strike_item].to_list(), 
                                    fill=False, 
                                    label=strike_item, 
                                    yAxisID="y2", 
                                    borderColor=ind % color_count
            )()
            newline_json = json.loads(json.dumps(newline.__dict__))
            ChartJSON_json['data']['datasets'].append(newline_json)

        logging.debug(pformat("Rendering chartjson string..."))
        ####################### chartjs ########################

        return Response(ChartJSON_json)





