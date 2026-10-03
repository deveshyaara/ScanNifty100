from django.contrib import admin
from .models import ProfitLoss, BalanceSheet, CashFlow


@admin.register(ProfitLoss)
class ProfitLossAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'year', 'sales', 'net_profit', 'eps')
    list_filter = ('year', 'symbol__sector')
    search_fields = ('symbol__symbol', 'symbol__company_name')
    readonly_fields = ('symbol', 'year')


@admin.register(BalanceSheet)
class BalanceSheetAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'year', 'total_assets', 'total_liabilities', 'debt_to_equity')
    list_filter = ('year', 'symbol__sector')
    search_fields = ('symbol__symbol', 'symbol__company_name')
    readonly_fields = ('symbol', 'year')


@admin.register(CashFlow)
class CashFlowAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'year', 'operating_activity', 'net_cash_flow', 'free_cash_flow')
    list_filter = ('year', 'symbol__sector')
    search_fields = ('symbol__symbol', 'symbol__company_name')
    readonly_fields = ('symbol', 'year')
