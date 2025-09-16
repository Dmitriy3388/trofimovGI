from django.urls import path
from . import views
from .views import MaterialListView

app_name = 'mebel'

urlpatterns = [

    path('', views.main_dashboard, name='main_dashboard'),
    path('create/', views.material_create, name='material_create'),
    path('materials/', MaterialListView.as_view(), name='material_list'),  # Изменили с 'materials' на 'materials/'
    path('refresh-materials/', views.refresh_materials, name='refresh_materials'),
    path('<int:material_id>/write-off/', views.material_write_off, name='material_write_off'),
    path('<int:material_id>/receipt/', views.material_receipt, name='material_receipt'),
    path('<int:material_id>/edit/', views.material_edit, name='material_edit'),  # Новый URL
    path('<slug:category_slug>/', MaterialListView.as_view(), name='material_list_by_category'),  # Используем MaterialListView
    path('<int:id>/<slug:slug>/', views.material_detail, name='material_detail'),

]