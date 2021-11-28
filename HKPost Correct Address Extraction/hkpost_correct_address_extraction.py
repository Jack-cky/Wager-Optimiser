"""
HKPOST CORRECT ADDRESS EXTRACTION
Version 02
    This programme scraps data from HKPost to find correct address of estate/building.
        1.  Input a LIST of estate/building/street names.
        2.  Output 'district', 'street' and 'building' shown in website as a data frame.
    Purpose: automate searching huge amount of addresses from the web
Contribution: Jack Chan
"""

import pandas as pd
from selenium import webdriver
import time
import re

class HongKongPostCorrectAddress():
    def __init__(self):
        self.url = 'https://www.hongkongpost.hk/correct_addressing/index.jsp?lang=en_US'

    def initialise_botton(self):
        self.search_input = self.web.find_element_by_name('buildinginput')
        self.search_button = self.web.find_element_by_css_selector(".newButtonStyle[id = 'rdsearch3']")
        self.reset_button = self.web.find_element_by_css_selector(".newButtonStyle[id = 'rdreset3']")

    def initialise_config(self):
        self.result = pd.DataFrame(columns = ['district', 'street', 'building'])
        self.first_n_result = -1 # default get all results

    def open_web(self):
        self.web = webdriver.Chrome('./chromedriver')
        self.web.get(self.url)
        self.initialise_botton()
        self.initialise_config()

    def click_search(self, estate_building_name):
        self.search_input.send_keys(estate_building_name)
        self.search_button.click()
        self.search_button.click() # (optional: tackle pop-up message from the web)
        time.sleep(5)

    def clean_result(self, data):
        data['street'] = data['street'].replace('&nbsp;&nbsp;', 'N/A')
        return data

    def get_result(self):
        self.html_content = self.web.page_source
        self.district = re.findall(r'<td width="220pt" valign="top" class="tdstyle">(.*)</td>', self.html_content)
        self.street = re.findall(r'<td width="250pt" valign="top" class="tdstyle">(.*)</td>', self.html_content)
        self.building = re.findall(r'<td width="280pt" valign="top" class="tdstyle">(.*)</td>', self.html_content)
        self.df_result = pd.DataFrame({'district': self.district, 'street': self.street, 'building': self.building})
        self.df_result = self.clean_result(self.df_result)
        return self.df_result if self.first_n_result == -1 else self.df_result[:self.first_n_result]

    def click_reset(self):
        self.reset_button.click()

    def close_web(self):
        self.web.close()

    def search_estate_building_name(self, estate_building_name):
        # check input
        if type(estate_building_name) != list or len(estate_building_name) < 1:
            return print('[ERROR] Input does not match data type or is empty list object.')
        
        # remove duplicate element to reduce query time
        estate_building_name = list(set(estate_building_name))
        
        # main operation
        self.open_web()
        for name in estate_building_name:
            try:
                self.click_search(name)
                self.df_result = self.get_result()
            except:
                self.df_result = pd.DataFrame({'district': ['NOT FOUND'], 'street': ['NOT FOUND'], 'building': ['NOT FOUND']})
            self.df_result['input_estate_building_name'] = name
            self.result = pd.concat([self.result, self.df_result])
            del self.df_result
            self.click_reset()
        self.close_web()
        
        self.result.reset_index(drop = True, inplace = True)

        return self.result

if __name__ == '__main__':
    demo = HongKongPostCorrectAddress()
    ## case 1: valid input and return correct address
    #      | district       | street                             | building                                           | input_estate_building_name       |
    # |---:|:---------------|:-----------------------------------|:---------------------------------------------------|:---------------------------------|
    # |  0 | CENTRAL (中環)  | N/A                                | TWO INTERNATIONAL FINANCE CENTRE (國際金融中心二期 ) | TWO INTERNATIONAL FINANCE CENTRE |
    # |  1 | WAN CHAI (灣仔) | 7 GLOUCESTER ROAD  (告士打道 7號 ) | IMMIGRATION TOWER (入境事務大樓 )                     | IMMIGRATION TOWER                |
    demo.search_estate_building_name(['TWO INTERNATIONAL FINANCE CENTRE', 'IMMIGRATION TOWER'])
    # control number of address return if there are more than one address shown
    # demo.first_n_result = 1
    
    ## case 2: valid input but no address return from HKPost
    #      | district       | street                             | building                                           | input_estate_building_name         |
    # |---:|:---------------|:-----------------------------------|:---------------------------------------------------|:-----------------------------------|
    # |  0 | NOT FOUND      | NOT FOUND                          | NOT FOUND                                          | THREE INTERNATIONAL FINANCE CENTRE |
    demo.search_estate_building_name(['THREE INTERNATIONAL FINANCE CENTRE'])

    ## case 3: invalid input
    # [ERROR] Input does not match data type or is empty list object.
    demo.search_estate_building_name('TWO INTERNATIONAL FINANCE CENTRE')
    demo.search_estate_building_name([])