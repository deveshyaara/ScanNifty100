from django.contrib import admin
from .models import Sector, Company


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('sector_code', 'sector_name', 'description')
    search_fields = ('sector_name', 'sector_code')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'company_name', 'sector', 'face_value')
    list_filter = ('sector',)
    search_fields = ('symbol', 'company_name')
    readonly_fields = ('symbol',)  # Primary key cannot be edited
