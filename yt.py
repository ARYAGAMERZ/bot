import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

# YouTube live video URL
url = 'https://www.youtube.com/watch?v=d2AcBsKtizI'

# Set up the Chrome driver
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
service = Service('C:/Users/Nova/Downloads/Compressed/chromedriver-win64/chromedriver.exe')  # Make sure to replace with the path to your ChromeDriver

driver = webdriver.Chrome(service=service, options=options)
driver.get(url)

time.sleep(10)  # Wait for the page to load

# Scroll to load live chat
chat_box = driver.find_element(By.TAG_NAME, 'body')
for _ in range(3):
    chat_box.send_keys(Keys.PAGE_DOWN)
    time.sleep(2)

# Get live chat messages
def get_live_chat():
    messages = driver.find_elements(By.CSS_SELECTOR, 'yt-live-chat-text-message-renderer')
    for message in messages:
        try:
            author_name = message.find_element(By.CSS_SELECTOR, '#author-name').text
            message_text = message.find_element(By.CSS_SELECTOR, '#message').text
            print(f'{author_name}: {message_text}')
        except Exception as e:
            print(f"Error: {e}")

# Display live chat messages
while True:
    get_live_chat()
    time.sleep(5)
