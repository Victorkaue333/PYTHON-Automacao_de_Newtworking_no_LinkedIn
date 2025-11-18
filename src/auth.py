from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from .config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD

def linkedin_login(driver):
    driver.get('https://www.linkedin.com/login')
    time.sleep(2)
    email_input = driver.find_element(By.ID, 'username')
    password_input = driver.find_element(By.ID, 'password')
    email_input.send_keys(LINKEDIN_EMAIL)
    password_input.send_keys(LINKEDIN_PASSWORD)
    password_input.send_keys(Keys.RETURN)
    time.sleep(3)
    # Verifica se login foi bem-sucedido
    if 'feed' in driver.current_url:
        return True
    return False
