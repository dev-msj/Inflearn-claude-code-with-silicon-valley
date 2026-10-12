from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from portfolio.models import Dividend, Ticker, YieldSnapshot

TICKER_DATA = {
    "symbol": "ko",
    "name": "Coca-Cola",
    "shares": "10",
    "avg_cost": "50",
    "current_price": "60",
    "dividend_per_share": "0.5",
    "frequency": "4",
    "first_payment_month": "1",
}


class DashboardTests(TestCase):
    def test_empty_dashboard(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "등록된 종목이 없습니다")

    def test_dashboard_shows_forecast(self):
        self.client.post(reverse("ticker_create"), TICKER_DATA)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["forecast"]), 12)
        self.assertEqual(response.context["annual_income"], Decimal("20"))
        self.assertEqual(response.context["forecast_total"], Decimal("20"))


class TickerViewTests(TestCase):
    def create(self):
        self.client.post(reverse("ticker_create"), TICKER_DATA)
        return Ticker.objects.get()

    def test_create_records_yield_snapshot(self):
        ticker = self.create()

        self.assertEqual(ticker.symbol, "KO")
        self.assertEqual(YieldSnapshot.objects.filter(ticker=ticker).count(), 1)

    def test_edit_without_yield_change_does_not_snapshot(self):
        ticker = self.create()

        self.client.post(reverse("ticker_edit", args=[ticker.pk]),
                         {**TICKER_DATA, "shares": "20", "current_price": "60.00"})

        self.assertEqual(YieldSnapshot.objects.count(), 1)

    def test_edit_with_price_change_snapshots(self):
        ticker = self.create()

        self.client.post(reverse("ticker_edit", args=[ticker.pk]),
                         {**TICKER_DATA, "current_price": "40"})

        latest = YieldSnapshot.objects.first()
        self.assertEqual(YieldSnapshot.objects.count(), 2)
        self.assertEqual(latest.price, Decimal("40"))

    def test_duplicate_symbol_case_insensitive_rejected(self):
        self.create()

        response = self.client.post(reverse("ticker_create"), {**TICKER_DATA, "symbol": "KO"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ticker.objects.count(), 1)

    def test_detail_and_delete(self):
        ticker = self.create()

        self.assertEqual(self.client.get(reverse("ticker_detail", args=[ticker.pk])).status_code, 200)
        self.client.post(reverse("ticker_delete", args=[ticker.pk]))

        self.assertFalse(Ticker.objects.exists())
        self.assertFalse(YieldSnapshot.objects.exists())


class DividendViewTests(TestCase):
    def setUp(self):
        self.client.post(reverse("ticker_create"), TICKER_DATA)
        self.ticker = Ticker.objects.get()

    def test_blank_shares_defaults_to_ticker_shares(self):
        self.client.post(reverse("dividend_create"), {
            "ticker": self.ticker.pk, "pay_date": "2026-04-01",
            "amount_per_share": "0.5", "shares": "",
        })

        dividend = Dividend.objects.get()
        self.assertEqual(dividend.shares, Decimal("10"))
        self.assertEqual(dividend.total, Decimal("5"))

    def test_list_shows_yearly_totals(self):
        Dividend.objects.create(ticker=self.ticker, pay_date="2025-12-01",
                                amount_per_share=Decimal("1"), shares=Decimal("3"))
        Dividend.objects.create(ticker=self.ticker, pay_date="2026-01-01",
                                amount_per_share=Decimal("1"), shares=Decimal("2"))

        response = self.client.get(reverse("dividend_list"))

        self.assertEqual(response.context["yearly_totals"],
                         [(2026, Decimal("2")), (2025, Decimal("3"))])
