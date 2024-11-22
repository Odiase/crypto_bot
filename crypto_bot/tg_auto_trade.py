import time
import psycopg2
from selenium import webdriver
from bs4 import BeautifulSoup
import chromedriver_autoinstaller
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import date
from urllib.parse import urlparse, parse_qs, unquote


class TokenDatabase:
    def __init__(self, max_retries=5, retry_delay=5):
        '''Initialize Database Connection with Retry Mechanism'''
        # Parse the connection URL
        self.config = self.parse_db_url("postgresql://elontrustsdb3_user:V2GclU6nnhoYFM9Mn1w9qHiXv6z1iQze@dpg-csvl53l6l47c73do62dg-a.oregon-postgres.render.com/elontrustsdb3", ssl_require=True)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.conn = self.connect_with_retry()

    def parse_db_url(self, url, ssl_require=False):
        parsed_config = {}

        spliturl = urlparse(url)

        path = spliturl.path[1:]
        query = parse_qs(spliturl.query)

        hostname = spliturl.hostname or ""
        if "%" in hostname:
            hostname = spliturl.netloc
            if "@" in hostname:
                hostname = hostname.rsplit("@", 1)[1]
            hostname = unquote(hostname)

        port = spliturl.port

        parsed_config.update(
            {
                "NAME": unquote(path or ""),
                "USER": unquote(spliturl.username or ""),
                "PASSWORD": unquote(spliturl.password or ""),
                "HOST": hostname,
                "PORT": port or 5432,
            }
        )

        if ssl_require:
            parsed_config["sslmode"] = "require"

        return parsed_config

    def connect_with_retry(self):
        '''Attempt to establish a database connection with retries'''
        attempt = 0
        while attempt < self.max_retries:
            try:
                conn = psycopg2.connect(
                    database=self.config["NAME"],
                    user=self.config["USER"],
                    password=self.config["PASSWORD"],
                    host=self.config["HOST"],
                    port=self.config["PORT"],
                    sslmode=self.config.get("sslmode", "")
                )
                return conn
            except psycopg2.OperationalError as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                attempt += 1
                time.sleep(self.retry_delay)
        raise Exception("Max retries exceeded, failed to connect to the database")

    def create_token_record_table(self):
        '''Create the Table that holds record for Trade orders'''
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS token_records (
                id SERIAL PRIMARY KEY,
                contract_address VARCHAR(200) NOT NULL,
                buy_status VARCHAR(10) DEFAULT 'UNBOUGHT',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()
        cur.close()

    def check_buy_status(self, contract_address):
        '''Check the buy status of a token by its contract address'''
        cur = self.conn.cursor()
        cur.execute("""
            SELECT buy_status FROM token_records WHERE contract_address = %s;
        """, (contract_address,))
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0] == 'BOUGHT'
        return False

    def register_token_record(self, contract_address):
        '''Register a new token record'''
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO token_records (contract_address) VALUES (%s)
            ON CONFLICT (contract_address) DO NOTHING;
        """, (contract_address,))
        self.conn.commit()
        cur.close()

    def set_token_as_bought(self, contract_address):
        '''Set the buy status of a token to "BOUGHT" by its contract address'''
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE token_records
            SET buy_status = 'BOUGHT'
            WHERE contract_address = %s;
        """, (contract_address,))
        self.conn.commit()
        cur.close()

    def get_unbought_tokens(self):
        '''Retrieve tokens with buy_status UNBOUGHT'''
        cur = self.conn.cursor()
        cur.execute("""
            SELECT contract_address FROM token_records WHERE buy_status = 'UNBOUGHT';
        """)
        tokens = cur.fetchall()
        cur.close()
        return [token[0] for token in tokens]

    def close(self):
        '''Close the database connection'''
        self.conn.close()


def initDriver():
    '''Starting Webdriver'''
    chromedriver_autoinstaller.install()
    options = Options()
    # options.add_argument("--no-sandbox")
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
    # options.add_argument("--disable-software-rasterizer")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(options=options)
    return driver

def getElement(driver, wait_time, element_locator, quantity_type):
    '''Gets an element or list of Elements from a page'''
    try:
        wait = WebDriverWait(driver, wait_time)

        if quantity_type == "single":
            element = wait.until(EC.presence_of_element_located(element_locator))
            return element
        elif quantity_type == "multiple":
            elements = wait.until(EC.presence_of_all_elements_located(element_locator))
            return elements
    except Exception as e:
        print(e)


