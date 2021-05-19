from django.contrib import admin
from django.urls import path
from . import views
from django.conf.urls import url

urlpatterns = [
   url( r'^openinterest/?$', views.Open_Interst_Chart_API_View.as_view(),name ='openinterest') ,
   url( r'^maxpainhistory/?$', views.MaxPain_History_Chart_API_View.as_view(),name ='maxpainhistory') ,
   url( r'^pcr/?$', views.PCR_Day_API_View.as_view(),name ='pcr') ,
   url( r'^pcrhistory/?$', views.PCR_History_Chart_API_View.as_view(),name ='pcrhistory') ,
   url( r'$', views.Home, name ='home'),
]
