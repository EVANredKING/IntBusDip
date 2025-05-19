from django.urls import path
from . import views

urlpatterns = [
    path('api/sync/', views.sync_data, name='sync_data'),
    path('api/sync', views.sync_data, name='sync_data_no_slash'),  # путь без завершающего слеша
    path('api/csrf-token/', views.get_csrf_token, name='get_csrf_token'),  # эндпоинт для получения CSRF-токена
    path('api/send-to-atom/', views.send_to_atom, name='send_to_atom'),
    path('api/send-to-teamcenter/', views.send_to_teamcenter, name='send_to_teamcenter'),
    path('api/get-mapping-table/', views.get_mapping_table, name='get_mapping_table'),
    path('api/check-connection/', views.check_connection, name='check_connection'),  # новый эндпоинт для проверки соединения
    path('api/apply-mapping/', views.apply_mapping, name='apply_mapping'),  # новый эндпоинт для применения маппинга полей
    path('api/direct-send/', views.direct_send_to_target, name='direct_send'),  # новый эндпоинт для прямой отправки данных с указанием отправителя
    path('api/teamcenter-lsi/', views.teamcenter_lsi_sync, name='teamcenter_lsi_sync'),  # специальный эндпоинт для LSI данных от TeamCenter
] 