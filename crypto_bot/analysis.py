import time
import requests


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
import chromedriver_autoinstaller
# from pyvirtualdisplay import Display
# display = Display(visible=0, size=(800, 800))  
# display.start()

chromedriver_autoinstaller.install() 
chrome_options = webdriver.ChromeOptions()    
# Add your options as needed    
options = [
  # Define window size here
#    "--window-size=1200,1200",
    "--ignore-certificate-errors"
 
    "--headless",
    #"--disable-gpu",
    #"--window-size=1920,1200",
    #"--ignore-certificate-errors",
    #"--disable-extensions",
    #"--no-sandbox",
    #"--disable-dev-shm-usage",
    #'--remote-debugging-port=9222'
]

for option in options:
    chrome_options.add_argument(option)

# driver_manager = ChromeDriverManager().install()
# print("Driver MAnager : ", driver_manager)
# PATH_TO_CHROME_DRIVER = "chromedriver.exe"

# service = Service(executable_path=PATH_TO_CHROME_DRIVER)
driver = webdriver.Chrome(options=chrome_options)

# driver.get('http://github.com')
# print(driver.title)
# with open('./GitHub_Action_Results.txt', 'w') as f:
#     f.write(f"This was written with a GitHub action {driver.title}")
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

proxy_options = {
    'proxy': {
        'https': 'https://4MumepfuHu2A8wbm:wifi;jp;;tokyo;@192.168.10.100:8888',
    }
}


driver.get("https://www.dextools.io/app/en/pairs")
# driver.get("https://currencystrengthmeter.org/")
# driver.get("http://whatismyipaddress.com")
driver.maximize_window()



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

def initialize_driver():
    driver = webdriver.Chrome(service=service)

    driver.get("https://www.dextools.io")


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




def openFilterSection():
    '''Getting the filter sidebar open'''

    # Retry mechanism
    max_attempts = 3
    attempt = 1
    element_clickable = False
    wait = WebDriverWait(driver, 60)

    while attempt <= max_attempts:   
        try:
            element_locator = (By.CLASS_NAME, "custom-filters")
            element = wait.until(EC.element_to_be_clickable(element_locator))
            element.click()
            element_clickable = True
        except Exception as e:
            print(e)
            attempt += 1   


def enterFilterData(minLiquidity, maxMarketCap, poolCreated):
    '''Inputting filter data for the tokens'''

    #radio buttons interactions
    radio_btn1 = elementInteractor(30, (By.ID, "excludeNative"), "click", "none")
    radio_btn2 = elementInteractor(30, (By.ID, "socialInfo"), "click", "none")

    #dropdown interactions
    chain_dropdown = elementInteractor(120, (By.CSS_SELECTOR, ".chain-selector button"), "click", "")
    chains = elementScraper(60, (By.CSS_SELECTOR, ".chain-selector .chain"), "multiple")
    chains[2].click()
    # chain_selection = retryElementInteractor((By.CLASS_NAME, "button-selected"))


    # form inputs
    min_liquidity = elementInteractor(60, (By.CSS_SELECTOR, "[formcontrolname='minLiquidity']"), "send_keys", f"{minLiquidity}")
    max_market_cap = elementInteractor(60,(By.CSS_SELECTOR, "[formcontrolname='maxFdv']"), "send_keys", f"{maxMarketCap}")
    pool_created = elementInteractor(60,(By.CSS_SELECTOR, "[formcontrolname='poolCreatedUnit']"), "send_keys", f"{poolCreated}")

    #pool dropdowns
    wrapper = driver.find_elements(By.CLASS_NAME, "item-select-wrapper")[3]
    wrapper.click()
    d_list = driver.find_element(By.CSS_SELECTOR, ".dropdown-list")
    span_hours = d_list.find_elements(By.CLASS_NAME, "ng-star-inserted")[2]
    span_hours.click()

    #submit
    submit_btn = elementInteractor(30, (By.CSS_SELECTOR, ".panel-footer > .btn"), "click", "none")


