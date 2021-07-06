# import sys
# sys.path.append('.')
from django.shortcuts import render
import logging
from pprint import pformat
import datetime as dt
from datetime import datetime,date,timedelta
from pychartjs import BaseChart, ChartType, Color, Options   
from sqlalchemy import create_engine
import math
from api.implied_vol import implied_volatility

from api.classes import KiteAuthentication, KiteFunctions, MonteCarlo_Simulation, OIAnalysis, PostgreSQLOperations , Charting
from api.chartjs_classes import *  
import pandas as pd
import plotly.io as pio

from rest_framework.views import APIView
from rest_framework.response import Response
import json
from pytz import timezone
from django.http import HttpResponse
import numpy as np
import sys


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

        if expiry_date < dt.datetime.now().date():
            return Response('Past expiry is not valid')
        display_strikes_count = 15
        # ticker = 'NIFTY'
        # expiry_date = dt.date(2020,12,31)
        
        ##################Input parameters #####################

        kf =  KiteFunctions()
        oi =  OIAnalysis()

        last_traded_day = kf.get_last_traded_dates()['last_traded_date']
        today_date = dt.datetime.now().date()
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
        if expiry_date < dt.datetime.now().date():
            return Response('Past expiry is not valid')
        
        connection_string = 'postgresql://doadmin:or5ka898vk8r1wdi@srifintech-db-do-user-8454140-0.b.db.ondigitalocean.com:25060/defaultdb'

        db = create_engine(connection_string)


        today = dt.datetime.now().date()
        from_date = today - dt.timedelta(10)

        print(from_date)

        kf =  KiteFunctions()
        oi =  OIAnalysis()

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
        if expiry_date < dt.datetime.now().date():
            return Response('Past expiry is not valid')
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
        if expiry_date < dt.datetime.now().date():
            return Response('Past expiry is not valid')

        connection_string = 'postgresql://doadmin:or5ka898vk8r1wdi@srifintech-db-do-user-8454140-0.b.db.ondigitalocean.com:25060/defaultdb'
        db = create_engine(connection_string)

        kf =  KiteFunctions()
        oi =  OIAnalysis()

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
        user_profile_json = json.loads(user_profile_json_str)
        ######## converting object to json########

        return Response(user_profile_json)

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
            return Response(return_text)
        ltp = kf.get_ltp(ticker=ticker)

        return Response(str(ltp))
    
    def get(self , request):
        return Response({'ticker':'NIFTY'})

class Get_Multistrike_OIchart(APIView):
    def post(self , request):
        logging.debug(pformat('Beginning of multistrikeoichartjs api...'))
        content = request.data
        logging.debug(pformat("Data in Post for /chartjson is # "))
        logging.debug(pformat(content))
        
        ticker = request.data.get('ticker')
        expiry_date_str = request.data.get('expiry_date')
        strikes = request.data.get('strikes')
        intraday_ind = request.data.get('intraday_ind')
        

        today_date = dt.datetime.now().date()
        ticker = ticker.upper()
        strike_list = strikes
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        if expiry_date < dt.datetime.now().date():
            return Response('Past expiry is not valid')

        logging.debug(pformat('Ticker # {0}\nExpiry {1}\nStrikes are # {2}\nIntradayIndicator # {3}'.format(ticker,expiry_date, strikes, intraday_ind)))

        current_time = dt.datetime.now().astimezone(timezone('Asia/Kolkata')).strftime('%H:%M')
        suptitle = 'Open Interest Analysis'
        title = 'Open Interest for ' + ticker.upper() + ' @ ' + str(current_time)
        xlabel = 'DateTime'
        ylabel = 'OI Volume'
        oi = OIAnalysis()

        
        if intraday_ind is True:
            start_date = oi.kf.get_last_traded_dates()['last_traded_date']
        else:
            start_date = today_date - dt.timedelta(days=10)
        
        end_date = today_date

        logging.debug(pformat('Ticker # {0}, Expiry {1} and Strikes are # {2}'.format(ticker,expiry_date, strike_list)))

        oi_df = oi.get_multistrike_oi_df(ticker=ticker,
                            strike_list=strike_list,
                            start_date=start_date,
                            end_date=end_date,
                            expiry_date=expiry_date,
                            intraday=intraday_ind)
        
        # print(oi_df)

        if intraday_ind is True:
            oi_df.index = oi_df.index.strftime("%H:%M")
        else:
            oi_df.index = oi_df.index.strftime("%b-%d")


        ####################### chartjs ########################
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
                            Color.Brown, ##
                            Color.Pink,##
                            Color.Lavender,##
                            Color.Mint,# 
                            Color.Apricot,#
                            Color.Beige,#
                            Color.Yellow,#
                            Color.White

        ]
        color_count = len(strike_list)

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
                # self.pointStyle = 'triangle'
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
                    # backgroundColor = Color.Green
                    fill            = False
                    yAxisID         = 'y1'
                    lineTension     = 0
                    pointStyle = 'triangle'
                    borderDash      = [3, 1] # ProvidesDashed line.  
                    #Point Properties
                    pointRadius     = 1
                    # pointRotation   = 180
                    # pointHoverRadius= 7

            class options:
                responsive = True

                tooltips = {
                                "intersect"         : False,
                                # "backgroundColor" : Color.Red
                                # "mode"              : "nearest",
                                # # "mode"              : "index",
                                # "axis"              : "x",
                                # "position"          : "nearest",
                                # "displayColors"     : True
                                # # "cornerRadius"      : 3
                }
                
                # title = Options.Title(text="MULTI STRIKE OI CHART", fontsize=18)
                # showLines = False # This will not draw lines between points
                # title = {   
                #             "display"           : True,
                #             "text"              : "sample title",
                #             "fontSize"          : 20,
                #             "fontColor"         : Color.Green
                # }

                # legend = Options.Legend(position="bottom")
                legend = {
                                'position'      : 'top', 
                                'labels'        : {
                                'fontColor'     : Color.Black, 
                                "boxWidth"      : 35,
                                # 'fullWidth'   : True,
                                "fontSize"      : 10,
                                "fontStyle"     : "bold"
                                # "padding"     : 50,
                                # "usePointStyle" : True
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
                            
                            "display"        : True,
                            #    "type"           : "time",
                            #    "time"           : {
                            #         "parser"         : "HH:mm",
                            #         # "unit"    : "minute"
                            #         "unit"      : "hour"
                            #         # "unitStepSize" : 60

                            #    },
                                # "labelString"    : "DateTime" ,
                                "gridLines"     : {
                                    "display"      : False,
                                    "drawBorder"   : True
                                }, 
                        }
                    ],
                    "yAxes": [
                            {
                                "scaleLabel": {
                                                "display"       : True,
                                                "labelString"   : ticker,
                                                "fontColor"     : Color.Black
                                }, 
                                "id"            : "y1",
                                "position"      : "right",
                                "display"       : True,
                                "gridLines"     : {
                                                    "display"     : False
                                                # "drawBorder"    : True
                            }
                        },
                        {
                            "scaleLabel": {
                                                "display"       : True,
                                                "labelString"   : "Open Interest",
                                                "fontColor"     : Color.Black
                            }, 
                            "id"            : "y2",
                            "position"      : "left",
                            "gridLines"     : {
                                            "display"       : True
                                            # "drawBorder"   : True
                            }
                        }
                    ]
                }
                # animation = {
                #     "duration"        : 1000
                #     "easing"          : "easeOutCirc"

                # }

            # class pluginOptions:
            #     zoom = {
            #         "pan": {
            #                       "enabled": True,
            #                       "mode": "x",
            #                       "speed": 10,
            #                       "threshold": 10
            #         },
            #         "zoom" : {
            #             "enabled" : True,
            #             "mode": "y"
            #         }
            #     }
                        
        NewChart = LineGraph()
        NewChart.labels.xaxis_labels = oi_df.index.to_list()
        NewChart.data.linedata.data = oi_df[ticker].to_list()
        ChartJSON_json = json.loads(NewChart.get())

        i = 0
        for strike_item in strike_list:
            ###Adding New Line
            newline = NewLineData(  data=oi_df[strike_item].to_list(), 
                                    fill=False, 
                                    label=strike_item, 
                                    yAxisID="y2", 
                                    # borderColor=Color.Hex(get_random_hexcolor())
                                    borderColor=color_palette[i % color_count]
            )
            newline_json = json.loads(json.dumps(newline.__dict__))
            ChartJSON_json['data']['datasets'].append(newline_json)
            i += 1
        # # ###Add New LIne
        # newline = NewLineData(data=oi_df[strike_list[1]].to_list(), fill=False, label=strike_list[1], yAxisID="y2", borderColor=Color.Hex(get_random_hexcolor()))
        # newline_json = json.loads(json.dumps(newline.__dict__))
        # ChartJSON_json['data']['datasets'].append(newline_json)
        
        
        # ChartJSON_str = json.dumps(ChartJSON_json) 

        ####################### chartjs ########################

        return Response(ChartJSON_json)
    
    def get(self , request):
        return Response({"ticker" : "NIFTY","expiry_date" : "2021-5-27","strikes" : ["15000PE", "15300CE"],"intraday_ind":'true'})

