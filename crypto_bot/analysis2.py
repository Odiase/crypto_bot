import time
import requests
import logging
import psycopg2

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.proxy import Proxy, ProxyType
from urllib.parse import urlparse, parse_qs, unquote
import chromedriver_autoinstaller


logging.basicConfig(level=logging.INFO)

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.154 Safari/537.36"

## DATABASE CODE
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
    

    def token_exists(self, contract_address):
        '''Check if a token record exists in the database by its contract address'''

        cur = self.conn.cursor()
        cur.execute("""
            SELECT 1 FROM token_records WHERE contract_address = %s;
        """, (contract_address,))
        exists = cur.fetchone() is not None
        cur.close()
        return exists


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







































def sendTelegramMessage(message):
    message = str(message)
    TOKEN = "6592918138:AAEWmvPEgFAJ4-dctj0-XM1xmzkauN3L8sA"
    # chat_id = "-1002001136974"
    chat_id = "-1002049858126"
    parameters = {
        "chat_id" : chat_id,
        "text" : message
    }

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"#?chat_id={chat_id}&text={message}"
    request = requests.get(url, data=parameters)



def is_over_1000(subscribers_str):
    cleaned_str = ''.join(filter(str.isdigit, subscribers_str))
    try:
        subscribers_count = int(cleaned_str)
    except ValueError:
        print("Invalid input. Please provide a valid subscriber count.")
        return False

    if subscribers_count > 1000:
        print("Over a 1000")
        return True
    else:
        print("not over")
        return False


def elementInteractor(wait_time, element_locator, action, key_value):
    '''Interacts With Elements on a page'''
    try:
        wait = WebDriverWait(driver, wait_time)
        if action == "ad":
            elements = wait.until(EC.presence_of_all_elements_located(element_locator))# this code is not running
            [element.click() for element in elements] # this code is not running
        else:
            if key_value == "chain_dropdown":
                print("sleeping")
                time.sleep(5)
            element = wait.until(EC.element_to_be_clickable(element_locator))
            time.sleep(3)
            if action == "click":
                element.click()
            elif action == "send_keys":
                element.send_keys(key_value)
    except Exception as e:
        print(e)


def elementScraper(wait_time, element_locator, quantity_type):
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




def openFilterSection(driver):
    '''Getting the filter sidebar open'''

    # Retry mechanism
    max_attempts = 3
    attempt = 1
    wait = WebDriverWait(driver, 60)

    while attempt <= max_attempts:
        try:
            element_locator = (By.CLASS_NAME, "custom-filters")
            element = wait.until(EC.element_to_be_clickable(element_locator))
            print("filter tab element : ", element)
            # Scroll the element into view
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(5)
            element.click()
        except Exception as e:
            print(e)
            attempt += 1
    print("opened filter tab")


def enterFilterData(driver, minLiquidity, maxMarketCap, poolCreated):
    '''Inputting filter data for the tokens'''
    print("In ENter Filter Data Function")

    #radio buttons interactions
    radio_btn1 = elementInteractor(30, (By.ID, "excludeNative"), "click", "none")
    radio_btn2 = elementInteractor(30, (By.ID, "socialInfo"), "click", "none")

    #dropdown interactions
    chain_dropdown = elementInteractor(120, (By.CSS_SELECTOR, ".chain-selector button"), "click", "")
    chains = elementScraper(60, (By.CSS_SELECTOR, ".chain-selector .chain"), "multiple")
    chains[3].click()
    # chain_selection = retryElementInteractor((By.CLASS_NAME, "button-selected"))

    print("AFter Dropdown in Enter Filter Data Function")
    # form inputs
    min_liquidity = elementInteractor(60, (By.CSS_SELECTOR, "[formcontrolname='minLiquidity']"), "send_keys", f"{minLiquidity}")
    max_market_cap = elementInteractor(60,(By.CSS_SELECTOR, "[formcontrolname='maxFdv']"), "send_keys", f"{maxMarketCap}")
    pool_created = elementInteractor(60,(By.CSS_SELECTOR, "[formcontrolname='poolCreatedUnit']"), "send_keys", f"{poolCreated}")

    #pool dropdowns
    # wrapper = driver.find_elements(By.CLASS_NAME, "item-select-wrapper")[3]
    # wrapper.click()
    # d_list = driver.find_element(By.CSS_SELECTOR, ".dropdown-list")
    # print("D LIST : ", d_list.get_attribute('innerHTML'))
    # span_hours = d_list.find_elements(By.CLASS_NAME, "ng-star-inserted")[2]
    # span_hours.click()
    #pool dropdowns
    pool_section_element = driver.find_element(By.CLASS_NAME, "pool-created")
    wrapper = pool_section_element.find_element(By.CLASS_NAME, "item-days")
    wrapper.click()
    d_list = driver.find_element(By.CSS_SELECTOR, ".dropdown-list")
    # Find all button elements under d_list
    time_buttons = d_list.find_elements(By.TAG_NAME, "button")
    time_buttons[1].click()
    

    #submit
    submit_btn = elementInteractor(30, (By.CSS_SELECTOR, ".panel-footer > .btn"), "click", "none")
    print("Filter Data Entered Successfully")


