from django.urls import path
from . import views

urlpatterns = [
    # Аутентификация
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    
    # Главная страница
    path('', views.home, name='home'),
    
    # Номенклатура (только просмотр)
    path('nomenclature/', views.nomenclature_list, name='nomenclature_list'),
    
    # LSI (Логическая структура изделия) (только просмотр)
    path('lsi/', views.lsi_list, name='lsi_list'),
    
    # URLs для отправки данных в TeamCenter и ATOM
    path('nomenclature/<int:pk>/send-to-teamcenter/', views.send_nomenclature_to_teamcenter, name='send_nomenclature_to_teamcenter'),
    path('nomenclature/<int:pk>/send-to-atom/', views.send_nomenclature_to_atom, name='send_nomenclature_to_atom'),
    path('lsi/<int:pk>/send-to-teamcenter/', views.send_lsi_to_teamcenter, name='send_lsi_to_teamcenter'),
    path('lsi/<int:pk>/send-to-atom/', views.send_lsi_to_atom, name='send_lsi_to_atom'),
    
    # Страница маппинга полей
    path('mapping/', views.mapping_view, name='mapping'),
    path('apply-mapping/', views.apply_mapping_view, name='apply_mapping'),
] 