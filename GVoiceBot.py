#!/usr/bin/env python3
"""
    *******************************************************************************************
    FbGroupBot.
    Author: Ali Toori, Python Developer [Bot Builder]\n'
    LinkedIn: https://www.linkedin.com/in/alitoori/
    *******************************************************************************************
"""
import os
import re
import time
import random
import pickle
import ntplib
import datetime
import pyfiglet
import pyautogui
import logging.config
from time import sleep
from pathlib import Path
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    'formatters': {
        'colored': {
            '()': 'colorlog.ColoredFormatter',  # colored output
            # --> %(log_color)s is very important, that's what colors the line
            'format': '[%(asctime)s] %(log_color)s%(message)s'
        },
    },
    "handlers": {
        "console": {
            "class": "colorlog.StreamHandler",
            "level": "INFO",
            "formatter": "colored",
            "stream": "ext://sys.stdout"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": [
            "console"
        ]
    }
})

LOGGER = logging.getLogger()
GVOICE_URL = "https://voice.google.com/signup"


class GVoiceBot:

    def __init__(self):
        self.first_time = True
        self.PROJECT_FOLDER = os.path.abspath(os.path.dirname(__file__))
        self.PROJECT_ROOT = Path(self.PROJECT_FOLDER)
        self.file_timer_sec = self.PROJECT_ROOT / 'GVoiceRes/TimerSec.txt'

    # Get random user-agent
    def get_random_user_agent(self):
        file_path = self.PROJECT_ROOT / 'GVoiceRes/user_agents.txt'
        user_agents_list = []
        with open(file_path) as f:
            content = f.readlines()
        user_agents_list = [x.strip() for x in content]
        return random.choice(user_agents_list)

    # Login to the website for smooth processing
    def get_driver(self):
        # For absolute chromedriver path
        DRIVER_BIN = str(self.PROJECT_ROOT / "GVoiceRes/bin/chromedriver_win32.exe")
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-notifications")
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument(F'--user-agent={self.get_random_user_agent()}')
        # options.add_argument('--headless')
        driver = webdriver.Chrome(executable_path=DRIVER_BIN, options=options)
        return driver

    def close_popup(self, driver, email):
        try:
            LOGGER.info(f"[Waiting for pop-up to become visible][Account: {str(email)}]")
            wait_until_visible(driver=driver, xpath='//*[@id="u_0_k"]', duration=5)
            driver.find_element_by_xpath('//*[@id="u_0_k"]').click()
            LOGGER.info(f"[Cookies Accepted][Account: {str(email)}]")
        except:
            pass

    # Google login
    def google_login(self, driver):
        LOGGER.info(f"[Signing-in to the Google]")
        file_path_account = self.PROJECT_ROOT / 'GVoiceRes/Account.txt'
        # Get account from input file
        with open(file_path_account) as f:
            content = f.readlines()
        account = [x.strip() for x in content[0].split(':')]
        email = account[0]
        password = account[1]
        cookies = 'Cookies' + str(email) + '.pkl'
        file_cookies = self.PROJECT_ROOT / 'GVoiceRes' / cookies
        if os.path.isfile(file_cookies):
            LOGGER.info(f"[Requesting: {str(GVOICE_URL)}][Account: {str(email)}]")
            driver.get(GVOICE_URL)
            # try:
            LOGGER.info(f"[Loading cookies][Account: {str(email)}]")
            with open(file_cookies, 'rb') as cookies_file:
                cookies = pickle.load(cookies_file)
            for cookie in cookies:
                driver.add_cookie(cookie)
            driver.get(GVOICE_URL)
            try:
                LOGGER.info(f"[Waiting for GVoice to become visible][Account: {str(email)}]")
                wait_until_visible(driver=driver, xpath='//*[@id="input_0"]')
                LOGGER.info(f"[Cookies login successful][Account: {str(email)}]")
                return
            except WebDriverException as ec:
                LOGGER.info(f"[Cookies login failed][Account: {str(email)}]")
                os.remove(file_cookies)
                pass
        # Try Signing-in normally
        driver.get(GVOICE_URL)
        LOGGER.info(f"[Waiting for email field to become visible]")
        wait_until_visible(driver=driver, xpath='//*[@id="identifierId"]')
        LOGGER.info(f"[Filling email]")
        driver.find_element_by_xpath('//*[@id="identifierId"]').send_keys(email)
        sleep(1)
        driver.find_element_by_xpath('//*[@id="identifierNext"]/div/button').click()
        sleep(1)
        LOGGER.info(f"[Filling password]")
        driver.find_element_by_xpath('//*[@id="password"]/div[1]/div/div[1]/input').send_keys(password)
        sleep(1)
        driver.find_element_by_xpath('//*[@id="passwordNext"]/div/button').click()
        LOGGER.info(f"[Login button clicked]")
        LOGGER.info(f"[Waiting for GVoice to become visible][Account: {str(email)}]")
        wait_until_visible(driver=driver, xpath='//*[@id="input_0"]')
        LOGGER.info(f"[Successfully logged-in][Account: {str(email)}]")
        # Store user cookies for later use
        LOGGER.info(f"[Saving cookies for][Account: {str(email)}]")
        with open(file_cookies, 'wb') as cookies_file:
            pickle.dump(driver.get_cookies(), cookies_file)
        LOGGER.info(f"Cookies have been saved][Account: {str(email)}]")

    def make_call(self, number):
        driver = self.get_driver()
        LOGGER.info('[GVoiceBot Launched]')
        self.google_login(driver)
        # Get timer sec from input file
        with open(self.file_timer_sec) as f:
            content = f.readlines()
        timer_sec = [x.strip() for x in content[0].split(':')]
        delay_sec_min = int(timer_sec[0])
        delay_sec_max = int(timer_sec[1])
        delays_sec = [t for t in range(delay_sec_min, delay_sec_max + 1)]
        LOGGER.info(f"[Delays Sec: {str(delays_sec)}]")

        LOGGER.info(f"[Waiting for GVoice to become visible]")
        wait_until_visible(driver=driver, xpath='//*[@id="input_0"]')
        driver.find_element_by_xpath('//*[@id="input_0"]').send_keys(number)
        LOGGER.info("[Page has been visible]")
        # LOGGER.info("[Scrolling down the posts]")
        scrolls = 0
        while True:
            driver.find_element_by_tag_name('html').send_keys(Keys.END)
            driver.find_element_by_tag_name('html').send_keys(Keys.END)
            scrolls += 1
            sleep(3)
            if scrolls >= 1:
                break
        LOGGER.info("[Looking for the post with highest number of likes]")
        like_list = []
        for post in driver.find_elements_by_class_name('kfpcsd3p'):
            try:
                like_text = str(post.find_element_by_css_selector('.gpro0wi8.cwj9ozl2.bzsjyuwj.ja2t1vim').text).strip().replace('\n', '')
            except:
                continue
            LOGGER.info(f"Video Likes: {like_text}")
            number = re.findall(r"(\d\.\d|\d+)", like_text)
            try:
                number = round(float(number[0]))
            except:
                continue
            letter = None
            try:
                letter = re.findall(r"([a-zA-Z])", like_text)
                letter = str(letter[0])
            except:
                pass
            if str(letter).lower() == 'k' or str(letter).lower() == 'm':
                num = self.switch(letter)
                like_counter = round(int(num) * number)
                LOGGER.info("Likes in digits: " + str(like_counter))
            else:
                like_counter = number
            like_list.append(like_counter)
        LOGGER.info(f"[Likes List: {str(like_list)}")
        max_likes = max(like_list)
        LOGGER.info(f"[Max Likes: {str(max_likes)}")
        LOGGER.info(f"[Selecting the post with highest number of likes: {max_likes}]")
        for post in driver.find_elements_by_class_name('kfpcsd3p'):
            # Scroll the item into view
            driver.execute_script("return arguments[0].scrollIntoView(true);", post)
            sleep(1)
            try:
                like_text = str(post.find_element_by_css_selector('.gpro0wi8.cwj9ozl2.bzsjyuwj.ja2t1vim').text).strip().replace('\n', '')
            except:
                continue
            number = re.findall(r"(\d\.\d|\d+)", like_text)
            number = round(float(number[0]))
            letter = None
            try:
                letter = re.findall(r"([a-zA-Z])", like_text)
                letter = str(letter[0])
            except:
                pass
            if str(letter).lower() == 'k' or str(letter).lower() == 'm':
                num = self.switch(letter)
                like_counter = round(int(num) * number)
                # LOGGER.info("Likes: " + str(like_counter))
            else:
                like_counter = number
            if max_likes == like_counter:
                LOGGER.info(f"[Post found with likes: {max_likes}]")
                # Scroll the item into view
                driver.execute_script("return arguments[0].scrollIntoView(true);", post)
                sleep(5)
                try:
                    post.find_element_by_css_selector('.gpro0wi8.cwj9ozl2.bzsjyuwj.ja2t1vim').click()
                    LOGGER.info(f"[The post with highest number of likes has been selected: {max_likes}]")
                except:
                    try:
                        post.find_element_by_css_selector('.gpro0wi8.cwj9ozl2.bzsjyuwj.ja2t1vim').find_element_by_tag_name('span').click()
                        LOGGER.info(f"[Div 0 Clicked]")
                    except:
                        try:
                            post.find_element_by_css_selector('.gpro0wi8.cwj9ozl2.bzsjyuwj.ja2t1vim').find_elements_by_tag_name('span')[1].click()
                            LOGGER.info(f"[Div 1 Clicked]")
                        except:
                            pass
                break
        LOGGER.info("[Scrolling down the followers/likes]")
        while True:
            LOGGER.info("[Getting followers]")
            pyautogui.press('space')
            sleep(1)
            followers = [follower.find_element_by_tag_name('a').get_attribute('href') for follower in driver.find_elements_by_css_selector('.nqmvxvec.j83agx80.cbu4d94t.tvfksri0.aov4n071.bi6gxh9e.l9j0dhe7')]
            LOGGER.info(f"[Followers found: {str(len(followers))}]")
            # if len(followers) >= max_likes - 80:
            if len(followers) >= max_likes - 40:
                break
        LOGGER.info(f"[Followers found: {str(len(followers))}]")
        for follower in followers:
            message = random.choice(numbers)
            LOGGER.info(f"[Requesting follower profile: {str(follower)}]")
            driver.get(follower)
            LOGGER.info("[Waiting for follower profile to become visible]")
            wait_until_visible(driver, xpath='//*[@id="fb-timeline-cover-name"]')
            LOGGER.info("[Member profile has been visible]")
            LOGGER.info("[Waiting for message button to become visible]")
            wait_until_visible(driver, xpath='//*[@id="u_0_19"]')
            LOGGER.info("[Message button has been visible]")
            LOGGER.info("[Clicking Message button]")
            driver.find_element_by_xpath('//*[@id="u_0_19"]').click()
            LOGGER.info("[Message button has been clicked]")
            LOGGER.info("[Sending message]")
            LOGGER.info(f"[Message to be sent: {message}]")
            sleep(1)
            pyautogui.typewrite(message)
            pyautogui.press('enter')
            LOGGER.info(f"[Message has been sent]")
            delay_sec = random.choice(delays_sec)
            LOGGER.info(f"[Waiting for {str(delay_sec)} seconds]")
            sleep(delay_sec)

        self.finish(driver)

    def switch(self, x):
        return {
            'K': 1000,
            'M': 1000000,
        }.get(x, 1)

    def finish(self, driver):
        try:
            driver.close()
            driver.quit()
        except WebDriverException as exc:
            LOGGER.info('Problem occurred while closing the WebDriver instance ...', exc.args)


