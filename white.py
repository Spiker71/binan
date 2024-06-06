import logging
import numpy as np
import matplotlib.pyplot as plt
from binance.client import Client
from binance.enums import *
from PIL import ImageGrab
import datetime
import time
import subprocess
import sys
import os
import ta
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Функция для установки необходимых пакетов
def install_packages():
    packages = ['numpy', 'matplotlib', 'python-binance', 'ta', 'Pillow', 'selenium', 'webdriver-manager']
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except Exception as e:
            logging.error(f"Failed to install package {package}: {e}")

# Установка пакетов
install_packages()

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

def get_all_symbols():
    """Получение всех символов с Binance"""
    exchange_info = client.get_exchange_info()
    symbols = [s['symbol'] for s in exchange_info['symbols'] if s['quoteAsset'] == 'USDT']
    return symbols

def analyze_market():
    """Основная функция для анализа рынка"""
    symbols = get_all_symbols()  # получение всех символов
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

            # Захват скриншота графика с Binance
            capture_chart(symbol, interval)

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

# Настройки для Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

# Инициализация драйвера Chrome
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def capture_chart(symbol, interval):
    """Снимок экрана графика с Binance"""
    url = f"https://www.binance.com/en/trade/{symbol}?theme=dark&type=spot"
    driver.get(url)
    time.sleep(5)  # Даем время странице загрузиться

    # Найти элемент графика на странице и сделать скриншот всей страницы
    chart_element = driver.find_element(By.CSS_SELECTOR, ".css-1rhbuit")
    screenshot = chart_element.screenshot_as_png
    
    # Сохранение скриншота
    filename = f"{symbol}_{interval}.png"
    with open(filename, "wb") as f:
        f.write(screenshot)
    logging.info(f"Скриншот сохранен: {filename}")

def main():
    logging.basicConfig(filename
