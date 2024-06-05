import logging
import sys
import time
from datetime import datetime, timedelta
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Установка кодировки для вывода в консоль
sys.stdout.reconfigure(encoding='utf-8')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

def get_historical_klines(client, symbol, interval, start_str, end_str=None):
    """Получение исторических данных"""
    try:
        klines = client.get_historical_klines(symbol, interval, start_str, end_str)
        return klines
    except BinanceAPIException as e:
        logging.error(f"Ошибка при получении исторических данных: {e}")
        return []

def calculate_fibonacci_levels(data):
    """Расчет уровней Фибоначчи"""
    max_price = max(data)
    min_price = min(data)
    diff = max_price - min_price
    levels = {
        '0.0%': max_price,
        '23.6%': max_price - 0.236 * diff,
        '38.2%': max_price - 0.382 * diff,
        '50.0%': max_price - 0.5 * diff,
        '61.8%': max_price - 0.618 * diff,
        '100.0%': min_price
    }
    return levels

def find_trade_signals(data, levels):
    """Поиск точек входа на основе уровней Фибоначчи"""
    signals = []
    for i in range(1, len(data)):
        if data[i-1] > levels['38.2%'] and data[i] <= levels['38.2%']:
            signals.append(('Buy', i))
        elif data[i-1] < levels['61.8%'] and data[i] >= levels['61.8%']:
            signals.append(('Sell', i))
    return signals

def main():
    api_key = 'czs8NPf9uo1va2Sg4HB5NCWFO7XGNtP8RPHWLWU8eWqNw0XhqjCsPhJreJfaEMhv'
    api_secret = 'v0Onk3jFT4G5Q4vufMt3eDqT2r2cKKW4NoOQC53uLNSfjRcBHfqdmYBrHaFa3Udx'
    symbol = 'BTCUSDT'
    interval = Client.KLINE_INTERVAL_1HOUR
    start_time = datetime.now() - timedelta(days=7)
    end_time = datetime.now()

    # Создание клиента Binance
    client = Client(api_key, api_secret)

    # Получение исторических данных
    klines = get_historical_klines(client, symbol, interval, start_time.strftime("%d %b, %Y %H:%M:%S"),
                                   end_time.strftime("%d %b, %Y %H:%M:%S"))
    if not klines:
        logging.error("Не удалось получить исторические данные. Прерывание работы.")
        return

    close_prices = np.array([float(kline[4]) for kline in klines])

    # Рассчет уровней Фибоначчи
    fibonacci_levels = calculate_fibonacci_levels(close_prices)

    # Поиск точек входа
    signals = find_trade_signals(close_prices, fibonacci_levels)

    # Вывод сигналов
    for signal in signals:
        logging.info(f"Signal: {signal[0]} at index {signal[1]} (price: {close_prices[signal[1]]})")

if __name__ == '__main__':
    main()