def getTelegramFollowers():
    '''Get Telegram Followers'''
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



def tokenPageDataExtraction():
    '''Extracting Token Information from the SINGLE_TOKEN page'''

    try:
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(5)
        
        print("broke here 1")
        token_data_list = elementScraper(60, (By.CSS_SELECTOR, ".pool-info__list > li"), "multiple")
        token_price = elementScraper(60, (By.CLASS_NAME, "big-price"), "single").text
        contract_address_element = elementScraper(60, (By.CSS_SELECTOR, ".pool-info__info .token-pair-info .link"),"single")
        contract_address = contract_address_element.get_attribute('href').split('token/')[1]
        print("Contract Address : ", contract_address)
        print("broke here 1 after, now okay")

        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        holders = token_data_list[3].text#.find_element(By.CSS_SELECTOR, "span")

        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        if "K" in holders or "k" in holders:
            followers = getTelegramFollowers()

            if is_over_1000(followers):
                print("broke here 2")
                token_name = elementScraper(10, (By.CLASS_NAME, "token-name-container"), "single").text
                data = {}
                data['token_name'] = token_name
                data["contract_address"] = contract_address
                data["token_price"] = token_price
                data['market_cap'] = str(token_data_list[0].text)
                data['liquidity'] = str(token_data_list[1].text)
                data['circ_supply'] = str(token_data_list[2].text)
                data['holders'] = holders.split('HOLDERS')[1]
                data['total_market_cap'] = str(token_data_list[4].text)
                data['24h_volume'] = str(token_data_list[5].text)
                data['total_supply'] = str(token_data_list[6].text)
                data["telegram_followers"] =  followers
                return data
            return {}
        else:
            driver.execute_script("window.scrollTo(0, 0);")
            return {}
    except:
        print("an error occured on this token page")
        return {}
    #Market Cap, Liquidity, Circ. Supply, Holders, TOTAL MKTCAP, 24h volume, Total Supply, 


def scrapeTableData():
    '''Scrapes Data from the list of tokens on the Data-Table '''

    token_elements = driver.find_elements(By.CLASS_NAME, "datatable-row-wrapper")
    tokens = token_elements[0:12] if len(token_elements) > 12 else token_elements[0:len(token_elements)]


    token_data = []
    for i in range(len(tokens)):
        try:
            time.sleep(3)
            token_link = tokens[i].find_element(By.CSS_SELECTOR, "a")
            token_link.click()
            time.sleep(3)
            data = tokenPageDataExtraction()

            if data != {}:
                token_data.append(data)
            time.sleep(2)
            driver.execute_script("window.history.back()")
            if "pair-explorer" in driver.current_url: # in the case the first .back() doesn't work
                driver.back()
            
            time.sleep(120)
            token_elements = elementScraper(15,(By.CLASS_NAME, "datatable-row-wrapper"),"multiple")
            print("scrape table error 5")
            tokens = token_elements[0:12] if len(token_elements) > 12 else token_elements[0:len(token_elements)]
            print("scrape table error 6")
        except Exception as e:
            print(e)
    if len(token_data) == 0:
        # token_data.append({"msg":"No Token with over 1k Holders"})
        token_data.append({"msg":"No Tokens"})
    return token_data

def formatData(data_list, filter):
    return_data = ""
    filter = str(filter).upper()
    return_data += f"{filter} \n\n\n"

    if data_list[0] == {"msg":"No Tokens"}:
        return data_list[0]['msg'] + f" from {filter}"

    for data in data_list:
        formatted_data = {
            'TOKEN': data['token_name'].replace('\n/\n', '(').replace('\n', '').capitalize(),
            'Price' : data['token_price'].replace('\n', '').lower(),
            'CA' : data['contract_address'],
            'Market Cap': data['market_cap'].replace('MARKET CAP\n', '').lower(),
            'Liquidity': data['liquidity'].replace('LIQUIDITY\n', '').lower(),
            'Circulating Supply': data['circ_supply'].replace('CIRC. SUPPLY\n', '').lower(),
            'Holders': data['holders'].replace('\n', '').lower(),
            'Total Supply': data['total_supply'].replace('TOTAL SUPPLY\n', '').lower(),
            'Followers' : str(data['telegram_followers']).split(",")[0]
        }
        for key, value in formatted_data.items():
            return_data += f"{key} - {value}\n"
        return_data += "\n\n"
    return return_data


