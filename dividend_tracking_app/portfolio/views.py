from collections import defaultdict
from decimal import Decimal

from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forecast import forecast_monthly_income
from .forms import DividendForm, TickerForm
from .models import Dividend, Ticker, YieldSnapshot

# 이 필드가 바뀌면 수익률이 달라지므로 스냅샷을 남깁니다.
YIELD_FIELDS = {"current_price", "dividend_per_share", "frequency"}


def dashboard(request):
    tickers = list(Ticker.objects.all())
    forecast = forecast_monthly_income(tickers, timezone.localdate())
    market_value = sum((t.market_value for t in tickers), Decimal("0"))
    annual_income = sum((t.annual_income for t in tickers), Decimal("0"))
    max_month = max((m.total for m in forecast), default=0)
    return render(request, "portfolio/dashboard.html", {
        "tickers": tickers,
        "forecast": forecast,
        "forecast_total": sum((m.total for m in forecast), Decimal("0")),
        "max_month": max_month,
        "market_value": market_value,
        "annual_income": annual_income,
        "monthly_average": annual_income / 12,
        "portfolio_yield": annual_income / market_value if market_value else None,
    })


def ticker_list(request):
    return render(request, "portfolio/ticker_list.html", {
        "tickers": Ticker.objects.all(),
    })


def ticker_detail(request, pk):
    ticker = get_object_or_404(Ticker, pk=pk)
    return render(request, "portfolio/ticker_detail.html", {
        "ticker": ticker,
        "payment_months": sorted(ticker.payment_months),
        "snapshots": ticker.yield_snapshots.all(),
        "dividends": ticker.dividends.all(),
    })


def ticker_form(request, pk=None):
    ticker = get_object_or_404(Ticker, pk=pk) if pk else None
    form = TickerForm(request.POST or None, instance=ticker)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        if ticker is None or YIELD_FIELDS & set(form.changed_data):
            YieldSnapshot.record(saved, timezone.localdate())
        return redirect("ticker_detail", pk=saved.pk)
    return render(request, "portfolio/form.html", {
        "form": form,
        "title": f"{ticker} 수정" if ticker else "종목 등록",
        "cancel_url": "ticker_list",
    })


def ticker_delete(request, pk):
    ticker = get_object_or_404(Ticker, pk=pk)
    if request.method == "POST":
        ticker.delete()
        return redirect("ticker_list")
    return render(request, "portfolio/confirm_delete.html", {
        "object": ticker,
        "warning": "이 종목의 배당 기록과 수익률 이력도 함께 삭제됩니다.",
        "cancel_url": "ticker_list",
    })


def dividend_list(request):
    dividends = Dividend.objects.select_related("ticker")
    yearly = defaultdict(Decimal)
    for d in dividends:
        yearly[d.pay_date.year] += d.total
    return render(request, "portfolio/dividend_list.html", {
        "dividends": dividends,
        "yearly_totals": sorted(yearly.items(), reverse=True),
    })


def dividend_form(request, pk=None):
    dividend = get_object_or_404(Dividend, pk=pk) if pk else None
    form = DividendForm(request.POST or None, instance=dividend)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("dividend_list")
    return render(request, "portfolio/form.html", {
        "form": form,
        "title": "배당 기록 수정" if dividend else "배당 기록 등록",
        "cancel_url": "dividend_list",
    })


def dividend_delete(request, pk):
    dividend = get_object_or_404(Dividend, pk=pk)
    if request.method == "POST":
        dividend.delete()
        return redirect("dividend_list")
    return render(request, "portfolio/confirm_delete.html", {
        "object": dividend,
        "cancel_url": "dividend_list",
    })
