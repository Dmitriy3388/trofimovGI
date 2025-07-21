from django.urls import path
from . import views


app_name = 'ordercart'

urlpatterns = [
    path('', views.ordercart_detail, name='ordercart_detail'),
    path('add/<int:material_id>/', views.ordercart_add, name='ordercart_add'),
    path('remove/<int:material_id>/', views.ordercart_remove,name='ordercart_remove'),
]