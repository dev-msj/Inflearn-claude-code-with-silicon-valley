from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

MONEY = {"max_digits": 14, "decimal_places": 4}
QUANTITY = {"max_digits": 14, "decimal_places": 4}
NON_NEGATIVE = [MinValueValidator(Decimal("0"))]


def _ratio(numerator, denominator):
    if not denominator:
        return None
    return numerator / denominator


class Ticker(models.Model):
    class Frequency(models.IntegerChoices):
        MONTHLY = 12, "월배당"
        QUARTERLY = 4, "분기배당"
        SEMI_ANNUAL = 2, "반기배당"
        ANNUAL = 1, "연배당"

    symbol = models.CharField("종목 코드", max_length=20, unique=True)
    name = models.CharField("종목명", max_length=100, blank=True)
    shares = models.DecimalField("보유 수량", validators=NON_NEGATIVE, **QUANTITY)
    avg_cost = models.DecimalField("평균 매입가", validators=NON_NEGATIVE, **MONEY)
    current_price = models.DecimalField("현재가", validators=NON_NEGATIVE, **MONEY)
    dividend_per_share = models.DecimalField(
        "1회 주당 배당금", validators=NON_NEGATIVE, **MONEY
    )
    frequency = models.PositiveSmallIntegerField(
        "지급 주기", choices=Frequency.choices, default=Frequency.QUARTERLY
    )
    first_payment_month = models.PositiveSmallIntegerField(
        "첫 지급 월",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return self.symbol

    def save(self, *args, **kwargs):
        self.symbol = self.symbol.strip().upper()
        super().save(*args, **kwargs)

    @property
    def payment_months(self):
        interval = 12 // self.frequency
        return {
            (self.first_payment_month - 1 + i * interval) % 12 + 1
            for i in range(self.frequency)
        }

    @property
    def annual_dividend_per_share(self):
        return self.dividend_per_share * self.frequency

    @property
    def annual_income(self):
        return self.annual_dividend_per_share * self.shares

    @property
    def market_value(self):
        return self.current_price * self.shares

    @property
    def current_yield(self):
        return _ratio(self.annual_dividend_per_share, self.current_price)

    @property
    def yield_on_cost(self):
        return _ratio(self.annual_dividend_per_share, self.avg_cost)


class Dividend(models.Model):
    ticker = models.ForeignKey(
        Ticker, on_delete=models.CASCADE, related_name="dividends", verbose_name="종목"
    )
    pay_date = models.DateField("지급일")
    amount_per_share = models.DecimalField(
        "주당 지급액", validators=NON_NEGATIVE, **MONEY
    )
    shares = models.DecimalField("수량", validators=NON_NEGATIVE, **QUANTITY)

    class Meta:
        ordering = ["-pay_date", "ticker__symbol"]

    def __str__(self):
        return f"{self.ticker} {self.pay_date}"

    @property
    def total(self):
        return self.amount_per_share * self.shares


class YieldSnapshot(models.Model):
    ticker = models.ForeignKey(
        Ticker, on_delete=models.CASCADE, related_name="yield_snapshots"
    )
    date = models.DateField()
    price = models.DecimalField(**MONEY)
    annual_dividend_per_share = models.DecimalField(**MONEY)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.ticker} {self.date}"

    @property
    def yield_pct(self):
        return _ratio(self.annual_dividend_per_share, self.price)

    @classmethod
    def record(cls, ticker, date):
        return cls.objects.create(
            ticker=ticker,
            date=date,
            price=ticker.current_price,
            annual_dividend_per_share=ticker.annual_dividend_per_share,
        )