class Get_Multistrike_OIchange(APIView):
    def post(self , request):
        content = request.data
        ticker = request.data.get('ticker')
        expiry_date_str = request.data.get('expiry_date')
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        if expiry_date < dt.datetime.now().date():
            return Response('Past expiry is not valid')
        strikes = request.data.get('strikes')
        chart = request.data.get('chart')
        intraday_ind = True

        logging.debug(pformat('Ticker # {0}\nExpiry {1}\nStrikes are # {2}\nIntradayIndicator # {3}'.format(ticker,expiry_date, strikes, intraday_ind)))

        current_time = dt.datetime.now().astimezone(timezone('Asia/Kolkata')).strftime('%H:%M')
        suptitle = 'Open Interest Analysis'
        title = 'Open Interest for ' + ticker.upper() + ' @ ' + str(current_time)
        xlabel = 'DateTime'
        ylabel = 'OI Volume'
        oi = OIAnalysis()

        today_date = dt.datetime.now().date()
        ticker = ticker.upper()
        strike_list = strikes

        if intraday_ind is True:
            """
            Get Last traded day in NSE by fetching NIFTY prices for last one week.  
            Then the last traded date in nifty_df will be the latest traded day.
            This activity is required only for the Intraday chart
            """
            

            start_date = oi.kf.get_last_traded_dates()['last_traded_date']
        else:
            start_date = today_date - dt.timedelta(days=10),

        end_date = today_date

        logging.debug(pformat('Ticker # {0}, Expiry {1} and Strikes are # {2}'.format(ticker,expiry_date, strike_list)))

        oi_df = oi.get_multistrike_oichange_df(ticker=ticker,
                            strike_list=strike_list,
                            start_date=start_date,
                            end_date=end_date,
                            expiry_date=expiry_date,
                            intraday=intraday_ind)

        if oi_df.empty:
            return_text = 'Data not fetched for ticker # ' + ticker + ' for expiry date # ' + str(expiry_date)
            return Response(return_text)
        else:
            if chart:
                ch = Charting()
                current_time = dt.datetime.now().astimezone(timezone('Asia/Kolkata')).strftime('%H:%M')
                title = 'OI Change for  ' + ticker + ' @ '+ str(current_time)

                fig = ch.plotly_goscatter_chart_with_secondary(df=oi_df,
                                                            title=title,
                                                            xlabel='DateTime',
                                                            ylabel='OI Volume',
                                                            secondary_plot=ticker
                                                            )
                logging.debug(pformat('Rendering OI Chart...'))
                return pio.to_html(fig=fig,full_html=True)
            else:
                return Response(oi_df.to_json(orient="index"), mimetype='application/json')    
    def get(self , request):
        return Response({"ticker":"NIFTY","expiry_date":"2021-05-27" , "strikes":"12800PE" , "chart":"temp"})

class Get_OIchange_Chart(APIView):
    def post(self , request):
        logging.debug(pformat('\n\nBeginning of OI Change api with new quote logic...'))

        content = request.data
        logging.debug(pformat("Data in Post is # "))
        logging.debug(pformat(content))

        ##################Input parameters #####################
        ticker = request.data.get('ticker')
        expiry_date_str = request.data.get('expiry_date')
        # from_date_str = content['from_date']
        # to_date_str = content['to_date']
            
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        if expiry_date < dt.datetime.now().date():
            return Response('Past expiry is not valid')
        
        # from_date   = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        # to_date     = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        
    
        ##################Input parameters ######################
        
        
        table_name = 'index_option_history_day'
        db_location = 'srifintech-database'
        oi = OIAnalysis()
        
        to_date = oi.kf.get_last_traded_dates()['last_traded_date']
        from_date = oi.kf.get_last_traded_dates()['last_traded_date-1']
        display_strikes_count = 15
        
        oi_df1 = oi.get_oi_df_anyday(ticker=ticker, expiry_date=expiry_date, date=from_date)
        
        oi_df1.rename(columns = {'calloi': 'calloi1', 
                                'putoi' : 'putoi1'}, inplace = True)

        logging.debug(pformat("HERE IS THE FIRST OI DATA"))
        logging.debug(pformat(oi_df1))
        today_date = dt.datetime.now().date()
        if to_date == today_date:
            oi_df2 = oi.get_oi_df_today(ticker=ticker, expiry_date=expiry_date)
            oi_df2.rename(columns = {'calloi': 'calloi2', 
                                    'putoi' : 'putoi2'}, inplace = True)
        else:
        
            oi_df2 = oi.get_oi_df_anyday(ticker=ticker, expiry_date=expiry_date, date=to_date)
            oi_df2.rename(columns = {'calloi': 'calloi2', 
                                    'putoi' : 'putoi2'}, inplace = True)

        logging.debug(pformat("HERE IS THE SECOND OI DATA"))
        logging.debug(pformat(oi_df2))

        oi_change_df = pd.merge(oi_df1, oi_df2, on = "strike", how = "inner")

        oi_change_df['callchange'] = oi_change_df['calloi2'] - oi_change_df['calloi1']
        oi_change_df['putchange'] = oi_change_df['putoi2'] - oi_change_df['putoi1']
        
        logging.debug(pformat(oi_change_df))
        #########################################
        ltp = oi.kf.get_ltp(ticker=ticker)
        annotation_label = "Spot Price: " + str(ltp)
        strike_list = oi_change_df.index.to_list()
        absolute_difference_function = lambda list_value : abs(list_value - ltp)
        closest_strike = min(strike_list, key=absolute_difference_function)
        logging.debug(pformat("Closest Strike is # ", closest_strike))
        row_num = oi_change_df.index.get_loc(closest_strike)
        logging.debug(pformat("Row Num of closest strike # ", row_num))
        oi_df = oi_change_df.iloc[row_num - display_strikes_count :  row_num + display_strikes_count]
        
        # logging.debug(pformat(oi_df))

        ####################### chartjs ########################

        NewChart = oichange_bargraph(closest_strike=closest_strike,
            annotation_label=annotation_label)()
        
        NewChart.labels.xaxis_labels    = oi_df.index.to_list()
        NewChart.data.bardata1.data     = oi_df["callchange"].to_list()
        NewChart.data.bardata2.data     = oi_df["putchange"].to_list()
        
        ChartJSON_json = json.loads(NewChart.get())

        # ChartJSON_str = NewChart.get()


        # logging.debug(pformat("\n\nHere is the chartjson..."))
        # logging.debug(pformat(ChartJSON_str))

        ####################### chartjs ########################

        return Response(ChartJSON_json)
    
    def get(self , request):
        return Response({"ticker":"NIFTY" ,"expiry_date":"2021-05-27"})

