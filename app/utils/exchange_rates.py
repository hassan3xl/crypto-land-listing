"""
Crypto Exchange Rates Module.
Provides currency conversion between supported cryptocurrencies and USD / USDT.
Designed to be easily upgraded to live market ticker APIs (e.g. CoinGecko, Binance, CoinMarketCap).
"""

from decimal import Decimal, ROUND_HALF_UP

# Base fallback exchange rates in USD / USDT
# 1 ETH = $3,200.00 USD
# 1 SOL = $145.00 USD
# 1 BTC = $64,000.00 USD
# 1 USDT = $1.00 USD
EXCHANGE_RATES = {
    'ETH': Decimal('3200.00'),
    'SOL': Decimal('145.00'),
    'BTC': Decimal('64000.00'),
    'USDT': Decimal('1.00'),
}


def get_exchange_rate(crypto_currency: str) -> Decimal:
    """Return USD value for 1 unit of given crypto currency."""
    currency = (crypto_currency or 'ETH').upper().strip()
    return EXCHANGE_RATES.get(currency, Decimal('1.00'))


def convert_crypto_to_usd(amount, crypto_currency: str) -> Decimal:
    """
    Convert a given crypto amount to USD/USDT value.
    Example: convert_crypto_to_usd(12, 'ETH') -> Decimal('38400.00')
    """
    if amount is None or amount == '':
        return Decimal('0.00')
    
    try:
        num_amount = Decimal(str(amount))
    except (ValueError, TypeError):
        return Decimal('0.00')

    rate = get_exchange_rate(crypto_currency)
    converted = num_amount * rate
    return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def convert_usd_to_crypto(usd_amount, crypto_currency: str) -> Decimal:
    """
    Convert a given USD amount to equivalent crypto currency amount.
    Example: convert_usd_to_crypto(38400, 'ETH') -> Decimal('12.000000')
    """
    if usd_amount is None or usd_amount == '':
        return Decimal('0.000000')
        
    try:
        num_usd = Decimal(str(usd_amount))
    except (ValueError, TypeError):
        return Decimal('0.000000')

    rate = get_exchange_rate(crypto_currency)
    if rate == 0:
        return Decimal('0.000000')

    converted = num_usd / rate
    return converted.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)


def get_all_rates_dict():
    """Return dictionary of currency rates serialized as float/string for JSON/JS APIs."""
    return {currency: float(rate) for currency, rate in EXCHANGE_RATES.items()}
