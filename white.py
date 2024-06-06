import logging
import numpy as np
import matplotlib.pyplot as plt
from binance.client import Client
from binance.enums import *
from PIL import Image, ImageDraw, ImageFont
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
            
            # Захват скриншота графика с Binance и наложение анализа
            capture_and_annotate_chart(symbol, interval, close_prices, fibonacci_levels, signals)

def capture_and_annotate_chart(symbol, interval, close_prices, levels, signals):
    """Снимок экрана графика с Binance и наложение уровней Фибоначчи и сигналов"""
    # Настройки для Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    # Инициализация драйвера Chrome
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

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
    driver.quit()

    # Открытие скриншота для редактирования
    image = Image.open(filename)
    draw = ImageDraw.Draw(image)

    # Наложение уровней Фибоначчи и сигналов
    font = ImageFont.load_default()

    for level in levels:
        y = int(image.height * (1 - (levels[level] - min(close_prices)) / (max(close_prices) - min(close_prices))))
        draw.line((0, y, image.width, y), fill="yellow", width=2)
        draw.text((10, y), level, fill="yellow", font=font)

    for signal in signals:
        x = int(image.width * signal[1] / len(close_prices))
        y = int(image.height * (1 - (close_prices[signal[1]] - min(close_prices)) / (max(close_prices) - min(close_prices))))
        color = "green" if signal[0] == "Buy" else "red"
        draw.ellipse((x-5, y-5, x+5, y+5), fill=color)
        draw.text((x+10, y), signal[0], fill=color, font=font)

    # Сохранение скриншота с аннотациями
    annotated_filename = f"{symbol}_{interval}_annotated.png"
    image.save(annotated_filename)
    logging.info(f"Скриншот с аннотациями сохранен: {annotated_filename}")

def main():
    logging.basicConfig(filename='trading_screenshots.log', level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s')

    while True:
        analyze_market()
        time.sleep(60 * 15)  # Анализировать каждые 15 минут

if __name__ == '__main__':
    main()
