#!/usr/bin/python

import re
from pathlib import Path
from urllib import request
from collections import Counter

import pandas as pd

from bs4 import BeautifulSoup

from phobia.storage import get


class WikiScraper:
    """Scrapes tables from Wikipedia, for list of terrorist organizations
    between 1999 and 2019. Information scraped from these wiki tables
    includes number of dead people, number of injured people, details of
    perpetrators, region of terror attack, etc.

    Attributes
    ----------
        prefix (str):
            Prefix URL of wikipedia pages containing list of terrorist
            incidents in a particular year.
        data (dict):
            Dictionary of :class: ``pandas.DataFrame`` for years between
            :var: ``start_year`` and :var: ``stop_year``.
        perpetrators (dict):
            Dictionary, containing perpetrators, and number of terror
            attacks undertaken by them.
    """
    def __init__(self, start_year=1999, stop_year=2019,
                 save_csv=True, csv_path='csv_data'):
        """Initializes :class: ``WikiScraper``.

        Arguments
        ---------
            start_year (int):
                Appended to Prefix URL to scrape list of terror incidents
                from the particular year.
            stop_year (int):
                Appended to Prefix URL to scrape list of terror incidents
                till the particular year.
            save_csv (bool):
                If True, saves to path as described by :var: ``csv_path``.
            csv_path (str):
                Saves CSV files for the years in this location.
        """
        self.prefix = 'https://en.wikipedia.org/wiki/List_of_terrorist_incidents_in_'

        data = {}
        for year in range(start_year, stop_year + 1):
            data[str(year)] = self.scrape_tables(year)

        self.data = data

        self.perpetrators = self.get_perpetrators()

        csv_path = get(csv_path)

        if save_csv:
            for year, df in self.data.items():
                Path(csv_path).mkdir(parents=True, exist_ok=True)
                file_path = csv_path / f'{year}.csv' 
                df.to_csv(file_path)

    def scrape_tables(self, year):
        """Scrapes table for a particular year by appending to
        the prefix URL.

        Arguments
        ---------
            year (int):
                Year to append to prefix URL.

        Returns
        -------
            df (pandas.DataFrame):
                DataFrame containing list of terror incidents
                for the given year.
        """
        headings_list, contents_list = [], []
        url = self.prefix + str(year)
        page = request.urlopen(url)
        html_tree = BeautifulSoup(page, "html.parser")
        table_classes = ["wikitable"]
        wikitables = html_tree.findAll("table", table_classes)

        for wikitable in wikitables:
            headings = wikitable.findAll("th")
            contents = wikitable.findAll("td")
            number_of_rows = len(contents) // len(headings)

            for row_number in range(number_of_rows):
                contents_row = []

                for index, heading in enumerate(headings):
                    if len(headings_list) < len(headings):
                        headings_list.append(self.clean_tags(heading))
                    content_index = row_number * len(headings) + index
                    contents_row.append(self.clean_tags(
                                            contents[content_index]))
                contents_list.append(contents_row)

        df = pd.DataFrame(contents_list, columns=headings_list)
        return df

    def clean_tags(self, item):
        """Cleans HTM tags from the given items.

        Arguments
        ---------
            item (bs4.Tag):
                Items containing HTML tags.

        Returns
        -------
            clean_item (str):
                Cleaned item by removing HTML tags.
        """
        tag = re.compile('<.*?>')
        newline = re.compile('\n')
        clean_item = re.sub(tag, '', str(item))
        clean_item = re.sub(newline, '', clean_item)        
        return clean_item

    def get_perpetrators(self):
        """Gets list of perpetrators from the pandas DataFrames.

        Returns
        -------
            (dict):
                List of perpetrators and the number of terror incidents
                undertaken by them.
        """
        perpetrators = []
        for df in self.data.values():
            if 'Perpetrator' in df.columns:
                perpetrators.extend(df['Perpetrator'].values.tolist())
            elif 'Perpetrators' in df.columns:
                perpetrators.extend(df['Perpetrators'].values.tolist())

        return dict(Counter(perpetrators))
