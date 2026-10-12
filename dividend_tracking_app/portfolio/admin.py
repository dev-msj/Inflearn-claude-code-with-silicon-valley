from django.contrib import admin

from .models import Dividend, Ticker, YieldSnapshot


@admin.register(Ticker)
class TickerAdmin(admin.ModelAdmin):
    list_display = ["symbol", "name", "shares", "current_price",
                    "dividend_per_share", "frequency"]
    search_fields = ["symbol", "name"]


@admin.register(Dividend)
class DividendAdmin(admin.ModelAdmin):
    list_display = ["ticker", "pay_date", "amount_per_share", "shares"]
    list_filter = ["ticker"]


@admin.register(YieldSnapshot)
class YieldSnapshotAdmin(admin.ModelAdmin):
    list_display = ["ticker", "date", "price", "annual_dividend_per_share"]
    list_filter = ["ticker"]