def getTelegramFollowers():
    '''Get Telegram Followers'''
    print("In Get Telegram followers function")
    try:
        social_link_elements = elementScraper(30, (By.CSS_SELECTOR, "#socials li"),"multiple")
        telegram_link = social_link_elements[3].find_element(By.TAG_NAME, "a").get_attribute('href')
        if "t.me" in telegram_link:
            # Send an HTTP GET request to the channel URL
            response = requests.get(telegram_link)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the HTML content of the response
                soup = BeautifulSoup(response.content, "html.parser")

                followers_element = soup.find("div", class_="tgme_page_extra")

                # Extract the follower count text
                print(followers_element)
                follower_count = followers_element.get_text() if followers_element else "Telegram Link Not found"

                print("Follower count:", follower_count.split(',')[0])
                return follower_count.split(',')[0]
            else:
                print("Failed to retrieve page. Status code:", response.status_code)
        return "No Telegram Provided."
    except Exception as e:
        print(e)
        return "Telegram Link not provided, chi"



def tokenPageDataExtraction(driver):
    '''Extracting Token Information from the SINGLE_TOKEN page'''

    try:
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(5)

        print("broke here 1")
        token_data_list = elementScraper(60, (By.CSS_SELECTOR, ".pool-info__list > li"), "multiple")
        token_price = elementScraper(60, (By.CLASS_NAME, "big-price"), "single").text
        contract_address_element = elementScraper(60, (By.CSS_SELECTOR, ".pool-info__info .token-pair-info .link"),"single")
        contract_address = contract_address_element.get_attribute('href').split('token/')[1]

        holders = token_data_list[3].text

        if "K" in holders or "k" in holders:
            followers = getTelegramFollowers()
            if is_over_1000(followers):
                token_name = elementScraper(10, (By.CLASS_NAME, "token-name-container"), "single").text
                data = {
                    'token_name': token_name,
                    "contract_address": contract_address,
                    "token_price": token_price,
                    'market_cap': str(token_data_list[0].text),
                    'liquidity': str(token_data_list[1].text),
                    'circ_supply': str(token_data_list[2].text),
                    'holders': holders.split('HOLDERS')[1],
                    'total_market_cap': str(token_data_list[4].text),
                    '24h_volume': str(token_data_list[5].text),
                    'total_supply': str(token_data_list[6].text),
                    "telegram_followers":  followers
                }
                db = TokenDatabase()
                if db.token_exists(contract_address):
                    print("Token ALready Exists")
                    pass
                else:
                    db.register_token_record(contract_address)
                    print('New Token Registered.')
                return data
            return {}
        else:
            driver.execute_script("window.scrollTo(0, 0);")
            return {}
    except Exception as e:
        print(e)
        return {}



def retry_wrapper(func, max_attempts=3, *args, **kwargs):
    '''Retries a function on failure up to max_attempts times'''
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.warning(f"Attempt {attempt} failed for {func.__name__}: {e}")
            if attempt == max_attempts:
                logging.error(f"Exceeded maximum attempts for {func.__name__}")
                raise



