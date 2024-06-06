import logging
import numpy as np
from binance.client import Client
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageDraw, ImageFont
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
    klines = client.futures_klines(symbol=symbol, interval=interval, startTime=start_str)
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
            signals.append(('Buy', i, levels['38.2%']))
        elif data[i-1] < levels['61.8%'] and data[i] >= levels['61.8%']:
            signals.append(('Sell', i, levels['61.8%']))
    return signals

def analyze_market():
    """Основная функция для анализа рынка"""
    # Получение всех фьючерсных символов
    futures_info = client.futures_exchange_info()
    symbols = [s['symbol'] for s in futures_info['symbols'] if s['quoteAsset'] == 'USDT']
    intervals = [Client.KLINE_INTERVAL_15MINUTE, Client.KLINE_INTERVAL_1HOUR]

    for symbol in symbols:
        for interval in intervals:
            start_str = int((datetime.datetime.now() - datetime.timedelta(days=30)).timestamp() * 1000)

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
            
            # Делание скриншота графика
            capture_chart_screenshot(symbol, interval, signals, fibonacci_levels, close_prices)

def capture_chart_screenshot(symbol, interval, signals, levels, prices):
    """Сделать скриншот графика с TradingView"""
    options = Options()
    # options.add_argument('--headless')  # Для отладки отключим headless режим
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=ChromeService(), options=options)
    driver.set_window_size(1920, 1080)
    
    # Открытие TradingView с графиком
    url = f'https://www.tradingview.com/chart/?symbol=BINANCE%3A{symbol.replace("USDT", "USDTPERP")}'
    driver.get(url)
    
    try:
        # Ждем, пока элемент станет видимым
        chart_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'canvas'))
        )
        time.sleep(5)  # Задержка для полной загрузки графика
        screenshot = chart_element.screenshot_as_png
        image = Image.open(BytesIO(screenshot))

        # Рисование сигналов на скриншоте
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        
        # Определение размеров изображения
        width, height = image.size
        
        # Рисование уровней Фибоначчи
        for level, price in levels.items():
            y = height - int((price - min(prices)) / (max(prices) - min(prices)) * height)
            draw.line([(0, y), (width, y)], fill='blue', width=2)
            draw.text((0, y), f'{level} ({price:.2f})', fill='blue', font=font)
        
        # Рисование сигналов Buy/Sell
        for signal in signals:
            x = signal[1] * (width / len(prices))
            y = height - int((signal[2] - min(prices)) / (max(prices) - min(prices)) * height)
            color = 'green' if signal[0] == 'Buy' else 'red'
            draw.text((x, y), signal[0], fill=color, font=font)
            draw.rectangle([x-5, y-5, x+5, y+5], outline=color)
        
        # Сохранение изображения
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