def openTelegram(driver):
    '''Opens Web Telegram'''
    driver.get("https://web.telegram.org/")
    time.sleep(20)
    log_in_with_phone_number_el = getElement(driver, 60, (By.TAG_NAME, 'button'),"single")
    log_in_with_phone_number_el.click()
    print("Opened Telegram.")
    # input("")

# def clickBuyButton(driver):
#     '''Clicks the buy button in the UNIBOT reply interface'''
#     try:
#         # Start from the 'MessageList' class
#         message_list = getElement(driver, 30, (By.CLASS_NAME, 'MessageList'), 'single')

#         # Find the 'messages-container' class within 'MessageList'
#         messages_container = message_list.find_element(By.CLASS_NAME, 'messages-container')

#         # Find the 'message-date-group' class within 'messages-container'
#         message_date_group = messages_container.find_element(By.CLASS_NAME, 'message-date-group')

#         # Get the last 'message-list-item' class within 'message-date-group'
#         message_list_items = message_date_group.find_elements(By.CLASS_NAME, 'message-list-item')
#         last_message_list_item = message_list_items[-1]

#         # Find the 'message-content-wrapper' class within the last 'message-list-item'
#         message_content_wrapper = last_message_list_item.find_element(By.CLASS_NAME, 'message-content-wrapper')

#         # Find the 'InlineButtons' class within 'message-content-wrapper'
#         inline_buttons = message_content_wrapper.find_element(By.CLASS_NAME, 'InlineButtons')

#         # Get the last 'row' class within 'InlineButtons'
#         rows = inline_buttons.find_elements(By.CLASS_NAME, 'row')
#         last_row = rows[-1]

#         # Click the button element under the last 'row'
#         button = last_row.find_element(By.TAG_NAME, 'button')
#         button.click()
#         print("Buy ButtonClicked")
#         return True
#     except Exception as e:
#         print("First Approach Failed!")
#         print(e)
#          print(f"First approach failed: {e1}")
#                 # Second approach
#                 try:
#                     whole = getElement(driver, 30, (By.ID, "page-chats"), "single")
#                     print('Gotten Whole')
#                     main_columns = whole.find_element(By.ID, "main-columns")
#                     print("Gotten Main Columns")
#                     column_left = main_columns.find_element(By.ID, "column-center")
#                     chat_container = column_left.find_element(By.CLASS_NAME, "chats-container")
#                     print("Gotten Chat Container")
#                     chat = chat_container.find_element(By.CLASS_NAME, "chat")
#                     bubbles = chat.find_element(By.CLASS_NAME, "bubbles")
#                     scrollable = bubbles.find_element(By.CLASS_NAME, "scrollable")
#                     bubbles_inner = scrollable.find_element(By.CLASS_NAME, "bubbles-inner")
#                     bubbles_date_group = bubbles_inner.find_element(By.CLASS_NAME, "bubbles-date-group")
#                     bubble_group = bubbles_date_group.find_elements(By.CLASS_NAME, "bubble-group")[-1]
#                     bubble_content_wrapper = bubble_group.find_element(By.CLASS_NAME, "bubble-content-wrapper")
#                     reply_markup = bubble_content_wrapper.find_element(By.CLASS_NAME, "reply-markup")
#                     reply_markup_row = reply_markup.find_elements(By.CLASS_NAME, "reply-markup-row")[-1]
#                     buy_button = reply_markup_row.find_element(By.TAG_NAME, "button")
#                     buy_button.click()
#                     print("Clicked buy button using second approach.")
#                     return True
#                 except Exception as e2:
#                     print(f"Second approach failed: {e2}")
#         return False

