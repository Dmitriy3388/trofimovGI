from django.urls import path
from . import views
from .views import MaterialListView


app_name = 'mebel'

urlpatterns = [
    path('', views.main_dashboard, name='main_dashboard'),
    path('materials', MaterialListView.as_view(), name='material_list'),
    path('<int:material_id>/write-off/', views.material_write_off, name='material_write_off'),
    path('<int:material_id>/receipt/', views.material_receipt, name='material_receipt'),
    path('<slug:category_slug>/', views.material_list,
         name='material_list_by_category'),
    path('<int:id>/<slug:slug>/', views.material_detail,
         name='material_detail'),
]