def wait_until_clickable(driver, xpath=None, element_id=None, name=None, class_name=None, tag_name=None, css_selector=None, duration=10000, frequency=0.01):
    if xpath:
        WebDriverWait(driver, duration, frequency).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    elif element_id:
        WebDriverWait(driver, duration, frequency).until(EC.element_to_be_clickable((By.ID, element_id)))
    elif name:
        WebDriverWait(driver, duration, frequency).until(EC.element_to_be_clickable((By.NAME, name)))
    elif class_name:
        WebDriverWait(driver, duration, frequency).until(EC.element_to_be_clickable((By.CLASS_NAME, class_name)))
    elif tag_name:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.TAG_NAME, tag_name)))
    elif css_selector:
        WebDriverWait(driver, duration, frequency).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))


def wait_until_visible(driver, xpath=None, element_id=None, name=None, class_name=None, tag_name=None, css_selector=None, duration=10000, frequency=0.01):
    if xpath:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    elif element_id:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.ID, element_id)))
    elif name:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.NAME, name)))
    elif class_name:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.CLASS_NAME, class_name)))
    elif tag_name:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.TAG_NAME, tag_name)))
    elif css_selector:
        WebDriverWait(driver, duration, frequency).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))


# Trial version logic
def trial(trial_date):
    ntp_client = ntplib.NTPClient()
    response = ntp_client.request('pool.ntp.org')
    local_time = time.localtime(response.ref_time)
    current_date = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
    current_date = datetime.datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')
    return trial_date > current_date


