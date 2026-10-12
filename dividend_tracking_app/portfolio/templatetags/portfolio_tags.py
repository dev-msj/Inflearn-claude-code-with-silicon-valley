from django import template

register = template.Library()


@register.filter
def percent(ratio):
    """비율(0.0412)을 '4.12%'로 표시합니다. 값이 없으면 '-'를 반환합니다."""
    if ratio is None:
        return "-"
    return f"{ratio * 100:.2f}%"
