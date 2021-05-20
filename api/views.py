# import sys
# sys.path.append('.')
from django.shortcuts import render
import logging
from pprint import pformat
import datetime as dt
from datetime import datetime
from pychartjs import BaseChart, ChartType, Color, Options   
from sqlalchemy import create_engine

from api.classes import KiteFunctions , OIAnalysis , PostgreSQLOperations
from api.chartjs_classes import *
import pandas as pd

from rest_framework.views import APIView
from rest_framework.response import Response
import json


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
        # logging.debug(pformat(content))

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

        chart = json.loads(ChartJSON_str)
      
        return Response(chart)

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
        chart = ChartJSON_json
        print(ChartJSON_json)
        return Response(chart)
             
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

        pcr_value = {'pcr':pcr}
        pcr_json = json.dumps(pcr_value)
        pcr_json = json.loads(pcr_json)

        return Response(pcr_json)
    def get(self , request):
        return Response({"ticker":"NIFTY","expiry_date":"2021-05-27"})


class PCR_History_Chart_API_View(APIView):
    def post(self , request):
        ticker = request.data.get('ticker')
        expiry_date_str = request.data.get('expiry_date')
        print('\t\t\t' + ticker)
        print('\t\t\t' + expiry_date_str)

        logging.debug(pformat("Data in Post is # "))
       
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
        chart = ChartJSON_json
        print(ChartJSON_json)
        return Response(chart)

        

    def get(self , request):
        return Response({"ticker":"NIFTY","expiry_date":"2021-05-27"})