from django.urls import path
from . import views
from .views import MaterialListView

app_name = 'mebel'

urlpatterns = [
    path('recalculate-balances/', views.recalculate_balances, name='recalculate_balances'),
    # НОВЫЕ ПУТИ ДЛЯ ОПЕРАЦИЙ - добавьте эти строки
    path('operations/', views.operations_list, name='operations_list'),
    path('operations/<int:operation_id>/edit/', views.operation_edit, name='operation_edit'),
    path('operations/<int:operation_id>/', views.operation_detail, name='operation_detail'),
    path('', views.main_dashboard, name='main_dashboard'),
    path('create/', views.material_create, name='material_create'),
    path('materials/', MaterialListView.as_view(), name='material_list'),  # Изменили с 'materials' на 'materials/'
    path('refresh-materials/', views.refresh_materials, name='refresh_materials'),
    path('<int:material_id>/write-off/', views.material_write_off, name='material_write_off'),
    path('<int:material_id>/receipt/', views.material_receipt, name='material_receipt'),
    path('<int:material_id>/edit/', views.material_edit, name='material_edit'),  # Новый URL
    path('<slug:category_slug>/', MaterialListView.as_view(), name='material_list_by_category'),  # Используем MaterialListView
    path('<int:id>/<slug:slug>/', views.material_detail, name='material_detail'),
    path('supplier/create-modal/', views.supplier_create_modal, name='supplier_create_modal'),
    path('material-chart-data/<int:material_id>/', views.material_daily_chart_data, name='material_chart_data'),
    path('material-autocomplete/', views.material_autocomplete, name='material_autocomplete'),
    path('material/<int:material_id>/operations/', views.material_operations, name='material_operations'),



]