from django.db import models

class Nomenclature(models.Model):
    uuid = models.CharField(max_length=36, verbose_name="УУИД", blank=True, null=True)
    spk_nomenclature_type = models.CharField(max_length=100, verbose_name="СПК_ВидНоменклатуры", blank=True, null=True)
    abbreviation = models.CharField(max_length=100, verbose_name="Аббревиатура", blank=True, null=True)
    effective_date = models.DateField(verbose_name="ДатаВведенияВДействие", blank=True, null=True)
    internal_code = models.CharField(max_length=100, verbose_name="КодВнутренний", blank=True, null=True)
    ekps_code = models.CharField(max_length=100, verbose_name="КодЕКПС", blank=True, null=True)
    kvt_code = models.CharField(max_length=100, verbose_name="КодКВТ", blank=True, null=True)
    checksum = models.CharField(max_length=255, verbose_name="КонтрольнаяСуммаЗаписи", blank=True, null=True)
    short_name = models.CharField(max_length=255, verbose_name="НаименованиеКраткое", blank=True, null=True)
    full_name = models.CharField(max_length=255, verbose_name="НаименованиеПолное", blank=True, null=True)
    deletion_mark = models.BooleanField(default=False, verbose_name="ПометкаУдаления")
    archived = models.BooleanField(default=False, verbose_name="ПризнакАрхивнойЗаписи")
    classifier_unique_code = models.CharField(max_length=100, verbose_name="УникальныйКодКлассификатора", blank=True, null=True)
    drawing_number = models.CharField(max_length=100, verbose_name="ЧертежныйНомер", blank=True, null=True)
    cipher = models.CharField(max_length=100, verbose_name="Шифр", blank=True, null=True)

    def __str__(self):
        return self.short_name or self.internal_code

class LSI(models.Model):
    cipher = models.CharField(max_length=100, verbose_name="Шифр", blank=True, null=True)
    uuid = models.CharField(max_length=36, verbose_name="УУИД", blank=True, null=True)
    specialty = models.CharField(max_length=255, verbose_name="Специальность", blank=True, null=True)
    group_indicator = models.BooleanField(default=False, verbose_name="ПризнакГруппы")
    deletion_mark = models.BooleanField(default=False, verbose_name="ПометкаУдаления")
    position_in_staff_structure_type = models.CharField(max_length=255, verbose_name="ПозицияВШтатнойСтруктуреТипа", blank=True, null=True)
    drawing_number = models.CharField(max_length=255, verbose_name="НомерЧертежа", blank=True, null=True)
    position_name = models.CharField(max_length=255, verbose_name="НаименованиеПозиции", blank=True, null=True)
    lkn = models.CharField(max_length=255, verbose_name="Лкн", blank=True, null=True)
    quantity = models.IntegerField(default=1, verbose_name="Количество")
    object_type_code = models.CharField(max_length=36, verbose_name="КодТипаОбъекта", blank=True, null=True)
    position_code = models.CharField(max_length=255, verbose_name="КодПозиции", blank=True, null=True)
    modification_code = models.CharField(max_length=255, verbose_name="КодМодификации", blank=True, null=True)
    code_5 = models.CharField(max_length=255, verbose_name="Код5", blank=True, null=True)
    code_4 = models.CharField(max_length=255, verbose_name="Код4", blank=True, null=True)
    code_3 = models.CharField(max_length=255, verbose_name="Код3", blank=True, null=True)
    code_2 = models.CharField(max_length=255, verbose_name="Код2", blank=True, null=True)
    code_1 = models.CharField(max_length=255, verbose_name="Код1", blank=True, null=True)
    parent_record_id = models.CharField(max_length=255, verbose_name="ИдентификаторРодительскойЗаписи", blank=True, null=True)
    dns = models.CharField(max_length=255, verbose_name="Dns", blank=True, null=True)

    def __str__(self):
        return self.position_name or self.uuid 