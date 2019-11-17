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
import re
import sqlite3

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException,
    JavascriptException,
)
import pandas as pd

START_YEAR = 2012
END_YEAR = 2019

# CSS Classes corresponding to each rating
ALLMUSIC_RATINGS = {"rating-allmusic-7": 4.0, "rating-allmusic-8": 4.5}


class Scraper(object):
    """ Automatically tears down the WebDriver object """

    def __init__(self):
        base_url = "https://www.allmusic.com/advanced-search"
        self.driver = webdriver.Chrome("./chromedriver")
        self.driver.get(base_url)

    def log_current_page(self, filename="page"):
        """ Gets the page source as the driver currently sees it.
        This method can be run after everytime that the driver executes
        some action/script
        """
        html = self.driver.page_source
        soup = BeautifulSoup(html, features="html.parser")

        with open("html/" + filename + ".html", "w") as f:
            f.write(soup.prettify())

    def get_select_options(self):
        start_select = Select(self.driver.find_element_by_name("start-year"))
        end_select = Select(self.driver.find_element_by_name("end-year"))

        for option in end_select.options:
            if option.get_attribute("value") == END_YEAR:
                option.click()

        for option in start_select.options:
            print(option.get_attribute("value"))

    def option_clicker(self, conn: sqlite3.Connection):
        scroll_script = """
        var e = document.getElementById("recordingtype:mainalbum");
        e.scrollIntoView({block: "center"});
        """

        self.driver.execute_script(scroll_script)
        by_album_option = self.driver.find_element_by_id("recordingtype:mainalbum")
        by_album_option.click()

        start_select = Select(self.driver.find_element_by_name("start-year"))
        end_select = Select(self.driver.find_element_by_name("end-year"))

        # Execute only twice (for testing purposes)
        i = 0

        table_df = pd.DataFrame(columns=["Year", "Artist", "Album", "AllMusic Rating"])

        # for start in reversed(start_select.options[:59]):
        for i in range(START_YEAR, END_YEAR + 1):
            end_select.select_by_value((i,))

            curr_year = i
            time.sleep(2)

            year_df = pd.DataFrame(
                columns=["Year", "Artist", "Album", "AllMusic Rating"]
            )

            start_select.select_by_value((i,))

            # Waits until a `artist` table element shows up, indicating
            # that all of the values have actually been loaded,
            # because they are dynamically loaded after we click the year
            element = WebDriverWait(self.driver, 5).until(
                ec.presence_of_element_located((By.XPATH, "//td[@class='artist']"))
            )

            html = self.driver.page_source
            soup = BeautifulSoup(html, features="html.parser")

            self.next_link_exists = True
            new_data = []

            def wait_for_table_or_fail():
                try:
                    element = WebDriverWait(self.driver, 20).until(
                        ec.presence_of_element_located((By.XPATH, "//table"))
                    )
                except TimeoutException:
                    element = self.driver.find_element_by_xpath(
                        "//h2[@class='no-results']"
                    )
                    return False

                # Update the soup for the newly rendered page
                html = self.driver.page_source
                soup = BeautifulSoup(html, features="html.parser")

                new_data.extend(self.table_processor(soup))

            while self.next_link_exists:
                res = wait_for_table_or_fail()
                if res == False:
                    break
                self.next_page_clicker(soup)

            # Executed one last time for the last page.
            wait_for_table_or_fail()

            table_df = table_df.append(new_data, ignore_index=True)
            year_df = year_df.append(new_data, ignore_index=True)

            # print(table_df.describe())
            # print(table_df.head())
            print(year_df.describe())
            print(year_df.head())

            # table_df.to_sql(f'{curr_year}_ratings', conn, if_exists='replace')

            year_df.to_sql(f"{curr_year}_ratings", conn, if_exists="replace")

            self.log_current_page(f"{curr_year}_ratings_page")

            i += 1
        return table_df

    def table_finder(self, soup: BeautifulSoup):
        tables = soup.find("table")
        i = 0

        with open("html/2019_tables.html", "w") as f:
            f.write(tables.prettify())

    def next_page_clicker(self, soup: BeautifulSoup):
        try:

            time.sleep(1)

            scroll_script = """
            var e = document.getElementsByClassName("next");
            e[0].scrollIntoView({block: "center"});
            """

            self.driver.execute_script(scroll_script)
            next_button = self.driver.find_element_by_xpath("//span[@class='next']")

            # link = next_button.find_element_by_tag_name("a")
            link = next_button.find_element_by_tag_name("a")
            print(link.get_attribute("href"))
            try:
                next_button.click()
            except ElementClickInterceptedException as e:
                self.driver.find_element_by_tag_name("body").send_keys(Keys.PAGE_UP)
                next_button.click()
            # print(link.get_attribute('href'))

            # link.click()
        except NoSuchElementException as e:
            self.next_link_exists = False
        except JavascriptException as j:
            self.next_link_exists = False

    def table_processor(self, soup: BeautifulSoup):
        element = WebDriverWait(self.driver, 5).until(
            # ec.presence_of_element_located((By.XPATH, "//td[@class='artist']"))
            ec.presence_of_element_located((By.XPATH, "//table"))
        )

        table = soup.find("table")

        # print(table)

        all_data = []

        i = 0

        body = table.find("tbody")
        for row in body.find_all("tr"):
            data = {}

            # Get rid of the cover column
            columns = row.find_all("td")[1:]

            # Sanity checks
            try:
                ratings_col = columns[3]
            except IndexError as e:
                print(row)
                continue
            assert ratings_col["class"][0] == "rating"

            match = re.match(r"rating-allmusic-(\d)", ratings_col.div["class"][1])

            if match:

                # Sanity checks
                year_col = columns[0]
                assert year_col["class"][0] == "year"

                try:
                    year = int(year_col.string)
                except ValueError:
                    continue

                # print(year)
                data["Year"] = year

                # Sanity checks
                artist_col = columns[1]
                assert artist_col["class"][0] == "artist"

                try:
                    artist = artist_col.a.string
                except AttributeError:
                    artist = artist_col.string

                # print(artist)

                data["Artist"] = artist

                # Sanity checks
                title_col = columns[2]
                assert title_col["class"][0] == "title"

                try:
                    title = title_col.a.string
                except AttributeError:
                    title = title_col.string
                # print(title)
                data["Album"] = title

                """ The '\d' captured from the class of our div, corresponds to some rating

                The lowest rating is 1 star, that corresponds to the class of 1. Each subsequent
                increment in class number increases the rating by 0.5 of a star
                """
                rating = (int(match.group(1)) + 1) * 0.5

                # print(rating)
                data["AllMusic Rating"] = rating

                # print(row.prettify())

                # table_df = table_df.append(data, ignore_index=True)
                all_data.append(data)

        return all_data


def main():
    scraper = Scraper()
    conn = sqlite3.connect("year_by_year_ratings.db")
    df = scraper.option_clicker(conn)


if __name__ == "__main__":
    main()
