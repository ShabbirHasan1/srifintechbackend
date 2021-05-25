from django.contrib import admin
from django.urls import path
from . import views
from django.conf.urls import url

urlpatterns = [
   url( r'^openinterest/?$', views.Open_Interst_Chart_API_View.as_view(),name ='openinterest') ,
   url( r'^maxpainhistory/?$', views.MaxPain_History_Chart_API_View.as_view(),name ='maxpainhistory') ,
   url( r'^pcr/?$', views.PCR_Day_API_View.as_view(),name ='pcr') ,
   url( r'^pcrhistory/?$', views.PCR_History_Chart_API_View.as_view(),name ='pcrhistory') ,
   url( r'^login/?$', views.Login.as_view(),name ='login') ,
   url( r'^kitelogin/?$', views.Kite_Login.as_view(),name ='kitelogin') ,
   url( r'^montecarlo/?$', views.Get_MonteCarlo_Simulation.as_view(),name ='montecarlo') ,
   url( r'^kiteauth/?$', views.Get_KiteAuth.as_view(),name ='kiteauth') ,
   url( r'^ltp/?$', views.Get_ltp_ticker.as_view(),name ='ltp') ,
   url( r'^multistrikeoi/?$', views.Get_Multistrike_OIchart.as_view(),name ='multistrikeoi') ,
   url( r'^multistrikeoichange/?$', views.Get_Multistrike_OIchange.as_view(),name ='multistrikeoichange') ,
   url( r'^oichange/?$', views.Get_OIchange_Chart.as_view(),name ='oichange') ,
   url( r'^maxpain/?$', views.Get_Maxpain_Chart.as_view(),name ='maxpain') , 
   url( r'^straddleprices/?$', views.Get_Straddle_Prices.as_view(),name ='straddleprices') , 
   url( r'^strangleprices/?$', views.Get_Strangle_Prices.as_view(),name ='strangleprices') , 
   url( r'$', views.Home, name ='home'),
]