def clickBuyButton(driver, retries=3):
    '''Clicks the buy button in the UNIBOT reply interface'''
    print("In Click Buy Function.")
    attempt = 0
    while attempt < retries:
        try:
            # First approach
            try:
                middle_column = getElement(driver, 30, (By.ID, 'MiddleColumn'), "single")
                print("Middle Column : ", middle_column)

                messages_layout = middle_column.find_element(By.CLASS_NAME, 'messages-layout')
                print(messages_layout.get_attribute('innerHTML'))
                
                transition = messages_layout.find_elements(By.XPATH, "./div")[1]

                transition_slide = transition.find_element(By.CLASS_NAME, "Transition_slide")
                
                # message_list = transition_slide.find_element(By.CLASS_NAME, 'custom-scroll')#'MessageList')
                print("Got Tansition Slide.")
                print(transition_slide.get_attribute('innerHTML'))
                messages_container = transition_slide.find_element(By.CLASS_NAME, 'messages-container')
                print("Got messages container")

                message_date_group = messages_container.find_element(By.CLASS_NAME, 'message-date-group')

                message_list_items = message_date_group.find_elements(By.CLASS_NAME, 'message-list-item')
                last_message_list_item = message_list_items[-1]

                message_content_wrapper = last_message_list_item.find_element(By.CLASS_NAME, 'message-content-wrapper')

                inline_buttons = message_content_wrapper.find_element(By.CLASS_NAME, 'InlineButtons')

                rows = inline_buttons.find_elements(By.CLASS_NAME, 'row')
                last_row = rows[-1]

                button = last_row.find_element(By.TAG_NAME, 'button')
                button.click()
                print("Clicked buy button using first approach.")
                return True
            except Exception as e1:
                print(f"First approach failed: {e1}")
                # Second approach
                try:
                    whole = getElement(driver, 30, (By.ID, "page-chats"), "single")
                    print('Gotten Whole')
                    main_columns = whole.find_element(By.ID, "main-columns")
                    column_left = main_columns.find_element(By.ID, "column-center")
                    chat_container = column_left.find_element(By.CLASS_NAME, "chats-container")
                    chat = chat_container.find_element(By.CLASS_NAME, "chat")
                    bubbles = chat.find_element(By.CLASS_NAME, "bubbles")
                    scrollable = bubbles.find_element(By.CLASS_NAME, "scrollable")
                    bubbles_inner = scrollable.find_element(By.CLASS_NAME, "bubbles-inner")
                    print("Bubble inner past.")
                    bubbles_date_group = bubbles_inner.find_elements(By.CLASS_NAME, "bubbles-date-group")[-1]
                    
                    print("Gotten to bubble date group recent one")
                    bubble_group = bubbles_date_group.find_element(By.CLASS_NAME, "bubbles-group-last")
                    print("Passed bubble date group")
                    bubble_content_wrapper = bubble_group.find_element(By.CLASS_NAME, "bubble-content-wrapper")
                    print("Passed bubblecontent wrapper")
                    reply_markup = bubble_content_wrapper.find_element(By.CLASS_NAME, "reply-markup")
                    print("In Reply Markup")
                    reply_markup_row = reply_markup.find_elements(By.CLASS_NAME, "reply-markup-row")
                    buy_button = reply_markup_row[len(reply_markup_row) - 1].find_element(By.TAG_NAME, "button")
                    buy_button.click()
                    print("Clicked buy button using second approach.")
                    return True
                except Exception as e2:
                    print(f"Second approach failed: {e2}")

            # If both approaches fail, retry
            attempt += 1
            time.sleep(5)  # Wait before retrying
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            attempt += 1
            time.sleep(5)  # Wait before retrying
    print("All attempts failed.")
    input()
    return False

    
def interactWithUnibot(driver, token):
    '''Sends Texts And Clicks Buttons On Unibot Solana'''
    print(f"Interacting With UNIBOT to buy token {token}.")

    # Focus the text field by sending a space key
    body = driver.find_element(By.TAG_NAME, 'body')
    body.send_keys(Keys.SPACE)
    time.sleep(1)
    active_element = driver.switch_to.active_element
    message = f"buy {token}"
    active_element.send_keys(message)
    active_element.send_keys(Keys.ENTER)
    
    time.sleep(5)
    clicked_buy_button = clickBuyButton(driver)
    return clicked_buy_button

def runBot():
    driver = initDriver()
    db = TokenDatabase()
    print(db.get_unbought_tokens())

    openTelegram(driver)
    time.sleep(120)  # Allow time for manual login

    try:
        while True:
            unbought_tokens = db.get_unbought_tokens()
            for token in unbought_tokens:
                if not db.check_buy_status(token):
                    success = interactWithUnibot(driver, token)
                    if success:
                        db.set_token_as_bought(token)
            time.sleep(20)  # Wait for 20 seconds before checking again
    finally:
        db.close()
        driver.quit()
runBot()