def scrapeTableData(driver, filter_number):
    '''Extracting the Tokens from the table'''
    # token_elements = retry_wrapper(driver.find_elements, By.CLASS_NAME, "datatable-row-wrapper")
    token_elements = driver.find_elements(By.CLASS_NAME, "datatable-row-wrapper")

    if not token_elements:
        sendTelegramMessage(f"FILTER {filter_number} \n No Result Found")
        driver.get("https://dextools.io/app/en/pairs")
        return []

    driver.execute_script("arguments[0].scrollIntoView(true);", token_elements[0])
    time.sleep(5)

    # Step 2: Save href links of the tokens in a list
    token_links = []
    for token_element in token_elements[:4]:
        try:
            # Extract the link (href attribute) from the <a> tag
            token_link = token_element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            token_links.append(token_link)
        except Exception as e:
            logging.error(f"Error while extracting link: {e}")
            continue

    # Step 3: Iterate over each token link and process the token pages
    token_data = []

    for token_link in token_links:
        try:
            # Step 4: Navigate to the token page using its URL
            driver.get(token_link)
            time.sleep(3)
            # Step 5: Extract token data from the token page
            data = tokenPageDataExtraction(driver)
            if data:
                token_data.append(data)

        except Exception as e:
            logging.error(f"Error while scraping token {token_link}: {e}")
            continue

    # Step 7: Handle case if no tokens are found from the filter
    if not token_data:
        sendTelegramMessage(f"No Tokens Found From Filter {filter_number}")

    driver.get("https://dextools.io/app/en/pairs")
    return token_data



def formatData(tokens_data, filter_number):
    message = f"FILTER {filter_number}\n\n"

    for token in tokens_data:
        if "msg" in token.keys():
            message = token["msg"]
        else:
            formatted_data = {
                'TOKEN': token['token_name'].replace('\n/\n', '(').replace('\n', '').capitalize(),
                'Price' : token['token_price'].replace('\n', '').lower(),
                'CA' : token['contract_address'],
                'Market Cap': token['market_cap'].replace('MARKET CAP\n', '').lower(),
                'Liquidity': token['liquidity'].replace('LIQUIDITY\n', '').lower(),
                'Circulating Supply': token['circ_supply'].replace('CIRC. SUPPLY\n', '').lower(),
                'Holders': token['holders'].replace('\n', '').lower(),
                'Total Supply': token['total_supply'].replace('TOTAL SUPPLY\n', '').lower(),
                'Followers' : str(token['telegram_followers']).split(",")[0]
            }
            for key, value in formatted_data.items():
                message += f"{key} - {value}\n"
        message += "\n\n\n\n"

        sendTelegramMessage(message)
        time.sleep(5)
    return



def enterFilterCriteria(driver, minLiquidity, maxMarketCap, poolCreated, filter_number):
    '''Orchestrating Filter Inputs and Data Extraction'''
    print("Opening Filter TAb")
    openFilterSection(driver)
    print("opened filter data")
    enterFilterData(driver, minLiquidity, maxMarketCap, poolCreated)

    #time for tokens
    time.sleep(120)
    token_data = scrapeTableData(driver, filter_number)
    if token_data:
        formatData(token_data, filter_number)



def initDriver():
    '''Initializes the Chrome WebDriver with error handling'''
    try:
        chromedriver_autoinstaller.install()
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        # options.add_argument("--headless")  # Uncomment for headless mode
        driver_service = Service()
        driver = webdriver.Chrome(service=driver_service, options=options)
        logging.info("WebDriver initialized successfully.")
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        raise


def close_ads():
    '''Closes ads if any pop up'''
    ad_locators = [
        (By.CLASS_NAME, "css-ppvcd6"),
        (By.CSS_SELECTOR, "[aria-label='Close']")
    ]
    for locator in ad_locators:
        elementInteractor(30, locator, "ad", None)

def main():
    global driver
    driver = initDriver()
    driver.get("https://dextools.io/app/en/pairs")
    
    # Close ads if any pop up
    # try:
    #     close_ads()
    # except:
    #     pass

    # Run the filters
    filter_criteria = [
        {'minLiquidity': 10000, 'maxMarketCap': 100000, 'poolCreated': 10, 'filter_number': '1'},
        {'minLiquidity': 100000, 'maxMarketCap': 1000000, 'poolCreated': 24, 'filter_number':'2'}
    ]

    for criteria in filter_criteria:
        # if openFilterSection(driver):
        if True:
            enterFilterCriteria(driver, criteria['minLiquidity'], criteria['maxMarketCap'], criteria['poolCreated'], criteria['filter_number'])

    # driver.quit()
    print("Script completed.")

while True:
    main()
    time.sleep(300)
