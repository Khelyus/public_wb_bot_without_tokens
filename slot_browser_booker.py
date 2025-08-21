from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

SUPPLY_ID = "39434885"
TARGET_DATES = ["13", "14", "15"]  # Дни месяца июня 2025

def book_slot_via_browser(cookies_path="cookies.txt"):
    chrome_options = Options()
    chrome_options.headless = False  # Отключаем headless для отладки
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # ✅ Используем профиль Chrome, где уже авторизован аккаунт Gmail/WB
    profile_path = "C:/Users/Acer/AppData/Local/Google/Chrome/User Data"
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_argument("--profile-directory=Default")  # Профиль по умолчанию

    driver = webdriver.Chrome(options=chrome_options)

    print("📂 Запущен профиль Chrome. Загружаем Google для проверки...")
    driver.get("https://google.com")

    # Закрыть все лишние вкладки, оставить одну
    if len(driver.window_handles) > 1:
        for handle in driver.window_handles[1:]:
            driver.switch_to.window(handle)
            driver.close()
        driver.switch_to.window(driver.window_handles[0])
    input("🔍 Убедись, что нужный аккаунт авторизован. Нажми Enter для продолжения...")

    try:
        print("🔐 Открываем страницу Wildberries")
        driver.get(f"https://seller.wildberries.ru/supplies-management/all-supplies/supply-detail?preorderId={SUPPLY_ID}&supplyId")
        print("🌐 Переход на страницу Wildberries поставок")
        input("⏸ Проверь, действительно ли открылся список поставок. Нажми Enter для продолжения...")
        time.sleep(3)

        # Проверка авторизации
        if "login" in driver.current_url or "signin" in driver.current_url:
            print("❌ Не авторизован. Проверь профиль Chrome")
            return False

        print("🔍 Переход к управлению поставками")
        driver.get("https://seller.wildberries.ru/supplies-management/all-supplies")
        wait = WebDriverWait(driver, 15)
        time.sleep(5)

        # Клик по кнопке "Запланировать поставку"
        plan_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Запланировать поставку')]")))
        plan_button.click()
        time.sleep(2)

        print("📅 Нажимаем 'Запланировать поставку'")
        book_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Запланировать поставку')]")))
        book_btn.click()
        time.sleep(3)

        print("🔄 Поиск доступных слотов на 13–15 июня")
        calendar_buttons = []
        for day in TARGET_DATES:
            try:
                button = driver.find_element(By.XPATH, f"//button[contains(text(), '{day}') and not(@disabled)]")
                calendar_buttons.append(button)
            except Exception as e:
                print(f"⚠️ Не удалось найти кнопку на {day} июня: {e}")
                continue

        for button in calendar_buttons:
            try:
                print(f"👉 Пробуем выбрать дату: {button.text}")
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(0.5)
                button.click()
                time.sleep(1)

                choose_btn = driver.find_element(By.XPATH, "//button[contains(., 'Выбрать')]")
                choose_btn.click()
                time.sleep(1)

                confirm_btn = driver.find_element(By.XPATH, "//button[contains(., 'Запланировать')]")
                confirm_btn.click()

                print(f"✅ Слот успешно забронирован на дату {button.text} июня.")
                return True
            except Exception as e:
                print(f"⚠️ Не удалось выбрать слот: {e}")
                continue

        print("❌ Не удалось забронировать слот на указанные даты.")
        return False

    finally:
        driver.quit()
