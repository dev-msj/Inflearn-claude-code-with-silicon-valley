from django import forms

from .models import Dividend, Ticker


class TickerForm(forms.ModelForm):
    class Meta:
        model = Ticker
        fields = [
            "symbol",
            "name",
            "shares",
            "avg_cost",
            "current_price",
            "dividend_per_share",
            "frequency",
            "first_payment_month",
        ]

    def clean_symbol(self):
        return self.cleaned_data["symbol"].strip().upper()


class DividendForm(forms.ModelForm):
    class Meta:
        model = Dividend
        fields = ["ticker", "pay_date", "amount_per_share", "shares"]
        widgets = {"pay_date": forms.DateInput(attrs={"type": "date"})}
        help_texts = {"shares": "비워 두면 종목의 현재 보유 수량을 사용합니다."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["shares"].required = False

    def clean(self):
        cleaned = super().clean()
        ticker = cleaned.get("ticker")
        if ticker and cleaned.get("shares") is None:
            cleaned["shares"] = ticker.shares
        return cleaned
