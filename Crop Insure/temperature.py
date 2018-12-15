import pandas as pd
from bs4 import BeautifulSoup
#from urllib.request import urlopen
import csv
from io import BytesIO, StringIO
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import boto3
import selenium
import time
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.wait import WebDriverWait
import multiprocessing as mp
import re

def get_temp(village, location, browser, state_dict, count=0):
    '''
    This function takes in the name of the village along with the location and
    returns the minimum and maximum temperatures for each month from the year
    2014 to 2017

    village(str): String specifying the name of the village for which the
                  latitude and longitude are returned
    location(str): String specifying the name of the location for which the
                  latitude and longitude are returned
    browser(webdriver): Webdriver object that will be used to make get requests
                        and for obtaining the page source
    state_dict(dict): Dictionary mapping the location for each village to the
                      state. The village name and state will then be used to
                      search for latitude and longitude
    count(int): Key for districts that are in the same region of CUDDAPAH
    '''

    #Making a get request to website from which temperature data can be acquired
    browser.get("https://www.wunderground.com/history/")
    #To make sure the page is rendered properly in headless mode
    browser.maximize_window()
    #Locating element using which location can be entered
    search = browser.find_element_by_id("histSearch")
    #search.send_keys('{}, {}, {}'.format(village, location, state_dict[location]))

    #if 'MAHARASHTRA' in village:
        #search.send_keys('{}'.format(state_dict[village]))
    #else:
        #search.send_keys('{}'.format(village))

    #Entering the location
    search.send_keys('{}, {}'.format(village, location))

    #Picking middle day of the month
    select = Select(browser.find_element_by_class_name("day"))
    select.select_by_visible_text('14')

    #Selecting 2014 as the year to start data collection
    select2 = Select(browser.find_element_by_class_name("year"))
    select2.select_by_visible_text('2014')

    #Clicking button to load the temperatures
    browser.find_element_by_css_selector("input.button.radius").click()
    time.sleep(2)
    #Change from daily temperature view to monthly
    browser.get(browser.current_url.replace('Daily', 'Monthly'))
    time.sleep(2)

    #browser.find_element_by_css_selector("a.contentTabActive.brTop5").click()
    try:
        soup = BeautifulSoup(browser.page_source.encode('utf-8').strip(),
                                                        'html.parser')
    except:
        soup = BeautifulSoup(browser.page_source, 'lxml')
    #soup = BeautifulSoup(re.sub("<!--|-->","", browser.page_source), "lxml")

    data_max = []
    data_min = []
    try:
        year = int(soup.find('select',
                                    {'class': 'year form-select'}).find('option',
                                    {'selected': "selected"}).get_text())
    except:
        year = 0.0

    while '2017' not in browser.current_url.split('?')[0]:
        row_max = []
        row_min = []
        #Entering the headers for the csv that will contain min and max
        #temperatures for the relevant location
        try:
            row_max.append(int(soup.find('select',
                                        {'class': 'year form-select'}).find('option',
                                        {'selected': "selected"}).get_text()))

            row_min.append(int(soup.find('select',
                                        {'class': 'year form-select'}).find('option',
                                        {'selected': "selected"}).get_text()))
        except:
            row_max.append(0)

            row_min.append(0)

        #Accounting for villages in mulitple regions/states
        if count:
            row_max.append(state_dict[village][count])
            row_min.append(state_dict[village][count])
        else:
            row_max.append(state_dict[village])
            row_min.append(state_dict[village])

        #Collecting max and min temperature data for every month of the year
        for i in range(12):

            #Parsing through the page source to extract the temperature data
            try:
                soup = BeautifulSoup(browser.page_source.encode('utf-8').strip(),
                                                                'html.parser')
            except:
                soup = BeautifulSoup(browser.page_source, 'lxml')

            #soup = BeautifulSoup(re.sub("<!--|-->","", browser.page_source),
                                        #"lxml")
            temp = soup.find_all('span', {'class': 'wx-value'})

            #Inserting zeros for entries where temp data not available
            try:
                row_max.append(float(temp[0].get_text()))
            except:
                row_max.append(0)

            if len(temp) > 5:
                row_min.append(float(temp[5].get_text()))
            else:
                row_min.append(0)

            #print (row_max, row_min)
            #Moving to the next page
            try:
                browser.find_element_by_class_name("next-link").click()
            except:
                continue
            time.sleep(2)

        data_max.append(row_max)
        data_min.append(row_min)


        if (len(data_max) >= 3) or (len(data_min) >= 3):
            break

    return data_max, data_min

    #except:
        #return ([[0, state_dict[village]], [0, state_dict[village]]],
                #[[0, state_dict[village]], [0, state_dict[village]]])

def write_temp(village_dict, browser, state_dict, s3, kind='max'):
    '''
    This function takes in names of villages, locations and their states to
    write the max and min temperature data to a csv in an AWS S3 Bucket

    village_dict(dict): Dictionary where the keys are villages and the values
                        are locations
    browser(webdriver): Webdriver object that will be used to make get requests
                        and for obtaining the page source
    state_dict(dict): Dictionary where the keys are locations and the values
                      are states
    s3(boto3 client): boto3 client that interacts with an AWS S3 bucket
    kind(str): String representing if the max or min temperature data will be
               collected
    '''
    #Writing the temperature data for each village to csv file in AWS S3 bucket
    with StringIO() as f:
        wr = csv.writer(f)

        #Writing headers for the csv file
        wr.writerow(['YEAR','Village','1', '2', '3', '4', '5',
                         '6', '7', '8', '9', '10', '11', '12'])
        #Accounting for multiple locations in the same region
        count = 1
        for village, location in village_dict.items():
            if 'CUDDAPAH' in village:
                data_max, data_min = get_temp(village, location,
                                              browser, state_dict, count)
                count += 1
            else:
                data_max, data_min = get_temp(village, location,
                                              browser, state_dict)

            #Writing either max or min data based on argument "kind"
            if kind == 'max':
                wr.writerows(data_max)

            elif kind == 'min':
                wr.writerows(data_min)


            s3.put_object(Bucket='capstone-web-scrape',
                          Key='village_temp_data_{}.csv'.format(kind),
                          Body=f.getvalue())
            time.sleep(3)
    return None