gvoice_bot = GVoiceBot()


def main(number):
    # Getting Day before Yesterday
    # day_before_yesterday = (datetime.datetime.now() - datetime.timedelta(2)).strftime('%m/%d/%Y')
    # while True:
    driver = gvoice_bot.get_driver()
    gvoice_bot.google_login(driver=driver)
    gvoice_bot.make_call(number=number)


if __name__ == '__main__':
    PROJECT_FOLDER = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = Path(PROJECT_FOLDER)
    file_path_numbers = PROJECT_ROOT / 'GVoiceRes/Numbers.txt'
    trial_date = datetime.datetime.strptime('2020-11-10 23:59:59', '%Y-%m-%d %H:%M:%S')
    # Print ASCII Art
    print('************************************************************************')
    pyfiglet.print_figlet('____________               FbPageBot ____________\n', colors='RED')
    print('Author: Ali Toori, Python Developer [Web-Automation Bot Developer]\n'
          'Profiles:\n\tUpwork: https://www.upwork.com/freelancers/~011f08f1c849755c46\n\t'
          'Fiver: https://www.fiverr.com/alitoori\n************************************************************************')
    # Trial version logic
    if trial(trial_date):
        with open(file_path_numbers) as f:
            content = f.readlines()
        numbers = [x.strip() for x in content]
        LOGGER.info(f"[Numbers: {str(numbers)}")
        # LOGGER.warning("Your trial will end on: " + str(trial_date))
        # LOGGER.warning("Please contact fiverr.com/AliToori !")
        # We can use a with statement to ensure threads are cleaned up promptly
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(numbers)) as executor:
            executor.map(main, numbers)
    else:
        pass
        # print("Your trial has been expired, To get full version, please contact fiverr.com/AliToori !")
