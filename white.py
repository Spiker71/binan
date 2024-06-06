import logging
import numpy as np
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
    symbols = ['BTCUSDT', 'ETHUSDT']  # Добавьте сюда нужные символы
    intervals = ['15', '60', '240', 'D']  # 15 мин, 1 час, 4 часа, 1 день

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=ChromeService(), options=options)
    driver.set_window_size(1920, 1080)

    for symbol in symbols:
        for interval in intervals:
            url = f'https://www.tradingview.com/chart/?symbol=BINANCE%3A{symbol.replace("USDT", "USDTPERP")}'
            logging.info(f"Opening URL: {url}")
            driver.get(url)
            time.sleep(10)  # Задержка для полной загрузки графика

            try:
                # Извлечение данных о ценах с графика
                logging.info(f"Extracting prices for {symbol} on {interval} interval")
                close_prices = extract_prices_from_chart(driver)
                if not close_prices:
                    logging.warning(f"No prices extracted for {symbol} on {interval} interval")
                    continue

                # Рассчет уровней Фибоначчи
                logging.info(f"Calculating Fibonacci levels for {symbol} on {interval} interval")
                fibonacci_levels = calculate_fibonacci_levels(close_prices)

                # Поиск точек входа
                logging.info(f"Finding trade signals for {symbol} on {interval} interval")
                signals = find_trade_signals(close_prices, fibonacci_levels)

                # Логирование сигналов
                for signal in signals:
                    if interval == '15':
                        logging.info(f"Signal: {signal[0]} at index {signal[1]} (price: {close_prices[signal[1]]}) for {symbol} on {interval}")
                        capture_chart_screenshot(driver, symbol, interval, signal, fibonacci_levels, close_prices)
            except Exception as e:
                logging.error(f"Error analyzing {symbol} on {interval}: {e}")

    driver.quit()

def extract_prices_from_chart(driver):
    """Извлечение цен закрытия с графика TradingView"""
    try:
        logging.info("Extracting prices from chart")
        # Предположим, что элемент, содержащий данные о ценах, имеет определенный CSS-селектор
        price_elements = driver.find_elements(By.CSS_SELECTOR, '.some-css-selector-for-prices')
        if not price_elements:
            logging.warning("No price elements found")
            return []

        prices = [float(element.text.replace(',', '')) for element in price_elements]
        logging.info(f"Extracted {len(prices)} prices")
        return prices
    except Exception as e:
        logging.error(f"Error extracting prices from chart: {e}")
        return []

def capture_chart_screenshot(driver, symbol, interval, signal, levels, prices):
    """Сделать скриншот графика с TradingView"""
    logging.info(f"Capturing chart screenshot for {symbol} on {interval}...")
    try:
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
        x = signal[1] * (width / len(prices))
        y = height - int((signal[2] - min(prices)) / (max(prices) - min(prices)) * height)
        color = 'green' if signal[0] == 'Buy' else 'red'
        draw.text((x, y), signal[0], fill=color, font=font)
        draw.rectangle([x-5, y-5, x+5, y+5], outline=color)

        # Определение ближайших уровней тейк-профита
        take_profit_1 = signal[2] + (levels['38.2%'] - levels['61.8%']) if signal[0] == 'Buy' else signal[2] - (levels['38.2%'] - levels['61.8%'])
        take_profit_2 = signal[2] + 2 * (levels['38.2%'] - levels['61.8%']) if signal[0] == 'Buy' else signal[2] - 2 * (levels['38.2%'] - levels['61.8%'])

        y_tp1 = height - int((take_profit_1 - min(prices)) / (max(prices) - min(prices)) * height)
        y_tp2 = height - int((take_profit_2 - min(prices)) / (max(prices) - min(prices)) * height)
        
        draw.line([(0, y_tp1), (width, y_tp1)], fill='green', width=1)
        draw.text((0, y_tp1), f'Take Profit 1 ({take_profit_1:.2f})', fill='green', font=font)
        
        draw.line([(0, y_tp2), (width, y_tp2)], fill='green', width=1)
        draw.text((0, y_tp2), f'Take Profit 2 ({take_profit_2:.2f})', fill='green', font=font)

        # Сохранение изображения
        image.save(f'screenshot_{symbol}_{interval}.png')
        logging.info(f"Screenshot saved: screenshot_{symbol}_{interval}.png")
    except Exception as e:
        logging.error(f"Error capturing screenshot for {symbol} on {interval}: {e}")

if __name__ == '__main__':
    analyze_market()
