"""
To run this script, make sure you have a browser driver in your directory.

The build I used, I found on 
https://chromedriver.storage.googleapis.com/index.html?path=78.0.3904.70/
I am using the macOS version.

This module, when run, generates a SQLite database with artist, song name, album name,
and rating, scraped from allmusic.com
"""
import atexit
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

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
        # Built-in timer to account for delay in loading pages
        # time.sleep(5)
        html = self.driver.page_source
        soup = BeautifulSoup(html, features='html.parser')

        self.table_finder(soup)

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

        # Execute only twice (for testing purposes)
        i = 0

        # Starting from index 1 skips over the empty options, going straight into the years
        # for start, end in zip(start_select.options[1:], end_select.options[1:]):
        for start in start_select.options[1:]:
            print(start.get_attribute('value'))

            # end = end_select.options[-1]
            # print(end.get_attribute('value'))
            # try:
            # print(end.get_attribute('value'))
            # except:
            #     print('error')
            #     self.get_html(f'click_error') 

            # Break the clicking loop once we have gone out of scope for our dataset.
            # Won't be used until the bottom `i` limiter is removed.
            curr_year = start.get_attribute('value') 

            if int(curr_year) == START_YEAR - 1:
                break
            
            # Values start with 2019... goes to 1920. We stop at 1963
            start.click()
            time.sleep(2)

            end = end_select.options[-1]
            print(end.get_attribute('value'))

            end.click()

            # Waits until a `artist` table element shows up, indicating
            # that all of the values have actually been loaded, 
            # because they are dynamically loaded after we click the year
            element = WebDriverWait(self.driver, 5).until(
                ec.presence_of_element_located((By.XPATH, "//td[@class='artist']"))
            )

            self.get_html(f'{curr_year}_ratings_page')

            # HTML page ready for processing here.
            # TODO: Remove once not needed anymore for testing....
            i += 1
            if i == 1:
                break
    

    def table_finder(self, soup: BeautifulSoup):
        tables = soup.find_all('table')
        print(len(tables))
        with open('html/2019_tables.html', 'w') as f:
            f.write(tables.__str__())


def main():
    scraper = Scraper()
    # scraper.get_select_options()
    scraper.option_clicker()

    scraper.get_html('option-tested')

    # scraper.tear_down()

if __name__ == '__main__':
    main()