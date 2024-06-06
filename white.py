import logging
import numpy as np
from binance.client import Client
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import time
import datetime

# Установка параметров логирования
logging.basicConfig(filename='trading_signals.log', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Создание клиента Binance
client = Client()

def get_historical_klines(symbol, interval, start_str):
    """Получение исторических данных"""
    klines = client.futures_klines(symbol=symbol, interval=interval, startTime=start_str)
    return klines

# Остальные функции (calculate_fibonacci_levels, find_trade_signals, analyze_market) остаются без изменений

# Функция для ожидания видимости элемента на странице
def wait_for_element(driver, by, selector, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, selector))
        )
        return element
    except Exception as e:
        print(f"Ошибка при ожидании элемента: {e}")
        return None

# Функция для создания скриншота с улучшениями
def capture_chart_screenshot(symbol, interval, signals, levels, prices):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=ChromeService(), options=options)
    driver.set_window_size(1920, 1080)
    
    # Открываем TradingView с нужным символом
    url = f'https://www.tradingview.com/chart/?symbol=BINANCE%3A{symbol.replace("USDT", "USDTPERP")}'
    driver.get(url)
    
    try:
        # Ждем, пока график станет видимым
        chart_element = wait_for_element(driver, By.CSS_SELECTOR, 'canvas')
        if chart_element is None:
            return
        
        # Дожидаемся полной загрузки графика
        time.sleep(5)

        # Создаем скриншот
        screenshot = chart_element.screenshot_as_png
        image = Image.open(BytesIO(screenshot))

        # Добавляем уровни Фибоначчи на скриншот
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        
        # Рисуем уровни Фибоначчи
        for level, price in levels.items():
            y = height - int((price - min(prices)) / (max(prices) - min(prices)) * height)
            draw.line([(0, y), (width, y)], fill='blue', width=2)
            draw.text((0, y), f'{level} ({price:.2f})', fill='blue', font=font)
        
        # Рисуем сигналы Buy/Sell
        for signal in signals:
            x = signal[1] * (width / len(prices))
            y = height - int((signal[2] - min(prices)) / (max(prices) - min(prices)) * height)
            color = 'green' if signal[0] == 'Buy' else 'red'
            draw.text((x, y), signal[0], fill=color, font=font)
            draw.rectangle([x-5, y-5, x+5, y+5], outline=color)
        
        # Сохраняем скриншот
        image.save(f'{symbol}_{interval}_screenshot.png')
    except Exception as e:
        print(f"Ошибка при создании скриншота: {e}")
    finally:
        driver.quit()

def main():
    while True:
        analyze_market()
        time.sleep(60 * 15)  # анализировать каждые 15 минут

if __name__ == '__main__':
    main()
