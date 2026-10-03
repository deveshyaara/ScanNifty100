from django.contrib import admin
from .models import Year


@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    list_display = ('year_label', 'fiscal_year', 'quarter', 'is_ttm', 'is_half_year', 'sort_order')
    list_filter = ('is_ttm', 'is_half_year')
    ordering = ['sort_order']
