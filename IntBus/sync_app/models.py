from django.db import models

# Create your models here.

class MappingField(models.Model):
    """
    Модель для хранения правил маппинга полей между системами.
    Используется для преобразования данных при отправке из одной системы в другую.
    """
    SOURCE_CHOICES = [
        ('ATOM', 'ATOM'),
        ('TEAMCENTER', 'TeamCenter'),
        ('INTBUS', 'IntBus'),
    ]
    
    TARGET_CHOICES = [
        ('ATOM', 'ATOM'),
        ('TEAMCENTER', 'TeamCenter'),
    ]
    
    DATA_TYPE_CHOICES = [
        ('nomenclature', 'Номенклатура'),
        ('lsi', 'ЛСИ (Логическая структура изделия)'),
    ]
    
    source_system = models.CharField(max_length=50, choices=SOURCE_CHOICES, 
                                    verbose_name="Система-источник")
    target_system = models.CharField(max_length=50, choices=TARGET_CHOICES, 
                                    verbose_name="Целевая система")
    data_type = models.CharField(max_length=50, choices=DATA_TYPE_CHOICES, 
                                verbose_name="Тип данных")
    source_field = models.CharField(max_length=255, verbose_name="Поле источника")
    target_field = models.CharField(max_length=255, verbose_name="Поле назначения")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    
    class Meta:
        verbose_name = "Правило маппинга"
        verbose_name_plural = "Правила маппинга"
        unique_together = ('source_system', 'target_system', 'data_type', 'source_field', 'target_field')
    
    def __str__(self):
        return f"{self.source_system} {self.source_field} -> {self.target_system} {self.target_field} ({self.data_type})"
