from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class MonthForecast:
    year: int
    month: int
    total: Decimal = Decimal("0")
    breakdown: list = field(default_factory=list)


def forecast_monthly_income(tickers, start: date, months: int = 12):
    """start가 속한 달부터 months개월 동안의 예상 배당 소득을 계산합니다."""
    result = []
    for offset in range(months):
        index = start.month - 1 + offset
        forecast = MonthForecast(year=start.year + index // 12, month=index % 12 + 1)
        for ticker in tickers:
            if forecast.month in ticker.payment_months:
                amount = ticker.dividend_per_share * ticker.shares
                forecast.breakdown.append((ticker.symbol, amount))
                forecast.total += amount
        result.append(forecast)
    return result
