from django.urls import path
from . import views

urlpatterns = [
    # Аутентификация
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    
    # Главная страница
    path('', views.home, name='home'),
    
    # Номенклатура
    path('nomenclature/', views.nomenclature_list, name='nomenclature_list'),
    path('nomenclature/create/', views.create_nomenclature, name='create_nomenclature'),
    path('nomenclature/edit/<int:pk>/', views.edit_nomenclature, name='edit_nomenclature'),
    path('nomenclature/delete/<int:pk>/', views.delete_nomenclature, name='delete_nomenclature'),
    path('nomenclature/<int:pk>/send-to-intbus/', views.send_nomenclature_to_intbus, name='send_nomenclature_to_intbus'),
    
    # LSI (Логическая структура изделия)
    path('lsi/', views.lsi_list, name='lsi_list'),
    path('lsi/create/', views.create_lsi, name='create_lsi'),
    path('lsi/edit/<int:pk>/', views.edit_lsi, name='edit_lsi'),
    path('lsi/delete/<int:pk>/', views.delete_lsi, name='delete_lsi'),
    path('lsi/<int:pk>/send-to-intbus/', views.send_lsi_to_intbus, name='send_lsi_to_intbus'),
    
    # Экспорт/Импорт
    path('export-excel/', views.export_to_excel, name='export_excel'),
    path('import-excel/', views.import_from_excel, name='import_excel'),
    
    # API для интеграции
    path('api/sync-from-intbus/', views.receive_data_from_intbus, name='receive_data_from_intbus'),
] 