if __name__ == '__main__':
    #df = pd.read_csv('village_names.csv')
    #places = df[df['Location'] == 'MAHARASHTRA']['Village'].unique()


    loc_dict = {'MAHARASHTRA': 'JAKAPUR', 'MAHARASHTRA1': 'GOLEGAON',
                'MAHARASHTRA2': 'KAKANDI', 'MAHARASHTRA3': 'GANPUR',
                'MAHARASHTRA4': 'DAHEGAON' }

    start = time.time()
    #Reading in the village and location names
    df = pd.read_csv('transform_loc_vill.csv')
    #places = df['Location'].unique()
    df.drop(columns='Unnamed: 0', inplace=True)
    location_groups = df.groupby(by='Location')
    village_dict = {}

    #Creating dictionary that has village names as keys and locations as values
    for loc, group in location_groups:
        for vill in set(group['Village'].values):
            village_dict[vill] = loc

    #states = ['KARNATAKA', 'ANDHRA PRADESH', 'ANDHRA PRADESH', 'MAHARASHTRA',
              #'ANDHRA PRADESH', 'ANDHRA PRADESH','TAMILNADU', 'TELANGANA',
              #'ANDHRA PRADESH', 'ANDHRA PRADESH', 'ANDHRA PRADESH',
              #'TELANGANA', 'TELANGANA', 'ANDHRA PRADESH']

    states = ['KARNATAKA','ANDHRA PRADESH', 'ANDHRA PRADESH', 'MAHARASHTRA',
              'MAHARASHTRA','MAHARASHTRA', 'MAHARASHTRA', 'ANDHRA PRADESH',
              'ANDHRA PRADESH','TAMILNADU', 'TELANGANA', 'ANDHRA PRADESH',
              'ANDHRA PRADESH', 'TELANGANA', 'TELANGANA','ANDHRA PRADESH']

    districts = ['BELLARY','CUDDAPAH', 'WEST GODAVARI', 'THANE', 'PUNE',
                 'OSMANABAD', 'WASHIM',
                 'GADCHIROLI', 'KURNOOL', 'CUDDAPAH', 'THENI', 'KHAMMAM',
                 'EAST GODAVARI', 'PRAKASAM', 'CUDDAPAH', 'KARIMNAGAR', 'WARANGAL',
                  'GUNTUR']

    states = ['KARNATAKA','ANDHRA PRADESH', 'ANDHRA PRADESH', 'MAHARASHTRA',
              'MAHARASHTRA',
              'MAHARASHTRA', 'MAHARASHTRA', 'MAHARASHTRA', 'ANDHRA PRADESH',
              'ANDHRA PRADESH','TAMILNADU', 'TELANGANA', 'ANDHRA PRADESH',
              'ANDHRA PRADESH', 'ANDHRA PRADESH',
              'TELANGANA', 'TELANGANA', 'ANDHRA PRADESH']

    loc_dict = {'THANE': 'MAHARASHTRA1', 'PUNE': 'MAHARASHTRA',
                'GADCHIROLI': 'MAHARASHTRA2','OSMANABAD': 'MAHARASHTRA3',
                'WASHIM': 'MAHARASHTRA4',
                'CUDDAPAH': {1:'DUVVURU', 2:'PORUMAMILLA', 3:'S MYDUKUR'},
                'WEST GODAVARI': 'ELURU','KURNOOL':'KURNOOL', 'THENI': 'CUMBAM',
                 'KHAMMAM': 'SATHUPALLY','EAST GODAVARI': 'RAJAHAMANDRY',
                 'PRAKASAM': 'MARKAPUR', 'KARIMNAGAR':'KARIMNAGAR',
                 'WARANGAL': 'WARANGAL', 'GUNTUR': 'GUNTUR', 'BELLARY': 'BALLARI'}

    #state_dict2 = dict(zip(df['Location'].unique(), states))
    #Creating dictionary that has districts as keys and states as values
    state_dict2 = dict(zip(districts, states))

    #Initializing headless Selenium webdrivers and boto3 client to interact
    #with AWS S3 bucket
    options = Options()
    options.add_argument('-headless')
    browser1 = Firefox(executable_path='geckodriver', firefox_options=options)
    browser2 = Firefox(executable_path='geckodriver', firefox_options=options)

    #browser1 = Firefox()
    #browser2 = Firefox()

    s3 = boto3.client('s3')

    #Creating mulitprocessing threads to obtain max and min data in parallel
    processes = [mp.Process(target=write_temp,
                            args=(state_dict2, browser1,
                                  loc_dict, s3, 'max')),
                 mp.Process(target=write_temp,
                            args=(state_dict2, browser2,
                                  loc_dict, s3, 'min'))]
    for p in processes:
        p.start()

    for p in processes:
        p.join()

    print (time.time() - start)
