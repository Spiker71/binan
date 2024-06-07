import logging
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import time
import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Установка параметров логирования
logging.basicConfig(filename='trading_signals.log', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Функция для ожидания видимости элемента на странице
def wait_for_element(driver, by, selector, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, selector))
        )
        return element
    except Exception as e:
        logging.error(f"Ошибка при ожидании элемента: {e}")
        return None

def analyze_market():
    """Основная функция для анализа рынка"""
    # Получение всех фьючерсных символов
    symbols = ['BTCUSD', 'ETHUSD']  # Пример символов для анализа
    
    for symbol in symbols:
        interval = '15'  # Анализируем только 15-минутные данные
        
        # Открываем TradingView с нужным символом и темной темой
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=ChromeService(), options=options)
        driver.set_window_size(1920, 1080)
        url = f'https://www.tradingview.com/chart/?symbol={symbol}&interval={interval}&theme=dark'
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
            width, height = image.size
            close_prices = np.random.rand(100)  # Вместо данных Binance используем случайные данные
            max_price = max(close_prices)
            min_price = min(close_prices)
            diff = max_price - min_price
            fibonacci_levels = {
                '0.0%': max_price,
                '23.6%': max_price - 0.236 * diff,
                '38.2%': max_price - 0.382 * diff,
                '50.0%': max_price - 0.5 * diff,
                '61.8%': max_price - 0.618 * diff,
                '100.0%': min_price
            }
            for level, price in fibonacci_levels.items():
                y = height - int((price - min_price) / diff * height)
                draw.line([(0, y), (width, y)], fill='blue', width=2)
                draw.text((0, y), f'{level} ({price:.2f})', fill='blue', font=font)
    
            # Рисуем сигналы Buy/Sell
            signals = [('Buy', 20, close_prices[20]), ('Sell', 50, close_prices[50])]  # Пример сигналов
            for signal in signals:
                x = signal[1] * (width / len(close_prices))
                y = height - int((signal[2] - min_price) / diff * height)
                color = 'green' if signal[0] == 'Buy' else 'red'
                draw.text((x, y), signal[0], fill=color, font=font)
                draw.rectangle([x - 5, y - 5, x + 5, y + 5], outline=color)
    
            # Находим индекс наилучшей точки входа
            best_entry_index = min(signals, key=lambda x: x[1])[1]
            best_entry_x = best_entry_index * (width / len(close_prices))
            best_entry_y = height - int((signals[best_entry_index][2] - min_price) / diff * height)
            draw.line([(best_entry_x, best_entry_y), (best_entry_x, 0)], fill='yellow', width=2)
        
            # Находим оптимальные уровни тейк-профитов
            take_profit_1 = signals[best_entry_index][2] + (fibonacci_levels['38.2%'] - fibonacci_levels['61.8%']) if signals[best_entry_index][0] == 'Buy' else signals[best_entry_index][2] - (fibonacci_levels['38.2%'] - fibonacci_levels['61.8%'])
            take_profit_2 = signals[best_entry_index][2] + 2 * (fibonacci_levels['38.2%'] - fibonacci_levels['61.8%']) if signals[best_entry_index][0] == 'Buy' else signals[best_entry_index][2] - 2 * (fibonacci_levels['38.2%'] - fibonacci_levels['61.8%'])
        
            # Нарисуем линии для тейк-профитов
            take_profit_1_y = height - int((take_profit_1 - min_price) / diff * height)
            take_profit_2_y = height - int((take_profit_2 - min_price) / diff * height)
            draw.line([(0, take_profit_1_y), (width, take_profit_1_y)], fill='green', width=2)
            draw.line([(0, take_profit_2_y), (width, take_profit_2_y)], fill='orange', width=2)
        
            # Сохраняем изображение
            image.save(f'{symbol}_{interval}_screenshot.png')
            
        except Exception as e:
            logging.error(f"Ошибка при анализе рынка для символа {symbol}: {e}")
        finally:
            driver.quit()

if __name__ == "__main__":
    analyze_market()
