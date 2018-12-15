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


def get_alt(village, location, browser, state_dict, lat, lon):
    '''
    The function takes in the name of the village and it's location along with
    the coordinates and uses that information to return the elevation of the
    coordinates/location

    village(str): String specifying the name of the village for which the
                  latitude and longitude are returned
    location(str): String specifying the name of the location for which the
                  latitude and longitude are returned
    browser(webdriver): Webdriver object that will be used to make get requests
                        and for obtaining the page source
    state_dict(dict): Dictionary mapping the location for each village to the
                      state. The village name and state will then be used to
                      search for latitude and longitude
    lat(float): The latitude for the village in degrees
    lon(float): The longitude for the village in degrees
    '''

    #Making a get request to website from which elevation data can be acquired
    browser.get("https://www.whatismyelevation.com")
    #Locating element using which location can be entered
    browser.find_element_by_id("change-location").click()
    time.sleep(2)

    #Entering location/coordinates to search for the elevation
    search = browser.find_element_by_id("address")
    search.send_keys('{}, {}'.format(lat, lon))

    #Making sure the changes were registered
    search.send_keys(Keys.ENTER)
    search.send_keys(Keys.ENTER)
    search.send_keys(Keys.ENTER)

    time.sleep(3)
    text = browser.page_source
    #coord = browser.current_url.split('@')[1].split(',')
    soup = BeautifulSoup(text, "lxml")

    #Parsing through the page source to find the elevation for the location
    elevation = soup.find('div', {'id':'elevation'})
    altitude = elevation.find('span', {'class': "value"})

    #Converting to float only if there is elevation data present for this
    #location
    if len(altitude.decode().split('>')[1].split('<')[0].replace(',', '')) > 0:
        alt = float(altitude.decode().split('>')[1].split('<')[0].replace(',', ''))
    else:
        alt = altitude.decode().split('>')[1].split('<')[0].replace(',', '')

    return location, village, alt

if __name__ == '__main__':
    df = pd.read_csv('complete_vill_loc.csv')
    #Reading in the village and location names
    df.drop(columns='Unnamed: 0', inplace=True)
    location_groups = df.groupby(by='Location')
    village_dict = {}

    #Creating dictionary that has village names as keys and locations as values
    for loc, group in location_groups:
        for vill in set(group['Village'].values):
            village_dict[vill] = loc

    states = ['KARNATAKA', 'ANDHRA PRADESH', 'ANDHRA PRADESH', 'MAHARASHTRA', 'ANDHRA PRADESH', 'ANDHRA PRADESH',
              'TAMILNADU', 'TELANGANA', 'ANDHRA PRADESH', 'ANDHRA PRADESH', 'ANDHRA PRADESH',
              'TELANGANA', 'TELANGANA', 'ANDHRA PRADESH']

    #Creating dictionary that has locations as keys and states as values
    state_dict = dict(zip(df['Location'].unique(), states))

    #Initializing headless Selenium webdriver and boto3 client to interact
    #with AWS S3 bucket
    options = Options()
    options.add_argument('-headless')
    browser = Firefox(executable_path='geckodriver', firefox_options=options)
    #browser = Firefox()
    s3 = boto3.client('s3')

    #Writing the elevation data for each village to csv file in AWS S3 bucket
    with StringIO() as f:
        wr = csv.writer(f)
        wr.writerow(['Location', 'Village', 'Elevation'])

        for village, location in village_dict.items():

            lat = df[df['Village'] == village]['Latitude'].values[0]
            lon = df[df['Village'] == village]['Longitude'].values[0]
            print (lat, lon)
            data = get_alt(village, location, browser, state_dict, lat, lon)
            print (data)
            wr.writerow(data)
            time.sleep(2)

            s3.put_object(Bucket='capstone-web-scrape',
                          Key='new_village_altitude_data.csv',
                          Body=f.getvalue())


'''    with open("village_altitude_data.csv", "w") as f:
        wr = csv.writer(f)
        wr.writerow(['State', 'Location', 'Altitude'])

        for location, state in zip(places, states):
            data = get_alt(location, state, browser)
            wr.writerow(data)
            time.sleep(2)'''
