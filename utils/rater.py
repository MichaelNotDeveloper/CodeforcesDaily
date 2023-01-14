from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class Ranker:
    def __init__(self):
        
        options = webdriver.ChromeOptions()
        
        options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.headless = True
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options = options)
        self.driver.get("https://cfviz.netlify.app/virtual-rating-change.html")

        self.contestId = self.driver.find_element('id', 'contestId')
        self.score = self.driver.find_element('id', 'points')
        self.penalty = self.driver.find_element('id', 'penalty')
        self.rating = self.driver.find_element('id', 'rating')
    
    def clear_box(self, id):
        self.driver.find_element('id', id).clear()
    
    def getrank(self, id, score, curr_rating, penalty = 0):
        
        self.clear_box('contestId')
        self.contestId.send_keys(id)
        self.clear_box('points')
        self.score.send_keys(score)
        self.clear_box('penalty')
        self.penalty.send_keys(penalty)
        self.clear_box('rating')
        self.rating.send_keys(curr_rating)
        
        #self.driver.find_element('id', 'submitButton').click()
        
        button = self.driver.find_element(By.CSS_SELECTOR, 'button[id = "submitButton"]')
        self.driver.execute_script("arguments[0].click();", button)
        
        
        while (self.driver.find_element('id', 'rank').get_attribute('innerHTML') == '...'):
            pass
    
        position = self.driver.find_element('id', 'rank').get_attribute('innerHTML')
        expected_rank = self.driver.find_element('id', 'position').get_attribute('innerHTML')
        change = self.driver.find_element('id', 'change').get_attribute('innerHTML')

        self.driver.execute_script (r"document.getElementById('rank').innerHTML = '...'")
        
        return [int(change), int(expected_rank), int(position)]
