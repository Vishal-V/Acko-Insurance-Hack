from bs4 import BeautifulSoup
from urllib.request import urlopen
import csv
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from io import BytesIO, StringIO
import boto3
import selenium
import time
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.wait import WebDriverWait

def get_loc(village, location, browser, state_dict):
    '''
    This function will get the Latitude and Longitude of the relevant village
    and location from a specific website and will return a tuple
    containing location, village, latitude, longitude

    village(str): String specifying the name of the village for which the
                  latitude and longitude are returned
    location(str): String specifying the name of the location for which the
                  latitude and longitude are returned
    browser(webdriver): Webdriver object that will be used to make get requests
                        and for obtaining the page source
    state_dict(dict): Dictionary mapping the location for each village to the
                      state. The village name and state will then be used to
                      search for latitude and longitude
    '''

    #browser.get("https://www.google.com/maps")

    #browser.get("https://www.latlong.net/")

    #Making a get request to the relevant website using the Selenium browser
    browser.get("https://www.findlatitudeandlongitude.com/")
    time.sleep(2)

    #Locating the input text box for the address, where the village and state
    #name are input
    search = browser.find_element_by_xpath("//input[@name='address']")
    #search = browser.find_element_by_id("tc1709").click()
    #search.send_keys('{}, {}, {}'.format(village, location, state_dict[location]))

    #Entering the village and state names in the address input box
    search.send_keys('{}, {}'.format(village, state_dict[location]))
    #search.send_keys(Keys.ENTER)
    time.sleep(2)
    #text = browser.page_source

    #The coordinates for the entered address are searched for
    browser.find_element_by_css_selector('input#load_address_button').click()
    time.sleep(2)
    #coord = browser.current_url.split('@')[1].split(',')
    soup = BeautifulSoup(browser.page_source.encode('utf-8').strip(),
                                                'html.parser')

    #Taking care degree symbol after coordinate float and for differing lengths
    #of latitude and longitude

    try:
        coord_lat = soup.find('span', {'id': 'lat_dec'}).find('span',
                                        {'class': 'value'}).get_text()[:6]
        coord_lon = soup.find('span', {'id': 'lon_dec'}).find('span',
                                        {'class': 'value'}).get_text()[:6]

        return location, village, float(coord_lat), float(coord_lon)
    except:

        coord_lat = soup.find('span', {'id': 'lat_dec'}).find('span',
                                        {'class': 'value'}).get_text()[:4]
        coord_lon = soup.find('span', {'id': 'lon_dec'}).find('span',
                                        {'class': 'value'}).get_text()[:4]
        return location, village, float(coord_lat), float(coord_lon)
    #except:
        #return location, village, '', ''

if __name__ == '__main__':
    #df = pd.read_csv('village_names.csv')
    #places = df[df['Location'] == 'MAHARASHTRA']['Village'].unique()




    loc_dict = {'MAHARASHTRA': 'JAKAPUR', 'MAHARASHTRA1': 'GOLEGAON',
                'MAHARASHTRA2': 'KAKANDI', 'MAHARASHTRA3': 'GANPUR',
                'MAHARASHTRA4': 'DAHEGAON'}


    #Reading in the village and location names
    start = time.time()
    df = pd.read_csv('village_location_duplicates.csv')
    #places = df['Location'].unique()
    df.drop(columns='Unnamed: 0', inplace=True)
    location_groups = df.groupby(by='Location')
    village_dict = {}

    #Creating dictionary that has village names as keys and locations as values
    for loc, group in location_groups:
        for vill in set(group['Village'].values):
            village_dict[vill] = loc

    states = ['KARNATAKA', 'TAMILNADU', 'KADAPA, ANDHRA PRADESH', 'KADAPA, ANDHRA PRADESH',
              'W GODAVARI, ANDHRA PRADESH', 'KHAMMAM, TELANGANA','TELANGANA', 'ANDHRA PRADESH',
              'MAHARASHTRA', 'PRAKASAM, ANDHRA PRADESH', 'KADAPA, ANDHRA PRADESH','E GODAVARI, ANDHRA PRADESH',
              'TELANGANA']

    #Creating dictionary that has locations as keys and states as values
    state_dict = dict(zip(df['Location'].unique(), states))

    #Initializing headless Selenium webdriver and boto3 client to interact
    #with AWS S3 bucket
    options = Options()
    options.add_argument('-headless')
    browser = Firefox(executable_path='geckodriver', firefox_options=options)
    s3 = boto3.client('s3')

    #Writing the latitude and longitude data for each village to csv file in
    #AWS S3 bucket
    with StringIO() as f:
        wr = csv.writer(f)
        wr.writerow(['Location', 'Village', 'Latitude', 'Longitude'])

        for village, location in village_dict.items():
            data = get_loc(village, location, browser, state_dict)
            wr.writerow(data)


            s3.put_object(Bucket='capstone-web-scrape',
                          Key='duplicates_village_location_data.csv',
                          Body=f.getvalue())
            time.sleep(4)
    print (time.time() - start)

'''    with open("location_coord_data.csv", "w") as f:
        wr = csv.writer(f)
        wr.writerow(['State', 'Location', 'Latitude', 'Longitude'])

        for place, state in zip(places, states):

            if 'MAHARASHTRA' in place:
                data = get_loc(loc_dict[place], state)
            else:
                data = get_loc(place, state)

            wr.writerow(data)
            time.sleep(3)'''
