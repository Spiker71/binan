import logging
import numpy as np
import matplotlib.pyplot as plt
from binance.client import Client
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
import time
import datetime

# Установка параметров логирования
logging.basicConfig(filename='trading_signals.log', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Вставьте ваш API ключ и секрет сюда
api_key = 'czs8NPf9uo1va2Sg4HB5NCWFO7XGNtP8RPHWLWU8eWqNw0XhqjCsPhJreJfaEMhv'
api_secret = 'v0Onk3jFT4G5Q4vufMt3eDqT2r2cKKW4NoOQC53uLNSfjRcBHfqdmYBrHaFa3Udx'

# Создание клиента Binance
client = Client(api_key, api_secret)

def get_historical_klines(symbol, interval, start_str):
    """Получение исторических данных"""
    klines = client.get_historical_klines(symbol, interval, start_str)
    return klines

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

def analyze_market():
    """Основная функция для анализа рынка"""
    symbols = [symbol['symbol'] for symbol in client.get_all_tickers()]  # Получение всех символов с Binance
    intervals = [Client.KLINE_INTERVAL_15MINUTE, Client.KLINE_INTERVAL_1HOUR]

    for symbol in symbols:
        for interval in intervals:
            start_str = '1 month ago UTC'

            # Получение исторических данных
            klines = get_historical_klines(symbol, interval, start_str)
            close_prices = np.array([float(kline[4]) for kline in klines])

            # Рассчет уровней Фибоначчи
            fibonacci_levels = calculate_fibonacci_levels(close_prices)

            # Поиск точек входа
            signals = find_trade_signals(close_prices, fibonacci_levels)

            # Логирование сигналов
            for signal in signals:
                logging.info(f"Signal: {signal[0]} at index {signal[1]} (price: {close_prices[signal[1]]}) for {symbol} on {interval}")
            
            # Сохранение графиков с уровнями Фибоначчи и сигналами
            save_chart(symbol, interval, close_prices, fibonacci_levels, signals)

            # Делание скриншота графика
            capture_chart_screenshot(symbol, interval)

def save_chart(symbol, interval, close_prices, levels, signals):
    """Сохранение графиков с уровнями Фибоначчи и сигналами"""
    plt.figure(figsize=(10, 5))
    plt.plot(close_prices, label='Close Prices')
    for level in levels:
        plt.axhline(y=levels[level], linestyle='--', label=f'Fibonacci {level}')
    for signal in signals:
        if signal[0] == 'Buy':
            plt.plot(signal[1], close_prices[signal[1]], 'go', label='Buy Signal')
        elif signal[0] == 'Sell':
            plt.plot(signal[1], close_prices[signal[1]], 'ro', label='Sell Signal')
    plt.title(f'{symbol} - {interval}')
    plt.legend()
    plt.savefig(f'{symbol}_{interval}.png')
    plt.close()

def capture_chart_screenshot(symbol, interval):
    """Сделать скриншот графика с TradingView"""
    options = Options()
    # options.add_argument('--headless')  # Для отладки отключим headless режим
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=ChromeService(), options=options)
    driver.set_window_size(1920, 1080)
    
    # Открытие TradingView с графиком
    url = f'https://www.tradingview.com/chart/?symbol=BINANCE%3A{symbol.replace("/", "")}'
    driver.get(url)
    
    try:
        # Ждем, пока элемент станет видимым
        chart_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'canvas'))
        )
        time.sleep(5)  # Задержка для полной загрузки графика
        screenshot = chart_element.screenshot_as_png
        image = Image.open(BytesIO(screenshot))
        image.save(f'{symbol}_{interval}_screenshot.png')
    except Exception as e:
        logging.error(f"Error capturing screenshot for {symbol} on {interval}: {e}")
    finally:
        driver.quit()

def main():
    while True:
        analyze_market()
        time.sleep(60 * 15)  # анализировать каждые 15 минут

if __name__ == '__main__':
    main()
