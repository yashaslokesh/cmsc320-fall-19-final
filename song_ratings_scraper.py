"""
To run this script, make sure you have a browser driver in your directory.

The build I used, I found on 
https://chromedriver.storage.googleapis.com/index.html?path=78.0.3904.70/
I am using the macOS version.

This module, when run, generates a SQLite database with artist, song name, album name,
and rating, scraped from allmusic.com
"""
import atexit

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select

START_YEAR = 1963
END_YEAR = 2019

class Scraper(object):
    """ Automatically tears down the WebDriver object """

    def __init__(self):
        base_url = 'https://www.allmusic.com/advanced-search'
        self.driver = webdriver.Chrome('./chromedriver')
        self.driver.get(base_url)

    def get_html(self, filename='page'):
        """ Gets the page source as the driver currently sees it.
        This method can be run after everytime that the driver executes
        some action/script
        """
        html = self.driver.page_source
        soup = BeautifulSoup(html, features='html.parser')

        with open('html/' + filename + '.html', 'w') as f:
            f.write(soup.prettify())
    
    def get_select_options(self):
        start_select = Select(self.driver.find_element_by_name('start-year'))
        end_select = Select(self.driver.find_element_by_name('end-year'))

        for option in end_select.options:
            if option.get_attribute('value') == END_YEAR:
                option.click()


        for option in start_select.options:
            print(option.get_attribute('value'))
    # @atexit.register
    # def tear_down(self):
    #     self.driver.quit()

    def option_clicker(self):
        start_select = Select(self.driver.find_element_by_name('start-year'))
        end_select = Select(self.driver.find_element_by_name('end-year'))

        for start, end in zip(start_select.options, end_select.options):
            print(start.get_attribute('value'))
            print(end.get_attribute('value'))
            start.click()
            end.click()
            break

def main():
    scraper = Scraper()
    # scraper.get_select_options()
    

    scraper.get_html('option-tested')

    # scraper.tear_down()

if __name__ == '__main__':
    main()