def getTokenData():
    '''Gets the Data-Table returned after the filter'''
    #checking if there are results
    try:
        wait = WebDriverWait(driver, 30)
        data_table_locator = (By.CLASS_NAME, "datatable-scroll")
        data_table = wait.until(EC.presence_of_element_located(data_table_locator))
        time.sleep(3)
        token_data = scrapeTableData()
        # print("token data : ",token_data)
        # cleaned_data = modify_token_data(token_data)
        
        return token_data
    except Exception as e:
        print("datatable exception")
        print(e)
        #checking if there are no results
        try:
            empty_table_locator = (By.CLASS_NAME, "empty-row")
            empty_table = wait.until(EC.element_to_be_clickable(empty_table_locator))
            print("EMpty Table Here")
            return "No Tokens From"
        except Exception as e:
            print("empty table exception")


def closeAds():
    '''close ads that appear on inital site opening'''
    print("closing ads")
    ad1_locator = "card__close"
    ad2_locator = "close"

    ad1 = elementInteractor(10, (By.CLASS_NAME, ad1_locator), "click", "")
    ad2 = elementInteractor(10, (By.CLASS_NAME, ad2_locator), "click", "ad")
    time.sleep(3)
    ad3 = elementInteractor(10, (By.CLASS_NAME, ad2_locator), "click", "ad")


def main():
    # print(len(driver.page_source))
    # closeAds()
    try:
        closeAds()
    except Exception as e:
        print(e)
    while True:
        try:
            #Filter 1
            openFilterSection()
            enterFilterData(10000, 100000, 10)
            time.sleep(120)
            data = getTokenData()
            if data == "No Tokens From":
                sendTelegramMessage(data + " FILTER 1")
            else:
                token_data = formatData(data, "FILTER 1")
                sendTelegramMessage(token_data)
            time.sleep(15)
        except Exception as e:
            print("Network Error In Loading Token Data : ", e)
            sendTelegramMessage("No Tokens Found")
        
        driver.get("https://www.dextools.io")
        try:
            #Filter 2
            openFilterSection()
            enterFilterData(100000, 1000000, 24)
            time.sleep(120)
            data = getTokenData()
            if data == "No Tokens From":
                sendTelegramMessage(data + " FILTER 2")
            else:
                token_data = formatData(data, "FILTER 2")
                sendTelegramMessage(token_data)
        except Exception as e:
            print("No Tokens Found : ", e)
            sendTelegramMessage("No Tokens Found")
        time.sleep(1800)
        driver.get("https://www.dextools.io")

#token data example
[{'token_name': 'APEPE\n/\nSOL', 'market_cap': 'MARKET CAP\n$1.78K', 'liquidity': 'LIQUIDITY\n$7.53', 'circ_supply': 'CIRC. SUPPLY\n100.00B', 'holders': '2.36K', 'total_market_cap': 'TOTAL MKTCAP\n$1.78K', '24h_volume': '24H VOLUME\n$34.50K', 'total_supply': 'TOTAL SUPPLY\n100.00B'}, {'token_name': 'MONKEY\n/\nSOL', 'market_cap': 'MARKET CAP\n$713.06K', 'liquidity': 'LIQUIDITY\n$98.70K', 'circ_supply': 'CIRC. SUPPLY\n420.66T', 'holders': '6.30K', 'total_market_cap': 'TOTAL MKTCAP\n$713.06K', '24h_volume': '24H VOLUME\n$817.14K', 'total_supply': 'TOTAL SUPPLY\n420.66T'}]
main()

