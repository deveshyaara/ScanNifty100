from django.contrib import admin
from .models import MLScore, HealthLabel, ProsCons


@admin.register(HealthLabel)
class HealthLabelAdmin(admin.ModelAdmin):
    list_display = ('label_name', 'min_score', 'max_score', 'color_hex')


@admin.register(MLScore)
class MLScoreAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'overall_score', 'health_label', 'computed_at')
    list_filter = ('health_label', 'computed_at')
    readonly_fields = ('symbol', 'computed_at')


@admin.register(ProsCons)
class ProsConsAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'is_pro', 'category', 'source', 'text_preview')
    list_filter = ('is_pro', 'source', 'category')
    search_fields = ('symbol__company_name', 'text')

    def text_preview(self, obj):
        return obj.text[:80] + "..." if len(obj.text) > 80 else obj.text
    text_preview.short_description = "Insight Text"
