from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
from threading import Thread

class Youtube:
    def __init__(self):
        self.browser_type = 'MicrosoftEdge'
        self.video        = None
        self.skipTrigger  = False
    def set_driver(self):
        if self.browser_type == 'MicrosoftEdge':
            from msedge.selenium_tools import Edge, EdgeOptions
            options = EdgeOptions()
            options.use_chromium = True
            options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            self.driver = Edge(options=options, executable_path=r".\drivers\msedgedriver.exe") 
    def youtube_skip_adds(self):
        self.set_driver()
        self.driver.maximize_window()
        self.driver.implicitly_wait(20)
        self.driver.get("https://www.youtube.com/")
        while True:
            try:
                skip_ad_button = self.driver.find_element(by=By.XPATH, value="//div[@class='ytp-ad-text ytp-ad-skip-button-text']")
                skip_ad_button.click()
            except NoSuchElementException:
                time.sleep(1)
                continue
            except Exception as e: 
                if 'target window already closed' in repr(e):
                    break
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
    def spaceToVideo(self):
        if self.video is not None:
            if self.send_space:
                self.video.click()
                self.send_space = False
    def skipAdProcess(self):
        while True:
            try:
                if self.skipTrigger:
                    skip_ad_button = self.driver.find_element(by=By.XPATH, value="//div[@class='ytp-ad-text ytp-ad-skip-button-text']")
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
                    break
    def playVideo(self):
        self.set_driver()
        self.driver.maximize_window()
        self.driver.implicitly_wait(20)
        self.driver.get(self.link)
        while True:
            try:
                self.video = self.driver.find_element_by_id('movie_player')
                break
            except NoSuchElementException:
                continue
            except Exception as e: 
                if 'target window already closed' in repr(e):
                    break
def main():
    ytb = Youtube()
    ytb.youtube_skip_adds()
    
if __name__ == '__main__':
    main()
