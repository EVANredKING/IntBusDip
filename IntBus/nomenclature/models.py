from django.db import models

class BaseIntegrationModel(models.Model):
    """Базовая модель для интеграционных объектов"""
    apikey = models.CharField(max_length=255, default="default_apikey")
    sender = models.CharField(max_length=255, default="intbus")
    data = models.TextField(default="{}")
    name = models.CharField(max_length=255, null=True, blank=True, help_text="Имя объекта, также используется как NAME в TeamCenter")
    code = models.CharField(max_length=100, null=True, blank=True, help_text="Код объекта")
    sent_to_atom = models.BooleanField(default=False)
    sent_to_teamcenter = models.BooleanField(default=False)
    
    class Meta:
        abstract = True

class Nomenclature(BaseIntegrationModel):
    """Модель для хранения номенклатуры"""
    def __str__(self):
        return f"Nomenclature {self.id}" + (f" - {self.name}" if self.name else f" from {self.sender}")

class LSI(BaseIntegrationModel):
    """Модель для хранения логической структуры изделия"""
    def __str__(self):
        return f"LSI {self.id}" + (f" - {self.name}" if self.name else f" from {self.sender}")

class TeamCenterLSI(models.Model):
    """
    Специальная модель для хранения LSI данных из TeamCenter.
    Содержит конкретные поля вместо общего JSON в поле data.
    """
    apikey = models.CharField(max_length=255, default="default_apikey")
    sender = models.CharField(max_length=255, default="TeamCenter")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Обязательные поля
    position_name = models.CharField(max_length=255, help_text="Название позиции (вместо name)")
    uuid = models.CharField(max_length=100, null=True, blank=True, help_text="UUID компонента")
    drawing_number = models.CharField(max_length=255, null=True, blank=True, help_text="Номер чертежа")
    
    # Дополнительные поля
    dns = models.TextField(null=True, blank=True, help_text="Описание (вместо description)")
    code_1 = models.CharField(max_length=100, null=True, blank=True, help_text="Код 1 - обычно revision")
    code_2 = models.CharField(max_length=100, null=True, blank=True, help_text="Код 2 - обычно type")
    code_3 = models.CharField(max_length=100, null=True, blank=True, help_text="Код 3 - обычно unitOfMeasure")
    
    # Прочие допустимые поля
    cipher = models.CharField(max_length=100, null=True, blank=True)
    code_4 = models.CharField(max_length=100, null=True, blank=True)
    code_5 = models.CharField(max_length=100, null=True, blank=True)
    deletion_mark = models.BooleanField(default=False)
    group_indicator = models.CharField(max_length=100, null=True, blank=True)
    lkn = models.CharField(max_length=100, null=True, blank=True)
    modification_code = models.CharField(max_length=100, null=True, blank=True)
    object_type_code = models.CharField(max_length=100, null=True, blank=True)
    parent_record_id = models.IntegerField(null=True, blank=True)
    position_code = models.CharField(max_length=100, null=True, blank=True)
    position_in_staff_structure_type = models.CharField(max_length=100, null=True, blank=True)
    quantity = models.FloatField(null=True, blank=True)
    specialty = models.CharField(max_length=100, null=True, blank=True)
    
    # Дополнительное JSON-поле для хранения остальных данных
    extra_data = models.TextField(default="{}", help_text="Дополнительные данные в JSON формате")
    
    # Флаги отправки
    sent_to_atom = models.BooleanField(default=False)
    
    def __str__(self):
        return f"TeamCenter LSI {self.id} - {self.position_name}"