class Get_Maxpain_Chart(APIView):
    def post(self , request):
        logging.debug(pformat('\n\nBeginning of Maxpain api...'))

        content = request.data
        logging.debug(pformat("Data in Post is # "))
        logging.debug(pformat(content))

        ##################Input parameters #####################
        ticker = request.data.get('ticker')
        expiry_date_str = request.data.get('expiry_date')
        
        # intraday_ind = contenct['intraday_ind']
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        if expiry_date < dt.datetime.now().date():
            return Response('Past expiry is not valid')
        
        # ticker = 'NIFTY'
        # expiry_date = dt.date(2020,12,31)
        
        logging.debug(pformat("\nCalculating maxpain for Ticker # {0}\nfor expiry # {1}".format(ticker, expiry_date)))
        ##################Input parameters #####################
        oi = OIAnalysis()
        maxpain_df = oi.get_maxpain( ticker=ticker,
                                expiry_date=expiry_date)

        maxpain_value = int(maxpain_df[['total_value']].idxmin().iloc[-1])

        logging.debug(pformat('\n\nHere is the Final Maxpain Dataframe...'))
        logging.debug(pformat(maxpain_df))
        logging.debug(pformat("\nMax pain value: ", maxpain_value))
        
        title_text = "Max Pain Value # " + str(maxpain_value)
        annotation_label = "MaxPain: " + str(maxpain_value)
        strike_list = maxpain_df.index.to_list()
        # absolute_difference_function = lambda list_value : abs(list_value - ltp)
        # closest_strike = min(strike_list, key=absolute_difference_function)
        # logging.debug(pformat("Closest Strike is # ", closest_strike))

        ####################### BarGraph chartjs ########################
        class NewBarData: 
            def __init__(self, data, fill, borderWidth=None,backgroundColor=None, borderColor=None): 
                self.data            = data
                #Border properties
                self.borderColor     = borderColor
                self.borderWidth     = borderWidth
                self.backgroundColor = backgroundColor
                self.fill            = fill


        class BarGraph(BaseChart):

            type = ChartType.Bar
            
            class labels:
                xaxis_labels = list()

            class data:
                class bardata1:     #This is for Plotting Cumulative Call Value
                        label           = "Cumulative Call"
                        data            = []
                        #Border properties
                        borderColor     = Color.Black
                        borderWidth     = 1
                        backgroundColor = Color.Red
                        fill            = True

                class bardata2:     #This is for Plotting Cumulative Put Value
                        label           = "Cumulative Put"
                        data            = []
                        #Border properties
                        borderColor     = Color.Black
                        borderWidth     = 1
                        backgroundColor = Color.Green
                        fill            = True

            class options:
                responsive = True
                annotation = {
                        "annotations": [
                        {
                            "drawTime": "beforeDatasetsDraw",
                            "id": "vline",
                            "type": "line",
                            "mode": "vertical",
                            "scaleID": "x-axis-0",  
                            "value": maxpain_value,
                            "borderColor": Color.Black,
                            "borderWidth": 5,
                            "label": {
                                "backgroundColor": Color.Hex("#7A9B0E"),
                                "content": annotation_label,
                                "enabled": True,
                                "position" : "top"
                            }
                        },          
                        ]
                }
                tooltips = {
                                "intersect"         : False,
                                # "mode"              : "nearest",
                                "mode"              : "index",
                                "axis"              : "x",
                                "position"          : "nearest",
                                "displayColors"     : True
                                # "cornerRadius"      : 3
                }
                
                # title = Options.Title(text=title_text, fontsize=30, fontcolor=Color.Black, fontstyle="bold")
        #         # showLines = False # This will not draw lines between points
                title = {   
                            "display"           : True,
                            "text"              : title_text,
                            "fontSize"          : 20,
                            "fontColor"         : Color.Black,
                            "fontStyle"         : "bold"
                }

        #         # legend = Options.Legend(position="bottom")
                legend = {      
                                'display'       : False,
                                'position'      : 'top', 
                                'labels'        : {
                                'fontColor'     : Color.Black, 
                                "boxWidth"      : 35,
                                # 'fullWidth'   : True,
                                "fontSize"      : 16,
                                "fontStyle"     : "bold"
                                # "padding"     : 50,
                                # "usePointStyle" : True
                            }
                }
                


                scales = {

                    "xAxes": [
                            {   
                            
                            "display"        : True,
                            "labelString"    : "Strike Prices" ,
                                "gridLines"     : {
                                    "display"      : False,
                                    "drawBorder"   : True
                                }, 
                        }
                    ],
                    "yAxes": [
                            {
                                "scaleLabel": {
                                                "display"       : False,
                                                "labelString"   : "Open Interest",
                                                "fontColor"     : Color.Black,
                                                "fontSize"      : 16
                                    }, 
                                "id"            : "y1",
                                "position"      : "left",
                                "display"       : True,
                                "gridLines"     : {
                                                    "display"     : True
                                                # "drawBorder"    : True
                            }
                        }
                    
                    ]
                }
    
        ####################### BarGraph chartjs ########################


        NewChart = BarGraph()
        
        NewChart.labels.xaxis_labels    = maxpain_df.index.to_list()
        NewChart.data.bardata1.data     = maxpain_df["cum_call"].to_list()
        NewChart.data.bardata2.data     = maxpain_df["cum_put"].to_list()

        # ChartJSON_str = NewChart.get()

        ChartJSON_json = json.loads(NewChart.get())


        # logging.debug(pformat("\n\nHere is the chartjson..."))
        # logging.debug(pformat(ChartJSON_str))
        ####################### chartjs ########################

        return Response(ChartJSON_json)
    def get(self , request):
        return Response({"ticker":"NIFTY" ,"expiry_date":"2021-05-27"})

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
            return Response({"Error encountered while reading input request:\n": str(e)})

        # ********************************** INPUT PARAMS ******************************************

        try:
            kf = KiteFunctions()
        except Exception as e:
            return_text = 'Error encountered # ' + e
            return Response(return_text)
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
                return Response("Error encountered while getting quote():\n" + str(e))

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
        # breakpoint()
        underlying_details = kf.kite.quote([
            "NSE:NIFTY 50" if i== "NIFTY"
            else "NSE:NIFTY BANK" if i=="BANKNIFTY"
            else "NSE:" + i for i in ticker 
            ])[
            [
            "NSE:NIFTY 50" if i== "NIFTY"
            else "NSE:NIFTY BANK" if i=="BANKNIFTY"
            else "NSE:" + i for i in ticker 
            ][0]
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

class Get_Straddle_Prices(APIView):
    def post(self, request):
        logging.debug(pformat("Beginning of straddle api..."))

        content = request.data
        logging.debug(pformat("Data in Post for /straddleprices is # "))
        logging.debug(pformat(content))

        ####################### Input parameters #####################
        try:
            ticker = content.get("ticker", None).upper()
            expiry_date = datetime.strptime(
                content.get("expiry_date", None), "%Y-%m-%d"
            ).date()
            if expiry_date < dt.datetime.now().date():
                return Response('Past expiry is not valid')

        except Exception as e:
            return Response({"Error encountered while reading input request:\n": str(e)})
        straddle_strike_list = content.get("strikes_list", [])
        intraday_ind = content.get("intraday_ind", True)
        combined = content.get("combined",True)
        ####################### Input parameters #####################

        try:
            kf = KiteFunctions()
        except Exception as e:
            return_text = 'Error encountered # ' + e
            return Response(return_text)
        days = 10
        today_date = dt.datetime.now().date()
        if intraday_ind:
            start_date = kf.get_last_traded_dates()["last_traded_date"]
            interval = kf.interval_5minute
        else:
            start_date = dt.datetime.now().date() - dt.timedelta(days=days)
            interval = kf.interval_day

        end_date = today_date

        logging.debug(
            pformat(
                "\n\nTicker # {0}\nExpiry Date # {1}\nStraddle List # {2}\nIntraday Indicator # {3}\nStart Date # {4}\nEnd Date # {5}".format(
                    ticker,
                    expiry_date,
                    straddle_strike_list,
                    intraday_ind,
                    start_date,
                    end_date,
                )
            )
        )

        final_straddle_df = pd.DataFrame()
        for strike in straddle_strike_list:
            filter_df = kf.master_instruments_df[
                (kf.master_instruments_df["name"] == ticker)
                & (kf.master_instruments_df["strike"] == strike)
                & (kf.master_instruments_df["expiry"] == expiry_date)
            ]

            logging.debug(pformat(filter_df))

            straddle_list = filter_df["tradingsymbol"].to_list()

            logging.debug(
                pformat(
                    "Straddle List {0} for strike {1}".format(straddle_list, strike)
                )
            )

            straddle_prices_df = pd.DataFrame()
            for straddle_instrument in straddle_list:
                price_df = kf.get_price_history(
                    ticker=straddle_instrument,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                )
                price_df[straddle_instrument] = price_df["close"]
                price_df.drop(
                    columns=["open", "low", "high", "close", "volume"], inplace=True
                )

                if straddle_prices_df.empty:
                    straddle_prices_df = price_df.copy()
                else:
                    straddle_prices_df = pd.concat(
                        [price_df, straddle_prices_df], axis=1, join="inner"
                    )

            straddle_prices_df[strike] = straddle_prices_df.sum(axis=1)

            if final_straddle_df.empty:
                final_straddle_df = straddle_prices_df.copy()
            else:
                final_straddle_df = pd.concat(
                    [final_straddle_df, straddle_prices_df], axis=1, join="inner"
                )

        if ticker.upper() == "NIFTY":
            base_ticker = "NIFTY 50"
        elif ticker.upper() == "BANKNIFTY":
            base_ticker = "NIFTY BANK"
        else:
            base_ticker = ticker.upper()

        ticker_df = kf.get_price_history(
            ticker=base_ticker,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )

        if not ticker_df.empty:
            ticker_df.drop(columns=["open", "high", "low", "volume"], inplace=True)
            ticker_df.rename(columns={"close": ticker}, inplace=True)
        else:
            logging.debug(pformat("Data for Base ticker is not fetched..."))

        final_straddle_df = pd.concat(
            [final_straddle_df, ticker_df], axis=1, join="inner"
        )
        final_straddle_df = final_straddle_df.apply(lambda x: round(x, 2), axis=1)

        # straddle_prices_df.reset_index(inplace=True)

        logging.debug(pformat("-****************************************"))
        logging.info(pformat(final_straddle_df))

        if intraday_ind is True:
            final_straddle_df.index = final_straddle_df.index.strftime("%H:%M")
        else:
            final_straddle_df.index = final_straddle_df.index.strftime("%b-%d")

        if combined:
            final_straddle_df["Combined"] = final_straddle_df[straddle_strike_list].sum(axis=1)
            straddle_strike_list.insert(0,"Combined")

        ############################ chartjs ##########################
        straddle_linegraph = strangle_linegraph
        straddle_newline = strangle_newline

        NewChart = straddle_linegraph(
            label_ticker=ticker, scale_label_str="Straddle Prices"
        )()
        NewChart.labels.xaxis_labels = final_straddle_df.index.to_list()
        NewChart.data.linedata.data = final_straddle_df[ticker].to_list()
        ChartJSON_json = json.loads(NewChart.get())

        color_count = len(straddle_strike_list)

        for ind, strike_item in enumerate(straddle_strike_list):
            ###Adding New Line
            newline = straddle_newline(
                data=final_straddle_df[strike_item].to_list(),
                fill=False,
                label=strike_item,
                yAxisID="y2",
                borderColor=ind % color_count,
            )()
            newline_json = json.loads(json.dumps(newline.__dict__))
            ChartJSON_json["data"]["datasets"].append(newline_json)

        logging.debug(pformat("Rendering chartjson string..."))
        ####################### chartjs ########################

        return Response(ChartJSON_json)

class Get_Strangle_Prices(APIView):
    def post(self, request):
        logging.debug(pformat("Beginning of strangle api..."))
        logging.debug(pformat(datetime.now()))
        sc_start_time = datetime.now()
        content = request.data
        logging.info(pformat("Data in Post for /strangleprices is # "))
        logging.info(pformat(content))

        ####################### Input parameters #####################
        try:
            ticker = content.get("ticker", None).upper()
            expiry_date = datetime.strptime(
                content.get("expiry_date", None), "%Y-%m-%d"
            ).date()
            if expiry_date < dt.datetime.now().date():
                return Response('Past expiry is not valid')

            # Creates a list of dictionaries of the form:
            # [{'CE': 16750.0, 'PE': 12200.0, 'label': 'Pair1'},{'CE': 16700.0, 'PE': 12250.0, 'label': 'Pair2'}]
            strangle_strike_list = [
                {
                    "CE": float(val.get("call_strike", None)),
                    "PE": float(val.get("put_strike", None)),
                    "label": str(key).capitalize(),
                }
                for key, val in content.get("strangle_strikes", {}).items()
            ]

        except Exception as e:
            return Response({"Error encountered while reading input request:\n": str(e)})
        intraday_ind = content.get("intraday_ind", True)
        combined = content.get("combined",True)
        ####################### Input parameters #####################

        days = 10
        try:
            kf = KiteFunctions()
        except Exception as e:
            return_text = 'Error encountered # ' + e
            return Response(return_text)

        # Interval = 5 mins if intraday set to True else Interval = 10 days
        start_date, interval = (
            (kf.get_last_traded_dates()["last_traded_date"], kf.interval_1minute)
            if intraday_ind
            else (dt.datetime.now().date() - dt.timedelta(days=days), kf.interval_day)
        )
        ####### Logging input params ######

        logging.debug(pformat(ticker))
        logging.debug(pformat(expiry_date))
        logging.debug(pformat(strangle_strike_list))
        logging.debug(pformat(intraday_ind))
        logging.debug(pformat(start_date))

        ####### Logging input params ######

        final_strangle_df = pd.DataFrame()
        for single_dict in strangle_strike_list:
            logging.debug(pformat("Printing single dict:"))
            logging.debug(pformat(single_dict))

            strangle_list = kf.master_instruments_df[
                (kf.master_instruments_df["name"] == ticker)
                & (
                    (
                        (kf.master_instruments_df["strike"] == single_dict["CE"])
                        & (kf.master_instruments_df["instrument_type"] == "CE")
                    )
                    | (
                        (kf.master_instruments_df["strike"] == single_dict["PE"])
                        & (kf.master_instruments_df["instrument_type"] == "PE")
                    )
                )
                & (kf.master_instruments_df["expiry"] == expiry_date)
            ]["tradingsymbol"].to_list()

            logging.debug(pformat("Strangle list obtained:"))
            logging.debug(pformat(strangle_list))

            strangle_prices_df = pd.DataFrame()
            for strangle_instrument in strangle_list:
                price_df = kf.get_price_history(
                    ticker=strangle_instrument,
                    start_date=start_date,
                    end_date=dt.datetime.now().date(),
                    interval=interval,
                )

                logging.debug(pformat(price_df))
                price_df[strangle_instrument] = price_df["close"]
                price_df.drop(
                    columns=["open", "low", "high", "close", "volume"], inplace=True
                )
                logging.debug(pformat(price_df))

                # Copy price_df  if strangle_prices_df is empty else
                #  append/concat price_df into strangle_prices_df
                strangle_prices_df = (
                    price_df.copy()
                    if strangle_prices_df.empty
                    else pd.concat([price_df, strangle_prices_df], axis=1, join="inner")
                )

                logging.debug(pformat(strangle_prices_df))

            # eg: column header label would be "pair1" for CE -> 16750.0 and PE -> 12200.0
            strangle_prices_df[f"{single_dict['label']}"] = strangle_prices_df.sum(
                axis=1
            )
            final_strangle_df = (
                strangle_prices_df.copy()
                if final_strangle_df.empty
                else pd.concat(
                    [final_strangle_df, strangle_prices_df], axis=1, join="inner"
                )
            )
            final_strangle_df = final_strangle_df.apply(lambda x: round(x, 2), axis=1)

            logging.debug(pformat(final_strangle_df))

        base_ticker = (
            "NIFTY 50"
            if ticker.upper() == "NIFTY"
            else "NIFTY BANK"
            if ticker.upper() == "BANKNIFTY"
            else ticker.upper()
        )

        ticker_df = kf.get_price_history(
            ticker=base_ticker,
            start_date=start_date,
            end_date=dt.datetime.now().date(),
            interval=interval,
        )

        logging.debug(pformat(ticker_df))

        if not ticker_df.empty:
            ticker_df.drop(columns=["open", "high", "low", "volume"], inplace=True)
            ticker_df.rename(columns={"close": ticker}, inplace=True)
        else:
            logging.debug(pformat("Data for Base ticker is not fetched..."))

        final_strangle_df = pd.concat(
            [final_strangle_df, ticker_df], axis=1, join="inner"
        )
        logging.debug(pformat(final_strangle_df))

        final_strangle_df.index = (
            final_strangle_df.index.strftime("%H:%M")
            if intraday_ind
            else final_strangle_df.index.strftime("%b-%d")
        )

        logging.debug(pformat(final_strangle_df))
        if combined:
            final_strangle_df["Combined"] = final_strangle_df[ [i['label'] for i in strangle_strike_list] ].sum(axis=1)
            strangle_strike_list.insert(0,{'label': "Combined"})

        ####################### chartjs ########################
        NewChart = strangle_linegraph(
            label_ticker=ticker, scale_label_str="Strangle Prices"
        )()
        NewChart.labels.xaxis_labels = final_strangle_df.index.to_list()
        NewChart.data.linedata.data = final_strangle_df[ticker].to_list()
        ChartJSON_json = json.loads(NewChart.get())
        logging.debug(pformat(ChartJSON_json))

        color_count = len(strangle_strike_list)
        for ind, single_dict in enumerate(strangle_strike_list):
            ###Adding New Line
            newline = strangle_newline(
                data=final_strangle_df[f"{single_dict['label']}"].to_list(),
                fill=False,
                label=f"{single_dict['label']}",
                yAxisID="y2",
                borderColor=ind % color_count,
            )()
            newline_json = json.loads(json.dumps(newline.__dict__))
            logging.debug(pformat(newline_json))
            ChartJSON_json["data"]["datasets"].append(newline_json)

        logging.debug(pformat(datetime.now() - sc_start_time))
        logging.debug(pformat("Rendering chartjson string..."))

        ####################### chartjs ########################

        return Response(ChartJSON_json)

class Gainers_Losers(APIView):
    def post(self, request):
        '''
        The gainers losers API returns the Top
        Gainers and Top Losers. 
        The expiry date is required only when
        Fetching the Gainers and Losers for Futures.

        :param number: Positive Integer for the number of records. 
                        0(Zero) returns all

        :param gainers_or_losers: String value. Allowed values are
        "Gainers","Losers" or "Both"

        :param type: String value. Allowed values are
        "Stocks", "Indices" or "Futures"

        :param chart: Boolean value. Default is True. 
        True -> Chart Js json response
        False -> DataFrame json response

        :param expiry_date: String date. Optional parameter.
        Required when :param type: set to "Futures"

        Example requests:

        1.
        {
        "number":5,
        "gainers_or_losers":"both",
        "type":"futures",
        "expiry_date":"2021-07-29"
        }

        Returns top 5 gainers and losers for futures for the expiry
        "2021-07-29"

        2.
        {
        "number":0,
        "gainers_or_losers":"losers",
        "type":"futures",
        "expiry_date":"2021-07-29"
        }
        Returns top all losers for futures for the expiry
        "2021-07-29"

        3.
        {
        "number":10,
        "gainers_or_losers":"losers",
        "type":"indices",
        }
        
        Returns 10 gainers of nifty indices
        '''
        # ********************************* INPUT PARAMS *******************************************
        
        try:
            number = request.data.get("number", None)
            gainers_or_losers = request.data.get("gainers_or_losers", None).upper()
            gnlr_type = request.data.get("type", None).upper()
            chart = request.data.get("chart", True)

            expiry_date = None
            if gnlr_type in ["FUTURES", "FUT"]:
                expiry_date = datetime.strptime(
                    request.data.get("expiry_date", None), "%Y-%m-%d"
                ).date()
                if expiry_date < dt.datetime.now().date():
                    return Response('Past expiry is not valid')

            from_date = request.data.get("from_date", None)
            to_date = request.data.get("to_date", None)
        except Exception as e:
            return Response({"Error encountered while reading input request:\n": str(e)})

        # ********************************** INPUT PARAMS ******************************************


        # Initialising KiteFuntions object
        try:
            kf = KiteFunctions()
        except Exception as e:
            return_text = 'Error encountered # ' + e
            return Response(return_text)
        stock_df = None
        if gnlr_type in ["STOCK", "STOCKS"]:
            gnlr_type = "STOCKS"

        # Converting the date strings into date() object
        if from_date is not None:
            from_date = datetime.strptime(
                    from_date, "%Y-%m-%d"
                ).date()
        if to_date is not None:
            to_date = datetime.strptime(
                    to_date, "%Y-%m-%d"
                ).date()


        # Retrieving the gainers losers dataframe.
        # Dataframe returned would have the following columns:
        # ["prev_close", "curr_close", "diff", "percent_diff"]
        res_df = kf.get_gainers_losers_close_df(gnlr_type, expiry_date,from_date,to_date)
        debug = False
        if debug:
            print(res_df)
        # Check if "chart" parameter is True. If False simply return
        # The dataframe in json format. If True return ChartJS response.
        if not chart:
            if gainers_or_losers == "GAINERS":
                return Response(
                    dict(
                        gainers=res_df.iloc[:number, -1].to_dict()
                        if number != 0
                        else res_df[res_df.iloc[:, -1] > 0].iloc[:, -1].to_dict()
                    )
                )

            elif gainers_or_losers == "LOSERS":
                return Response(
                    dict(
                        losers=res_df.iloc[-number:, -1][::-1].to_dict()
                        if number != 0
                        else res_df[res_df.iloc[:, -1] < 0].iloc[:, -1][::-1].to_dict()
                    )
                )

            # This block would be executed when gainers_or_losers == "BOTH" 
            return Response(
                dict(
                    gainers=res_df.iloc[:number, -1].to_dict()
                    if number != 0
                    else res_df[res_df.iloc[:, -1] > 0].iloc[:, -1].to_dict(),
                    losers=res_df.iloc[-number:, -1][::-1].to_dict()
                    if number != 0
                    else res_df[res_df.iloc[:, -1] < 0].iloc[:, -1][::-1].to_dict(),
                )
            )



        ####################### chartjs ########################

        '''
        Gainers Losers ChartJS class is returned by gl_bargraph() function. 
        This function takes the following parameters:
        :param data1: list of bargraph data,
        Here it would be the list of percentages of the top gainers/losers
        :param yaxis_labels: List of labels for the corresponding bars.
        :param y_label: String label for Y-axis.
        :param top_label: String label for the top of the chart.
        :param barcolor: String Color name for the color of bar. Default is "GREEN"
        
        :param position: String position for the bars alignment. 
        Takes 'left' or 'right'. Default is 'left'. Works in opposing fashion 
        for bars with negative values (Losers).
        :param len1: Integer representing the length of 1st bardata. 
        Required for the case of "BOTH", otherwise is optional.
        :param len2: Integer representing the length of 1st bardata. 
        Required for the case of "BOTH", otherwise is optional.
        '''

        if gainers_or_losers == "GAINERS":
            NewChart = gl_bargraph(
                data1=res_df[res_df.iloc[:, -1] > 0].iloc[:number, -1].tolist()
                if number != 0
                else res_df[res_df.iloc[:, -1] > 0].iloc[:, -1].tolist(),
                yaxis_labels=res_df[res_df.iloc[:, -1] > 0]
                .iloc[
                    :number,
                ]
                .index.tolist()
                if number != 0
                else res_df[res_df.iloc[:, -1] > 0].index.tolist(),
                y_label=gnlr_type,
                top_label=gainers_or_losers,
            )()

        elif gainers_or_losers == "LOSERS":
            NewChart = gl_bargraph(
                data1=res_df[res_df.iloc[:, -1] < 0].iloc[-number:, -1][::-1].tolist()
                if number != 0
                else res_df[res_df.iloc[:, -1] < 0].iloc[:, -1][::-1].tolist(),
                yaxis_labels=res_df[res_df.iloc[:, -1] < 0]
                .iloc[
                    -number:,
                ][::-1]
                .index.tolist()
                if number != 0
                else res_df[res_df.iloc[:, -1] < 0][::-1].index.tolist(),
                y_label=gnlr_type,
                top_label=gainers_or_losers,
                barcolor="RED",
                position="right",
            )()
        else:   
            NewChart = gl_bargraph(
                data1=res_df[res_df.iloc[:, -1] > 0].iloc[:number, -1].tolist()
                + res_df[res_df.iloc[:, -1] < 0].iloc[-number:, -1][::-1].tolist()
                if number != 0
                # else res_df[res_df.iloc[:, -1] != 0].iloc[:, -1].tolist(),
                else res_df[res_df.iloc[:, -1] > 0].iloc[:, -1].tolist()
                + res_df[res_df.iloc[:, -1] < 0].iloc[:, -1][::-1].tolist(),

                yaxis_labels=res_df[res_df.iloc[:, -1] > 0]
                .iloc[
                    :number,
                ]
                .index.tolist()
                + res_df[res_df.iloc[:, -1] < 0]
                .iloc[
                    -number:,
                ][::-1]
                .index.tolist()
                if number != 0
                else res_df[res_df.iloc[:, -1] > 0].index.tolist()
                + res_df[res_df.iloc[:, -1] < 0][::-1].index.tolist(),

                y_label=gnlr_type,
                top_label="GAINERS & LOSERS",
                barcolor="BOTH",
                position="left",
                len1=number
                if number != 0
                else len(res_df[res_df.iloc[:, -1] > 0].index),
                len2=number
                if number != 0
                else len(res_df[res_df.iloc[:, -1] < 0].index),
            )()

        ####################### chartjs ########################
        return Response(json.loads(NewChart.get()))

class Gainers_Losers_OI(APIView):
    '''
        The gainers losers oi API returns the Top OI
        Gainers and Top OI Losers. 
        The expiry date is required only when
        Fetching the Gainers and Losers for Futures.

        :param number: Positive Integer for the number of records. 
                        0(Zero) returns all records.

        :param gainers_or_losers: String value. Allowed values are
        "Gainers","Losers" or "Both"

        :param chart: Boolean value. Default is True. 
        True -> Chart Js json response
        False -> DataFrame json response

        :param expiry_date: String date. 

        Example requests:

        1.
        {
        "number":5,
        "gainers_or_losers":"both",
        "expiry_date":"2021-07-29"
        }

        Returns top 5 gainersoi and losersoi for futures for the expiry
        "2021-07-29" in chartjs

        2.
        {
        "number":0,
        "gainers_or_losers":"losers",
        "expiry_date":"2021-07-29"
        }
        Returns top all losers for futures for the expiry
        "2021-07-29" in chartjs

        2.
        {
        "number":0,
        "gainers_or_losers":"losers",
        "expiry_date":"2021-07-29",
        "chart":false
        }
        Returns top all losers for futures for the expiry
        "2021-07-29" in dataframe json response
        '''
    def post(self, request):
        # ********************************* INPUT PARAMS *******************************************
        try:
            number = request.data.get("number", None)
            gainers_or_losers = request.data.get("gainers_or_losers", None).upper()
            chart = request.data.get("chart", True)
            expiry_date = datetime.strptime(
                request.data.get("expiry_date", None), "%Y-%m-%d"
            ).date()
            if expiry_date < dt.datetime.now().date():
                return Response('Past expiry is not valid')
        except Exception as e:
            return Response({"Error encountered while reading input request:\n": str(e)})

        # ********************************** INPUT PARAMS ******************************************

        # Initialising KiteFuntions object
        try:
            kf = KiteFunctions()
        except Exception as e:
            return_text = 'Error encountered # ' + e
            return Response(return_text)

        # Filtering the instruments df to get FUTURES instruments
        stock_df = kf.master_instruments_df[
            (kf.master_instruments_df["segment"] == "NFO-FUT")
            & (kf.master_instruments_df["expiry"] == expiry_date)
            & ~(
                kf.master_instruments_df["name"].isin(
                    ["NIFTY", "BANKNIFTY", "FINNIFTY"]
                )
            )
        ]
        

        # Appending "NFO:" to the tradingsymbol in order to pass the instruments in quote().
        # Example: "ACC21AUGFUT" -- > "NFO:ACC21AUGFUT"
        stock_df = pd.concat(
            [
                stock_df,
                stock_df.loc[:, "tradingsymbol"].apply(lambda x: "NFO:" + x),
            ],
            axis=1,
        )
        stock_df.columns.values[-1] = "exchange_tradingsymbol"

        # Fetching the last traded date from quote()
        ltd = kf.kite.quote(["NSE:NIFTY 50"])["NSE:NIFTY 50"]["timestamp"].date()
        res_df = None

        # If today is also the last traded date i.e. markets are open
        if date.today() == ltd:

            # Get previous days futures dataframe
            res_df = kf.ka.pg.get_postgres_data_df_with_condition(
                table_name="stock_futures_history_day",
                where_condition="where CAST(last_update AS DATE) = '{}' and CAST(expiry_date as DATE) = '{}'".format(
                    (date.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    expiry_date.strftime("%Y-%m-%d"),
                ),
            )

            # Appending "NFO:" to the index in order to pass the instruments in quote().
            # Example: "ACC21AUGFUT" -- > "NFO:ACC21AUGFUT"
            res_df.index = res_df.apply(lambda x: "NFO:" + x["ticker"], axis=1)
            res_df.columns.values[-3] = "past_oi"


            # Get todays futures data from quote() in the form of dictionary,
            # pass the dictionary in pd.DataFrame to convert it to a DataFrame,
            # Combine previous days futures df with todays futures df using pd.concat(),
            # apply the formula ( (current oi - prev oi) / prev oi ) * 100
            res_df = pd.concat(
                [
                    res_df,
                    pd.DataFrame(
                        kf.kite.quote(stock_df["exchange_tradingsymbol"].tolist())
                    ).transpose(),
                ],
                axis=1,
            ).apply(
                lambda x: ((x["oi"] - x["past_oi"]) / x["past_oi"]) * 100
                if x["past_oi"] != 0
                else None,
                axis=1,
            )

            # Remove "NFO:" from the index 
            # Example "NFO:ACC21AUGFUT" -- > "ACC21AUGFUT"
            res_df.index = (
                res_df.index.to_series().apply(lambda x: x.split(":")[1]).tolist()
            )

        # If today is not last traded date i.e. a holiday/weekend
        else:
            # Get day before last traded date's futures dataframe
            res_df = kf.ka.pg.get_postgres_data_df_with_condition(
                table_name="stock_futures_history_day",
                where_condition="where CAST(last_update AS DATE) "
                + "= (SELECT CAST (max(last_update) AS DATE) from public.stock_futures_history_day"
                + " WHERE CAST(last_update AS DATE) < '{}') and CAST(expiry_date as DATE) = '{}'".format(
                    ltd.strftime("%Y-%m-%d"), expiry_date.strftime("%Y-%m-%d")
                ),
            )
            res_df.columns.values[-3] = "past_oi"
            res_indx = res_df["ticker"]


            # Get Last traded date's dataframe from the database
            # Combine previous days futures df with todays futures df using pd.concat(),
            # apply the formula ( (current oi - prev oi) / prev oi ) * 100
            res_df = pd.concat(
                [
                    res_df,
                    kf.ka.pg.get_postgres_data_df_with_condition(
                        table_name="stock_futures_history_day",
                        where_condition="where CAST(last_update AS DATE) = '{}' and CAST(expiry_date as DATE) = '{}'".format(
                            ltd.strftime("%Y-%m-%d"), expiry_date.strftime("%Y-%m-%d")
                        ),
                    ),
                ],
                axis=1,
            ).apply(
                lambda x: ((x["oi"] - x["past_oi"]) / x["past_oi"]) * 100
                if x["past_oi"] != 0
                else None,
                axis=1,
            )
            res_df.index = res_indx

        # Drop the 'NA' values and sort the dataframe to get top gainers and losers
        res_df.dropna(inplace=True)
        res_df.sort_values(ascending=False, inplace=True)

        res_df = res_df.round(2)

        # Check if "chart" parameter is True. If False simply return
        # The dataframe in json format. If True return ChartJS response.
        if not chart:
            if gainers_or_losers == "GAINERS":
                return Response(
                    dict(
                        gainers=res_df[res_df > 0]
                        .iloc[
                            :number,
                        ]
                        .to_dict()
                        if number != 0
                        else res_df[res_df > 0].to_dict()
                    )
                )

            elif gainers_or_losers == "LOSERS":
                return Response(
                    dict(
                        losers=res_df[res_df < 0].iloc[-number:][::-1].to_dict()
                        if number != 0
                        else res_df[res_df < 0][::-1].to_dict()
                    )
                )

            # This block would be executed when gainers_or_losers == "BOTH" 
            return Response(
                dict(
                    gainers=res_df[res_df > 0]
                    .iloc[
                        :number,
                    ]
                    .to_dict()
                    if number != 0
                    else res_df[res_df > 0].to_dict(),
                    losers=res_df[res_df < 0].iloc[-number:][::-1].to_dict()
                    if number != 0
                    else res_df[res_df < 0][::-1].to_dict(),
                )
            )

        ####################### chartjs ########################

        '''
        Gainers Losers ChartJS class is returned by gl_bargraph() function. 
        This function takes the following parameters:
        :param data1: list of bargraph data,
        Here it would be the list of percentages of the top gainers/losers
        :param yaxis_labels: List of labels for the corresponding bars.
        :param y_label: String label for Y-axis.
        :param top_label: String label for the top of the chart.
        :param barcolor: String Color name for the color of bar. Default is "GREEN"
        
        :param position: String position for the bars alignment. 
        Takes 'left' or 'right'. Default is 'left'. Works in opposing fashion 
        for bars with negative values (Losers).
        :param len1: Integer representing the length of 1st bardata. 
        Required for the case of "BOTH", otherwise is optional.
        :param len2: Integer representing the length of 1st bardata. 
        Required for the case of "BOTH", otherwise is optional.
        '''

        if gainers_or_losers == "GAINERS":
            NewChart = gl_bargraph(
                data1=res_df[res_df > 0]
                .iloc[
                    :number,
                ]
                .tolist()
                if number != 0
                else res_df[res_df > 0].tolist(),
                yaxis_labels=res_df[res_df > 0]
                .iloc[
                    :number,
                ]
                .index.tolist()
                if number != 0
                else res_df[res_df > 0].index.tolist(),
                y_label="FUTURES",
                top_label=gainers_or_losers + " OI",
            )()

        elif gainers_or_losers == "LOSERS":
            NewChart = gl_bargraph(
                data1=res_df[res_df < 0].iloc[-number:][::-1].tolist()
                if number != 0
                else res_df[res_df < 0][::-1].tolist(),
                yaxis_labels=res_df[res_df < 0].iloc[-number:][::-1].index.tolist()
                if number != 0
                else res_df[res_df < 0][::-1].index.tolist(),
                y_label="FUTURES",
                top_label=gainers_or_losers + " OI",
                barcolor="RED",
                position="right",
            )()
        else:
            NewChart = gl_bargraph(
                data1=res_df[res_df > 0]
                .iloc[
                    :number,
                ]
                .tolist()
                + res_df[res_df < 0].iloc[-number:][::-1].tolist()
                if number != 0
                else res_df[res_df > 0].tolist()
                + res_df[res_df < 0][::-1].tolist(),

                yaxis_labels=res_df[res_df > 0]
                .iloc[
                    :number,
                ]
                .index.tolist()
                + res_df[res_df < 0].iloc[-number:][::-1].index.tolist()
                if number != 0
                else res_df[res_df > 0].index.tolist()
                + res_df[res_df < 0][::-1].index.tolist(),

                y_label="FUTURES",
                top_label="GAINERS OI & LOSERS OI",
                barcolor="BOTH",
                position="left",
                len1=number if number != 0 else len(res_df[res_df > 0].index),
                len2=number if number != 0 else len(res_df[res_df < 0].index),
            )()

        ####################### chartjs ########################
        return Response(json.loads(NewChart.get()))

class Get_Cumulative_OI(APIView):
    def post(self , request):
        logging.debug(pformat('\n\nBeginning of OpenInterest api with new quote logic...'))


        logging.debug(pformat("Data in Post is # "))
        logging.debug(pformat(request.data))

        ##################Input parameters #####################
        
        ticker = request.data.get('ticker')
        expiry_date_str = request.data.get('expiry_date')
        date = request.data.get('date')
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        if expiry_date < dt.datetime.now().date():
            return Response('Past expiry is not valid')

        ##################Input parameters #####################

        oi = OIAnalysis()

        if date:
            oi_df = oi.get_oi_df_anyday(ticker , expiry_date , date)
        else:
            oi_df = oi.get_oi_df_today(ticker , expiry_date )

        ####################### chartjs ########################

        # breakpoint()
        NewChart = coi_bargraph(
            data1=[oi_df['calloi'].sum().item(),oi_df['putoi'].sum().item()],
            yaxis_labels= [],
            y_label="Open Interest",
            top_label="Cumulative OI",
            barcolor="BOTH",
            len1=1,
            len2=1,
            bar_type="Vertical",
            xaxis_labels=['Call OI','Put OI']
        )()
        
        ####################### chartjs ########################
        return Response(json.loads(NewChart.get()))
    
    def get(self , request):
        return Response({"ticker":"NIFTY","expiry_date":"2021-05-27"})

class Cash_Futures_Arbitrage(APIView):
    '''
    Sample Data in Post
    {   
        "expiry":"CURRENT" , //"near", "far"
        "chart" : true
    }
    '''
    def post(self,request):

        # ********************************* INPUT PARAMS *******************************************
        try:
            chart = request.data.get("chart", True)
            expiry = request.data.get("expiry","current").upper()
        except Exception as e:
            return Response({"Error encountered while reading input request:\n": str(e)})

        # ********************************** INPUT PARAMS ******************************************
        kf = KiteFunctions()
        exclude_list = ["NIFTY","FINNIFTY","BANKNIFTY"]

        if expiry == "CURRENT":
            stock_df = kf.master_instruments_df[(kf.master_instruments_df["segment"]=="NFO-FUT")
                                 & ~ (kf.master_instruments_df["name"].isin(exclude_list))
                                 & (kf.master_instruments_df["expiry"]==kf.master_instruments_df[
                                     (kf.master_instruments_df["segment"]=="NFO-FUT")
                                      & ~ (kf.master_instruments_df["name"].isin(exclude_list))]["expiry"].min())]
        elif expiry == "NEAR":
            stock_df = kf.master_instruments_df[(kf.master_instruments_df["segment"]=="NFO-FUT")
                                 & ~ (kf.master_instruments_df["name"].isin(exclude_list))
                                 & ~(kf.master_instruments_df["expiry"]==kf.master_instruments_df[
                                     (kf.master_instruments_df["segment"]=="NFO-FUT")
                                      & ~ (kf.master_instruments_df["name"].isin(exclude_list))]["expiry"].min())
                                 & ~(kf.master_instruments_df["expiry"]==kf.master_instruments_df[
                                     (kf.master_instruments_df["segment"]=="NFO-FUT")
                                      & ~ (kf.master_instruments_df["name"].isin(exclude_list))]["expiry"].max())
                                 & ~ (kf.master_instruments_df["exchange_token"]==0)]

        elif expiry == "FAR":
            stock_df = kf.master_instruments_df[(kf.master_instruments_df["segment"]=="NFO-FUT")
                                 & ~ (kf.master_instruments_df["name"].isin(exclude_list))
                                 & (kf.master_instruments_df["expiry"]==kf.master_instruments_df[
                                     (kf.master_instruments_df["segment"]=="NFO-FUT")
                                      & ~ (kf.master_instruments_df["name"].isin(exclude_list))]["expiry"].max())]

        stock_df = pd.concat([stock_df,stock_df.loc[:,"tradingsymbol"].apply(lambda x:"NFO:"+x)],axis=1)

        stock_df.columns.values[-1] = "exchange_tradingsymbol"

        stock_df["exchange_name"] = stock_df.apply(lambda x:"NSE:"+x["name"],axis=1)

        stock_df.reset_index(drop=True,inplace=True)

        stock_df = pd.concat([stock_df,pd.DataFrame(kf.kite.quote(stock_df[
            "exchange_name"].tolist())).transpose()[
            'last_price'].reset_index(drop=True)],axis=1)

        stock_df.columns.values[-1] = "stock_price"

        stock_df = pd.concat([stock_df,pd.DataFrame(kf.kite.quote(stock_df[
            "exchange_tradingsymbol"].tolist())).transpose()[
            'last_price'].reset_index(drop=True)],axis=1)

        stock_df.columns.values[-1] = "futures_price"

        stock_df = stock_df.apply(lambda x:[
            x['name'],
            x['stock_price'],
            x['futures_price'],
            x['futures_price'] - x['stock_price'],
            ((x['futures_price'] - x['stock_price']) / x['stock_price'])*100
        ]
            if x['stock_price'] !=0 else
            [
            x['name'],
            x['stock_price'],
            x['futures_price'],
            None,
            None],axis=1)

        stock_df = pd.DataFrame(stock_df.to_list(),columns = ["FNO Stocks","Stock Price",
            "Futures Price","Price Change","Difference in %"])

        stock_df.index = stock_df['FNO Stocks']

        stock_df.drop(labels=["FNO Stocks"],axis=1,inplace=True)

        stock_df = stock_df.round(2)
        stock_df.sort_values(by="Difference in %",ascending=False, inplace=True)
        stock_df = stock_df[~(stock_df["Futures Price"] == 0)]
        if not chart:
            return Response(stock_df.to_dict("index"))
        else:
            ####################### chartjs ########################
            cfa_bargraph = gl_bargraph

            NewChart = cfa_bargraph(
                data1=stock_df["Difference in %"].tolist(),
                yaxis_labels= stock_df.index.tolist(),
                y_label="Stocks",
                top_label="Cash Futures Arbitrage",
                barcolor="BOTH",
                position="left",
                len1=len(stock_df[stock_df["Difference in %"] > 0].index),
                len2=len(stock_df[stock_df["Difference in %"] <= 0].index),
            )()
            ####################### chartjs ########################
            return Response(json.loads(NewChart.get()))

    def get(self , request):
        post_data = {   "expiry":"CURRENT" ,
                        "chart" : "true"
        }
        return Response(post_data)

class Cumulative_Prices(APIView):
    def post(self , request):
        debug=True
        ticker = request.data.get('ticker').upper()
        expiry_date_str = request.data.get('expiry_date')
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        if expiry_date < dt.datetime.now().date():
            return Response('Past expiry is not valid')
        kf =  KiteFunctions()
        
        filter_df = kf.master_instruments_df[
            (kf.master_instruments_df['name']        == ticker)
        & (kf.master_instruments_df['expiry']      == expiry_date)
        & (kf.master_instruments_df['segment']     == 'NFO-OPT')
        ]

        filter_instruments_df = filter_df[['instrument_token', 'strike', 'tradingsymbol', 'instrument_type']].copy()
        filter_instruments_df.reset_index(drop=True, inplace=True)
        filter_instruments_df.sort_values(by=['strike'], inplace=True)
        instruments_list = filter_instruments_df['instrument_token'].to_list()

        # if self.debug:
        #     print("Here are instruments List to fetch OI... ")
        #     print(instruments_list)

        quote = kf.ka.kite.quote(instruments_list)
        test =  kf.ka.kite.quote(13169154)
        print(test)
        
        ltp_df = pd.DataFrame(columns=['strike', 'callltp', 'putltp'])
        ltp_df['strike'] = kf.get_strike_prices(ticker=ticker, expiry_date=expiry_date)
        ltp_df['callltp'] = 0.0
        ltp_df['putltp'] = 0.0
        ltp_df.set_index(keys='strike', inplace=True)

        for index in filter_instruments_df.index:
            
            instrument_token = str(filter_instruments_df['instrument_token'][index])
            strike_price = filter_instruments_df['strike'][index]
            ltp_value = quote[instrument_token]['last_price']
            # print(ltp_value , index)
            if filter_instruments_df['instrument_type'][index] == "CE":
                ltp_df['callltp'][strike_price] = ltp_value
            else:
                ltp_df['putltp'][strike_price] = ltp_value
        if debug:
            print(ltp_df)
            ltp_df.to_csv('ltp_df.csv')


        NewChart = coi_bargraph(
            data1=[round(ltp_df['callltp'].sum() ,2).item(),round(ltp_df['putltp'].sum().item() ,2)],
            yaxis_labels= [],
            y_label="Last Traded Price",
            top_label="Cumulative Price",
            barcolor="BOTH",
            len1=1,
            len2=1,
            bar_type="Vertical",
            xaxis_labels=['Call LTP','Put LTP']
        )()
        
        ####################### chartjs ########################
        return Response(json.loads(NewChart.get()))
        
    def get(self , request):
        return Response({"ticker":"NIFTY","expiry_date":"2021-05-27"})

class Fno_Stock_Adv_Decl(APIView):
    def post(self,request):

        # ********************************* INPUT PARAMS *******************************************
        try:
            chart = request.data.get("chart", True)
        except Exception as e:
            return Response({"Error encountered while reading input request:\n": str(e)})

        # ********************************** INPUT PARAMS ******************************************
        try:
            kf = KiteFunctions()
        except Exception as e:
            return Response({"Error encountered :\n": str(e)})

        # Retrieving the gainers losers dataframe.
        # Dataframe returned would have the following columns:
        # ["prev_close", "curr_close", "diff", "percent_diff"]
        res_df = kf.get_gainers_losers_close_df("STOCKS")

        if not chart:
            return Response({
                "Advances":res_df[res_df.iloc[:, -1] > 0].iloc[:, -1].count().item(),
                "Declines":res_df[res_df.iloc[:, -1] <= 0].iloc[:, -1].count().item()})
        else:

            NewChart = gl_piechart(data1 = [
            res_df[res_df.iloc[:, -1] <= 0].iloc[:, -1].count().item(),
            res_df[res_df.iloc[:, -1] > 0].iloc[:, -1].count().item()],
            labels = ["Declines","Advances"])()
            return Response(json.loads(NewChart.get()))
