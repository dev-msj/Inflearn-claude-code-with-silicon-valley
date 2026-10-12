# 배당 기록 앱 스펙

## 목적
보유 종목(ticker), 실제 수령한 배당(dividend), 수익률(yield) 이력을 관리하고,
종목별 배당 지급 일정을 기반으로 **향후 12개월의 월별 배당 소득을 예측**하는 개인용 웹 앱입니다.

## 범위와 결정 사항
- 백엔드: Django 5.2 (LTS), 단일 앱 `portfolio`
- 프론트엔드: Django 템플릿 + 최소한의 CSS (JS 프레임워크 없음)
- DB: SQLite
- 데이터 입력: 전부 수동 입력 (외부 시세/배당 API 없음)
- 인증: 단일 사용자, 로그인 없음 (`/admin`만 Django 기본 인증으로 보호)
- 실행 환경: conda env `py312` (Python 3.12)

## 데이터 모델
모든 금액·수량은 `DecimalField`로 저장합니다.

### Ticker (보유 종목)
| 필드 | 설명 |
|---|---|
| `symbol` | 종목 코드, 고유값, 대문자로 저장 |
| `name` | 종목명 (선택) |
| `shares` | 보유 수량 (소수점 허용) |
| `avg_cost` | 평균 매입 단가 |
| `current_price` | 현재가 (수동 입력) |
| `dividend_per_share` | 1회 지급 시 주당 배당금 |
| `frequency` | 연간 지급 횟수: 월 12 / 분기 4 / 반기 2 / 연 1 |
| `first_payment_month` | 연중 첫 지급 월 (1–12) |

계산 값:
- `payment_months`: 첫 지급 월부터 `12 / frequency` 간격으로 도출한 지급 월 집합
  - 예: 분기, 첫 지급 월 2 → {2, 5, 8, 11}
- `annual_dividend_per_share` = `dividend_per_share × frequency`
- `annual_income` = `annual_dividend_per_share × shares`
- `market_value` = `current_price × shares`
- `current_yield` = `annual_dividend_per_share / current_price` (현재가가 0이면 없음)
- `yield_on_cost` = `annual_dividend_per_share / avg_cost` (매입가가 0이면 없음)

### Dividend (실제 수령 배당 기록)
| 필드 | 설명 |
|---|---|
| `ticker` | Ticker FK (종목 삭제 시 함께 삭제) |
| `pay_date` | 지급일 |
| `amount_per_share` | 주당 지급액 |
| `shares` | 지급 시점 보유 수량 (스냅샷) |

- `total` = `amount_per_share × shares`
- 새 기록 폼은 종목을 선택하지 않은 상태에서 수량을 비워 두며, 비어 있으면 종목의 현재 보유 수량으로 채웁니다.

### YieldSnapshot (수익률 추적 이력)
| 필드 | 설명 |
|---|---|
| `ticker` | Ticker FK |
| `date` | 기록일 |
| `price` | 당시 가격 |
| `annual_dividend_per_share` | 당시 연간 주당 배당금 |

- `yield_pct` = `annual_dividend_per_share / price` (가격 0이면 없음)
- 종목 **생성 시**, 그리고 **현재가·배당금·지급 주기가 바뀐 수정 시** 스냅샷 1건을 생성합니다. 그 외 수정에서는 생성하지 않습니다.

## 월 소득 예측
`portfolio/forecast.py`의 순수 함수로 구현합니다 (DB 비의존).

```python
forecast_monthly_income(tickers, start: date, months: int = 12) -> list[MonthForecast]
```
- `start`가 속한 달부터 `months`개월을 순서대로 반환합니다 (연도 넘김 처리).
- 각 달의 금액 = 그 달이 `payment_months`에 포함된 종목들의 `dividend_per_share × shares` 합계
- `MonthForecast`: `year`, `month`, `total`, `breakdown` (`[(symbol, amount)]`)

## 화면 / URL
| URL | 내용 |
|---|---|
| `/` | 대시보드: 총 평가액, 연간 예상 배당, 월 평균 배당, 포트폴리오 수익률, 향후 12개월 월별 예측 표(+ CSS 막대) |
| `/tickers/` | 종목 목록 |
| `/tickers/new/` | 종목 등록 |
| `/tickers/<id>/` | 종목 상세: 수익률 지표, 수익률 이력, 해당 종목 배당 기록 |
| `/tickers/<id>/edit/` | 종목 수정 |
| `/tickers/<id>/delete/` | 종목 삭제 (POST 확인) |
| `/dividends/` | 배당 기록 목록 + 연도별 수령 합계 |
| `/dividends/new/` | 배당 기록 등록 |
| `/dividends/<id>/edit/` | 배당 기록 수정 |
| `/dividends/<id>/delete/` | 배당 기록 삭제 (POST 확인) |
| `/admin/` | Django 관리자 (세 모델 등록) |

포트폴리오 수익률 = 전체 `annual_income` / 전체 `market_value` (평가액 0이면 없음)

## 검증 기준
- `forecast`: 월/분기/반기/연 주기, 연도 넘김(11월 시작), 빈 포트폴리오에서 올바른 결과
- 모델: 지급 월 도출, 수익률 계산, 가격·원가 0 처리, 심볼 대문자화
- 뷰: 대시보드 200 응답, 종목 생성 시 스냅샷 생성, 가격 미변경 수정 시 스냅샷 미생성, 가격 변경 수정 시 스냅샷 생성, 배당 기록 수량 기본값
- 전체 테스트: `conda run -n py312 python manage.py test portfolio`
