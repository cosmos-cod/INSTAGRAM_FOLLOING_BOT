import os
import time
import random

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASS = os.getenv("PASS")
SIMILAR_ACCOUNT = "cristiano"
MAX_FOLLOWS = 20  # keep this low, see the note below


class InstaFollower:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def login(self):
        self.driver.get("https://www.instagram.com/accounts/login/")
        email_entry = self.wait.until(ec.presence_of_element_located((By.NAME, "email")))
        email_entry.send_keys(EMAIL)
        password_entry = self.wait.until(ec.presence_of_element_located((By.NAME, "pass")))
        password_entry.send_keys(PASS)
        password_entry.send_keys(Keys.ENTER)
        input("Complete the CAPTCHA/login steps, then press ENTER here...")


        for xpath in ("//div[contains(text(), 'Not now')]",
                      "//button[contains(text(), 'Not Now')]"):
            try:
                WebDriverWait(self.driver, 5).until(
                    ec.element_to_be_clickable((By.XPATH, xpath))
                ).click()
            except Exception:
                pass

    def find_followers(self):
        time.sleep(3)
        self.driver.get(f"https://www.instagram.com/{SIMILAR_ACCOUNT}/followers/")

        try:

            self.wait.until(ec.presence_of_element_located(
                (By.XPATH, "//div[@role='dialog']")
            ))
        except Exception:
            # Fallback: open the profile and click the "followers" link by its text
            self.driver.get(f"https://www.instagram.com/{SIMILAR_ACCOUNT}/")
            link = WebDriverWait(self.driver, 15).until(ec.element_to_be_clickable(
                (By.XPATH, "//a[contains(@href, 'followers')] | //*[contains(text(), 'followers')]")
            ))
            link.click()
            self.wait.until(ec.presence_of_element_located(
                (By.XPATH, "//div[@role='dialog']")
            ))

        time.sleep(3)

    def _get_scrollable(self):
        """Find the scrollable container inside the followers dialog."""
        dialog = self.driver.find_element(By.XPATH, "//div[@role='dialog']")
        return self.driver.execute_script(
            """
            const divs = arguments[0].querySelectorAll('div');
            for (const el of divs) {
                const oy = getComputedStyle(el).overflowY;
                if ((oy === 'auto' || oy === 'scroll') && el.scrollHeight > el.clientHeight) {
                    return el;
                }
            }
            return null;
            """,
            dialog,
        )

    def follow(self, max_follows=MAX_FOLLOWS):
        followed = 0
        empty_rounds = 0
        scrollable = self._get_scrollable()
        if scrollable is None:
            print("Could not find the scrollable followers list.")
            return

        while followed < max_follows and empty_rounds < 3:
            dialog = self.driver.find_element(By.XPATH, "//div[@role='dialog']")

            buttons = dialog.find_elements(By.XPATH, ".//button[normalize-space(.)='Follow']")

            clicked_this_round = 0
            for button in buttons:
                if followed >= max_follows:
                    break
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", button
                    )
                    time.sleep(random.uniform(0.5, 1.2))
                    try:
                        button.click()
                    except ElementClickInterceptedException:
                        self.driver.execute_script("arguments[0].click();", button)
                    followed += 1
                    clicked_this_round += 1
                    print(f"Followed {followed}/{max_follows}")
                    time.sleep(random.uniform(3, 7))  # human-like pause
                except StaleElementReferenceException:
                    continue

            # Scroll the list down to load the next set of people
            before = self.driver.execute_script("return arguments[0].scrollTop;", scrollable)
            self.driver.execute_script(
                "arguments[0].scrollTop += arguments[0].clientHeight;", scrollable
            )
            time.sleep(random.uniform(2, 4))
            after = self.driver.execute_script("return arguments[0].scrollTop;", scrollable)

            if clicked_this_round == 0 and after == before:
                empty_rounds += 1
            else:
                empty_rounds = 0

        print(f"Done. Followed {followed} accounts.")


bot = InstaFollower()
bot.login()
bot.find_followers()
bot.follow()
