from sqlalchemy import create_engine
import datetime as dt
from datetime import datetime
import pandas as pd

from classes import KiteFunctions , OIAnalysis , PostgreSQLOperations

ticker ="NIFTY"
expiry_date_str="2021-07-29"
expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()

connection_string = 'postgresql://doadmin:or5ka898vk8r1wdi@srifintech-db-do-user-8454140-0.b.db.ondigitalocean.com:25060/defaultdb'
db = create_engine(connection_string)

KF =  KiteFunctions()
OI =  OIAnalysis()
PO =  PostgreSQLOperations()


today = dt.datetime.now().date()
from_date = today - dt.timedelta(10)
ltd = KF.get_last_traded_dates(ticker)['last_traded_date']

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
    oi_df = OI.get_oi_df_today(ticker , expiry_date )
    call_oi  = oi_df['calloi'].sum()
    put_oi = oi_df['putoi'].sum()
    
    # pcr value zero if put_oi/call_oi is 0 (handeling ZeroDivisionError Exception)
    if put_oi == 0 or call_oi == 0:
        pcr = 0   
    else: 
        pcr = round(float(put_oi / call_oi),2)
    spot_price = KF.get_ltp(ticker)
    data.append([today ,pcr , spot_price])
    data_temp = get_data_db()
    data += data_temp

main_df = pd.DataFrame( data =data , columns=['date','pcr_value','price'])

print(main_df)