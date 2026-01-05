# CVaR (Historical VaR & CVaR) — Açıklama ve Kullanım

Bu küçük Python projesi, Yahoo Finance'ten hisse kapanış fiyatlarını çekip günlük getiriler üzerinden tarihsel Value at Risk (VaR) ve Conditional Value at Risk (CVaR / Expected Shortfall) hesaplaması yapar. Ayrıca portföy beklenen getirisi ve riski (standart sapma) için basit bir yardımcı fonksiyon sağlar.

Not: Bu README, repository'deki `cvar.py` (güncel sürüm) dosyasına göre hazırlanmıştır.

## Öne çıkan özellikler
- Yahoo Finance'ten kapanış verilerini çekme (`get_data`)
- Günlük getiriler, ortalama getiriler ve kovaryans matrisi hesaplama
- Portföy beklenen getirisi ve standart sapma hesaplama (`portfolio_performance`)
- Tarihsel VaR hesaplama (`historical_var`) — alfa hem yüzde (ör. `5`) hem oran (ör. `0.05`) şeklinde verilebilir
- Tarihsel CVaR / Expected Shortfall hesaplama (`historical_cvar`) — var altındaki getirilerin ortalaması
- CVaR fonksiyonundaki önceki özyineleme hatası giderildi

## Gereksinimler
- Python 3.8+
- pandas
- numpy
- pandas_datareader

Kurulum (örnek):
```bash
python -m pip install pandas numpy pandas_datareader
```

Not: pandas_datareader ile Yahoo veri çekme internet bağlantısı gerektirir; bazen ek yapılandırma veya `yfinance` gibi paketlere ihtiyaç duyulabilir.

## Hızlı başlangıç — CLI (script olarak çalıştırma)
Repository kökünde `cvar.py` çalıştırılabilir. Bu durumda örnek bir portföy oluşturulur, %5 VaR ve CVaR hesaplanıp yazdırılır:

```bash
python cvar.py
```

Çalıştırınca:
- Veri çekilir (son 800 gün)
- Deterministik rastgele ağırlıklar ile portföy getirisi hesaplanır
- Portföyün %5 VaR ve CVaR'ı yazdırılır

## API Referansı (kısa)

Aşağıdaki fonksiyonlar `cvar.py` içinde tanımlıdır ve başka bir Python dosyasından import edilerek kullanılabilir.

- get_data(stocks, start, end)
  - Açıklama: Yahoo Finance'ten `stocks` listesindeki sembollerin kapanış fiyatlarını çeker.
  - Girdi:
    - stocks: liste (örn. `['CBA.AX', 'BHP.AX']`)
    - start, end: datetime nesneleri veya uygun stringler
  - Döner: (returns, meanReturns, covMatrix)
    - returns: DataFrame (günlük yüzde değişimler)
    - meanReturns: Series (ortalama günlük getiri)
    - covMatrix: DataFrame (getiri kovaryansı)

- portfolio_performance(weights, meanReturns, covMatrix, time_horizon)
  - Açıklama: Verilen ağırlıklara göre beklenen getiri ve standart sapma hesaplar.
  - Girdi:
    - weights: array-like (ağırlıkların toplamı 1 olmalı)
    - meanReturns: Series (genellikle günlük ortalama getiriler)
    - covMatrix: kovaryans matrisi
    - time_horizon: ölçekleyici (ör. günlük veriden yıllıklaştırma için 252)
  - Döner: (expected_return, std_dev) — her ikisi de time_horizon ile ölçeklenmiş

- historical_var(returns, alpha=5)
  - Açıklama: Tarihsel VaR (percentile temelli).
  - Girdi:
    - returns: pd.Series veya pd.DataFrame
    - alpha: yüzde ya da oran (varsayılan `5` = %5). `0.05` veya `5` ikisi ile de çalışır.
  - Döner: Series için tek bir sayı; DataFrame için sütun bazlı Series.

- historical_cvar(returns, alpha=5)
  - Açıklama: Tarihsel CVaR / Expected Shortfall.
  - Girdi: `historical_var` ile aynı.
  - İşlem: Series için önce VaR hesaplanır, sonra VaR ve altındaki getirilerin ortalaması döndürülür.
  - Not: Orijinal dosyadaki özyineleme (recursion) hatası düzeltilmiştir.

- _alpha_to_percent(alpha)
  - Yardımcı fonksiyon: alpha girişini yüzde (0-100) biçimine çevirir. Doğrudan kullanılmamalıdır (private).

## Kullanım örnekleri

1) Başka bir script içinde import ederek:

```python
from cvar import get_data, historical_var, historical_cvar, portfolio_performance
import datetime as dt
import numpy as np

stocks = ['CBA.AX', 'BHP.AX', 'TLS.AX']
start = dt.datetime(2024, 1, 1)
end = dt.datetime(2025, 1, 1)

returns, meanReturns, covMatrix = get_data(stocks, start, end)
returns = returns.dropna()

# Basit eşit ağırlık portföyü
weights = np.array([1/len(stocks)] * len(stocks))

# Portföy günlük getirisi
portfolio_returns = returns.dot(weights)

# %5 VaR ve CVaR (alpha hem 5 hem 0.05 ile verilebilir)
var_5 = historical_var(portfolio_returns, alpha=5)
cvar_5 = historical_cvar(portfolio_returns, alpha=0.05)

print("VaR (5%):", var_5)
print("CVaR (5%):", cvar_5)

# Yıllıklaştırılmış performans (günlük -> yıllık için 252)
exp_ret, std_dev = portfolio_performance(weights, meanReturns, covMatrix, time_horizon=252)
print("Annualized expected return:", exp_ret)
print("Annualized std dev:", std_dev)
```

2) DataFrame üzerinde sütun bazlı VaR/CVaR:
```python
# Her hisseler için %1 VaR ve CVaR hesaplama
var_1 = historical_var(returns, alpha=1)
cvar_1 = historical_cvar(returns, alpha=0.01)
print(var_1)
print(cvar_1)
```

## Alpha (α) parametresi hakkında notlar
- Fonksiyonlar alpha'yı hem yüzde (ör. `5`) hem de oran (ör. `0.05`) olarak kabul eder.
- `_alpha_to_percent` bu dönüşümü yapar. Geçersiz veya anlamsız değerler (örn. negatifler, 100) reddedilir.
- Varsayılan `alpha=5` olarak bırakılmıştır (yüzde 5). İsterseniz `alpha=0.05` de kullanabilirsiniz.

## Dikkat edilmesi gereken noktalar
- Veri çekme: `pandas_datareader` üzerinden Yahoo verisi çekmek internet gerektirir. Bazı sistemlerde ek yapılandırma gerekebilir.
- Eksik veriler: Fonksiyonlar içlerinde `.dropna()` kullanır; ancak kullanıcının veri ön işleme yapması (ör. boş sütunları kontrol) tavsiye edilir.
- Reproducibility: Örnek script deterministik rastgele ağırlıklar (`np.random.seed(42)`) kullanır. Kendi ağırlıklarınızı siz belirleyin.
- CVaR hesaplama: Eğer belirlenen alpha için "tail" (VaR altı) boş ise fonksiyon `numpy.nan` döndürür.

## Katkıda bulunma
- Hatalar/öneriler için pull request veya issue açabilirsiniz.
- CVaR için farklı tanımlar (ortalama yerine interpolasyon vb.) uygulanmak istenirse fonksiyonlar genişletilebilir.

## Lisans
Varsayılan olarak açık kaynak (ör. MIT) kabul edilebilir. Kendi tercih ettiğiniz lisansı ekleyin.
