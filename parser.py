from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

def get_player_status(nickname):
    url = f'https://vimetop.ru/player/{nickname}'
    
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        driver.get(url)
        
        try:
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "fa-spinner"))
            )
            
            status_element = driver.find_element(By.ID, "profile-session")
            status_text = status_element.text.strip()
            
            driver.quit()
            return status_text if status_text else "Оффлайн"
            
        except Exception as e:
            print(f"Ошибка ожидания статуса для {nickname}: {e}")
            driver.quit()
            return None
            
    except Exception as e:
        print(f"Ошибка Selenium для {nickname}: {e}")
        return None

# Тест
if __name__ == '__main__':
    status = get_player_status("")
    print(f"Статус: {status}")