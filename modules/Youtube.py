from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
from threading import Thread

class Youtube:
    SKIP_STR = "//div[@class='ytp-ad-text ytp-ad-skip-button-text-centered ytp-ad-skip-button-text']"
    def __init__(self):
        self.browser_type = 'MicrosoftEdge'
        self.video        = None
        self.skipTrigger  = False
    def set_driver(self):
        if self.browser_type == 'MicrosoftEdge':
            from selenium.webdriver.edge.options import Options
            from selenium.webdriver.edge.service import Service
            options = Options()
            options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            service = Service(r".\drivers\msedgedriver.exe")
            self.driver = webdriver.Edge(options=options, service=service) 
    def youtube_skip_adds(self):
        self.set_driver()
        self.driver.maximize_window()
        self.driver.implicitly_wait(20)
        self.driver.get("https://www.youtube.com/")
        while True:
            try:
                skip_ad_button = self.driver.find_element(by=By.XPATH, value=Youtube.SKIP_STR)
                skip_ad_button.click()
            except Exception as e: 
                if 'target window already closed' in repr(e):
                    print("driver.quit()")
                    self.driver.quit()
                    break
                else:
                    time.sleep(1)
                    continue
    def open_link(self,link):
        self.link = link
        t1 = Thread(target=Youtube.playVideo, args=(self,))
        t1.start()
    def sendSpace(self):
        self.send_space = True
        t2 = Thread(target=Youtube.spaceToVideo, args=(self,))
        t2.start()
    def skipAd(self):
        self.skipTrigger = True
        t3 = Thread(target=Youtube.skipAdProcess, args=(self,))
        t3.start()
    def open_youtube(self):
        t4 = Thread(target=Youtube.youtube_skip_adds, args=(self,))
        t4.start()
    def back5s(self):
        self.send_left = True
        t5 = Thread(target=Youtube.LeftToVideo, args=(self,))
        t5.start()
    def spaceToVideo(self):
        if self.video is not None:
            if self.send_space:
                self.video.click()
                self.send_space = False
        else:
            print("self.video is None\n")
            self.video = self.driver.find_element(By.ID, 'movie_player')
    def LeftToVideo(self):
        if self.video is not None:
            if self.send_left:
                actions = ActionChains(self.driver)
                actions.move_to_element(self.video)
                actions.send_keys(Keys.ARROW_LEFT)
                actions.perform()
                self.send_left = False
        else:
            print("self.video is None\n")
            self.video = self.driver.find_element(By.ID, 'movie_player')
    def skipAdProcess(self):
        while True:
            try:
                if self.skipTrigger:
                    skip_ad_button = self.driver.find_element(by=By.XPATH, value=Youtube.SKIP_STR)
                    print()
                    print('Find skip button')
                    print()
                    skip_ad_button.click()
                    self.skipTrigger = False
                else:
                    time.sleep(1)
                    continue
            except NoSuchElementException:
                time.sleep(1)
                continue
            except Exception as e: 
                if 'target window already closed' in repr(e):
                    print("driver.quit()")
                    self.driver.quit()
                    break
    def playVideo(self):
        self.set_driver()
        self.driver.maximize_window()
        self.driver.implicitly_wait(20)
        self.driver.get(self.link)
        while True:
            try:
                self.video = self.driver.find_element(By.ID, 'movie_player')
                break
            except NoSuchElementException:
                continue
            except Exception as e: 
                if 'target window already closed' in repr(e):
                    print("driver.quit()")
                    self.driver.quit()
                    break
    def again(self):
        self.driver.get(self.link)
        try:
            self.video = self.driver.find_element(By.ID, 'movie_player')
        except Exception as e: 
            if 'target window already closed' in repr(e):
                print("driver.quit()")
                self.driver.quit()

def main():
    ytb = Youtube()
    ytb.youtube_skip_adds()
    
if __name__ == '__main__':
    main()
