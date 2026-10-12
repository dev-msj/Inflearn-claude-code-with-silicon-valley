from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from portfolio.forecast import forecast_monthly_income
from portfolio.models import Ticker


def make_ticker(symbol, frequency, first_month, dps, shares):
    return Ticker(
        symbol=symbol,
        shares=Decimal(shares),
        avg_cost=Decimal("10"),
        current_price=Decimal("10"),
        dividend_per_share=Decimal(dps),
        frequency=frequency,
        first_payment_month=first_month,
    )


class ForecastTests(SimpleTestCase):
    def test_empty_portfolio_returns_zero_months(self):
        result = forecast_monthly_income([], date(2026, 1, 15))

        self.assertEqual(len(result), 12)
        self.assertTrue(all(m.total == 0 and m.breakdown == [] for m in result))

    def test_monthly_payer_pays_every_month(self):
        t = make_ticker("O", Ticker.Frequency.MONTHLY, 1, "0.25", "100")

        result = forecast_monthly_income([t], date(2026, 1, 1))

        self.assertEqual([m.total for m in result], [Decimal("25.00")] * 12)

    def test_quarterly_payer_pays_only_in_payment_months(self):
        t = make_ticker("KO", Ticker.Frequency.QUARTERLY, 1, "0.5", "10")

        result = forecast_monthly_income([t], date(2026, 1, 1))

        paid = {m.month: m.total for m in result if m.total}
        self.assertEqual(paid, {1: Decimal("5.0"), 4: Decimal("5.0"),
                                7: Decimal("5.0"), 10: Decimal("5.0")})

    def test_semi_annual_and_annual(self):
        semi = make_ticker("S", Ticker.Frequency.SEMI_ANNUAL, 6, "1", "10")
        annual = make_ticker("A", Ticker.Frequency.ANNUAL, 3, "2", "10")

        result = forecast_monthly_income([semi, annual], date(2026, 1, 1))

        paid = {m.month: m.total for m in result if m.total}
        self.assertEqual(paid, {3: Decimal("20"), 6: Decimal("10"), 12: Decimal("10")})

    def test_wraps_into_next_year(self):
        t = make_ticker("KO", Ticker.Frequency.QUARTERLY, 1, "1", "1")

        result = forecast_monthly_income([t], date(2026, 11, 20))

        self.assertEqual((result[0].year, result[0].month), (2026, 11))
        self.assertEqual((result[2].year, result[2].month), (2027, 1))
        self.assertEqual((result[-1].year, result[-1].month), (2027, 10))
        self.assertEqual(result[2].total, Decimal("1"))

    def test_breakdown_lists_each_paying_ticker(self):
        a = make_ticker("A", Ticker.Frequency.MONTHLY, 1, "1", "2")
        b = make_ticker("B", Ticker.Frequency.ANNUAL, 1, "3", "1")

        january = forecast_monthly_income([a, b], date(2026, 1, 1), months=1)[0]

        self.assertEqual(january.breakdown, [("A", Decimal("2")), ("B", Decimal("3"))])
        self.assertEqual(january.total, Decimal("5"))
