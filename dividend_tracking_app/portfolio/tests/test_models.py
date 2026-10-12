from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from portfolio.models import Dividend, Ticker, YieldSnapshot


def make_ticker(**overrides):
    fields = dict(
        symbol="ko",
        shares=Decimal("10"),
        avg_cost=Decimal("50"),
        current_price=Decimal("60"),
        dividend_per_share=Decimal("0.5"),
        frequency=Ticker.Frequency.QUARTERLY,
        first_payment_month=2,
    )
    fields.update(overrides)
    return Ticker(**fields)


class TickerPropertyTests(SimpleTestCase):
    def test_payment_months_quarterly(self):
        self.assertEqual(make_ticker().payment_months, {2, 5, 8, 11})

    def test_payment_months_wrap_around_year(self):
        t = make_ticker(frequency=Ticker.Frequency.SEMI_ANNUAL, first_payment_month=9)
        self.assertEqual(t.payment_months, {9, 3})

    def test_payment_months_monthly(self):
        t = make_ticker(frequency=Ticker.Frequency.MONTHLY, first_payment_month=5)
        self.assertEqual(t.payment_months, set(range(1, 13)))

    def test_annual_figures(self):
        t = make_ticker()
        self.assertEqual(t.annual_dividend_per_share, Decimal("2.0"))
        self.assertEqual(t.annual_income, Decimal("20.0"))
        self.assertEqual(t.market_value, Decimal("600"))

    def test_yields(self):
        t = make_ticker()
        self.assertEqual(t.current_yield, Decimal("2.0") / Decimal("60"))
        self.assertEqual(t.yield_on_cost, Decimal("0.04"))

    def test_zero_price_and_cost_give_no_yield(self):
        t = make_ticker(current_price=Decimal("0"), avg_cost=Decimal("0"))
        self.assertIsNone(t.current_yield)
        self.assertIsNone(t.yield_on_cost)


class PersistedModelTests(TestCase):
    def test_symbol_saved_uppercase(self):
        t = make_ticker(symbol=" ko ")
        t.save()
        self.assertEqual(Ticker.objects.get().symbol, "KO")

    def test_dividend_total(self):
        t = make_ticker()
        t.save()
        d = Dividend(ticker=t, pay_date="2026-01-01",
                     amount_per_share=Decimal("0.5"), shares=Decimal("10"))
        self.assertEqual(d.total, Decimal("5.0"))

    def test_yield_snapshot_record(self):
        t = make_ticker()
        t.save()
        snap = YieldSnapshot.record(t, "2026-10-12")
        self.assertEqual(snap.price, Decimal("60"))
        self.assertEqual(snap.annual_dividend_per_share, Decimal("2.0"))
        self.assertEqual(snap.yield_pct, Decimal("2.0") / Decimal("60"))
