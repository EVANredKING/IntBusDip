from django.contrib import admin
from .models import Nomenclature, LSI

@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    list_display = ('id', 'abbreviation', 'short_name', 'internal_code', 'cipher')
    search_fields = ('abbreviation', 'short_name', 'full_name', 'internal_code', 'cipher', 'uuid')
    list_filter = ('spk_nomenclature_type', 'deletion_mark', 'archived')

@admin.register(LSI)
class LSIAdmin(admin.ModelAdmin):
    list_display = ('id', 'cipher', 'position_name', 'drawing_number', 'quantity')
    search_fields = ('cipher', 'position_name', 'uuid', 'object_type_code')
    list_filter = ('group_indicator', 'deletion_mark') 