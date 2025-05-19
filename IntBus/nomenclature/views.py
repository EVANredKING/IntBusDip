from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.forms.models import model_to_dict
from .models import Nomenclature, LSI
from .services import data_parser, integrations
import logging

# Настройка логгера
logger = logging.getLogger(__name__)

# Аутентификация и регистрация
def login_view(request):
    next_url = request.GET.get('next', 'home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        next_param = request.POST.get('next', 'home')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect(next_param if not next_param.startswith('/') else next_param)
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    return render(request, 'nomenclature/login.html', {'next': next_url})

def logout_view(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Аккаунт создан для {form.cleaned_data.get("username")}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'nomenclature/register.html', {'form': form})

# Главная страница
@login_required
def home(request):
    context = {
        'nomenclature_count': Nomenclature.objects.count(),
        'lsi_count': LSI.objects.count()
    }
    return render(request, 'nomenclature/home.html', context)

# Работа с номенклатурой и LSI
@login_required
def nomenclature_list(request):
    return render(request, 'nomenclature/nomenclature_list.html', 
                 {'nomenclatures': Nomenclature.objects.all()})

@login_required
def lsi_list(request):
    return render(request, 'nomenclature/lsi_list.html', 
                 {'lsi_items': LSI.objects.all()})

# Функции для отправки данных
@login_required
def send_nomenclature_to_teamcenter(request, pk):
    return integrations.send_to_target(request, 'nomenclature', pk, 'TEAMCENTER')

@login_required
def send_nomenclature_to_atom(request, pk):
    return integrations.send_to_target(request, 'nomenclature', pk, 'ATOM')

@login_required
def send_lsi_to_teamcenter(request, pk):
    return integrations.send_to_target(request, 'lsi', pk, 'TEAMCENTER')

@login_required
def send_lsi_to_atom(request, pk):
    return integrations.send_to_target(request, 'lsi', pk, 'ATOM')

# Страницы маппинга
@login_required
def mapping_view(request):
    source_id = request.GET.get('source_id')
    source_type = request.GET.get('source_type', 'nomenclature')
    target = request.GET.get('target', '').upper()
    
    if not source_id or not target:
        messages.error(request, "Отсутствуют обязательные параметры")
        return redirect('home')
    
    try:
        context = integrations.prepare_mapping_context(source_id, source_type, target)
        
        # Добавляем в контекст сохраненные маппинги из cookies, если они есть
        cookie_name = f"mapping_{source_type}_{target}"
        saved_mapping = request.COOKIES.get(cookie_name)
        if saved_mapping:
            try:
                import json
                saved_mapping = json.loads(saved_mapping)
                # Преобразуем в строку JSON для безопасной передачи в шаблон
                context['saved_mapping'] = json.dumps(saved_mapping)
                logger.info(f"Загружен сохраненный маппинг из cookies: {cookie_name}")
            except Exception as e:
                logger.error(f"Ошибка при загрузке маппинга из cookies: {str(e)}")
        
        return render(request, 'nomenclature/mapping.html', context)
    except Exception as e:
        logger.error(f"Ошибка при формировании страницы маппинга: {str(e)}", exc_info=True)
        messages.error(request, f"Ошибка при формировании страницы маппинга: {str(e)}")
        return redirect('home')

@login_required
def apply_mapping_view(request):
    """Обработка маппинга полей и отправка данных в целевую систему"""
    if request.method != 'POST':
        return redirect('home')
        
    # Получаем параметры из POST запроса
    source_id = request.POST.get('source_id')
    source_type = request.POST.get('source_type', 'nomenclature')
    target = request.POST.get('target')
    
    # Собираем маппинг полей из формы
    field_mapping = {}
    for field, value in request.POST.items():
        if field.startswith('field_mapping[') and field.endswith(']') and value:
            source_field = field[len('field_mapping['):-1]
            field_mapping[source_field] = value
    
    # Проверяем обязательные параметры
    if not source_id or not target:
        messages.error(request, "Отсутствуют обязательные параметры")
        return redirect('home')
    
    try:
        # Применяем маппинг и отправляем данные
        response = integrations.apply_mapping(source_id, source_type, target, field_mapping)
        
        # Подготавливаем ответ для возврата
        redirect_url = 'nomenclature_list' if source_type == 'nomenclature' else 'lsi_list'
        response_obj = redirect(redirect_url)
        
        # Сохраняем маппинг в cookies
        if field_mapping:
            import json
            cookie_name = f"mapping_{source_type}_{target}"
            response_obj.set_cookie(
                cookie_name, 
                json.dumps(field_mapping), 
                max_age=60*60*24*365  # 1 год
            )
            logger.info(f"Маппинг сохранен в cookies: {cookie_name}")
        
        # Обрабатываем результат
        if isinstance(response, dict) and response.get('success'):
            messages.success(request, f"Данные успешно отправлены в {target}!")
        else:
            messages.error(request, f"Ошибка при отправке данных: {getattr(response, 'content', response.get('message', 'Неизвестная ошибка'))}")
        
        return response_obj
        
    except Exception as e:
        logger.error(f"Ошибка при обработке маппинга: {str(e)}", exc_info=True)
        messages.error(request, f"Ошибка при обработке маппинга: {str(e)}")
    
    # После обработки перенаправляем пользователя на список соответствующих объектов
    return redirect('nomenclature_list' if source_type == 'nomenclature' else 'lsi_list')
