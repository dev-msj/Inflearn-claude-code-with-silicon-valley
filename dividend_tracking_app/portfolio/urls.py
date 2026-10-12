from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tickers/", views.ticker_list, name="ticker_list"),
    path("tickers/new/", views.ticker_form, name="ticker_create"),
    path("tickers/<int:pk>/", views.ticker_detail, name="ticker_detail"),
    path("tickers/<int:pk>/edit/", views.ticker_form, name="ticker_edit"),
    path("tickers/<int:pk>/delete/", views.ticker_delete, name="ticker_delete"),
    path("dividends/", views.dividend_list, name="dividend_list"),
    path("dividends/new/", views.dividend_form, name="dividend_create"),
    path("dividends/<int:pk>/edit/", views.dividend_form, name="dividend_edit"),
    path("dividends/<int:pk>/delete/", views.dividend_delete, name="dividend_delete"),
]
