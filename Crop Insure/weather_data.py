from bs4 import BeautifulSoup
from urllib.request import urlopen
import csv

from selenium import webdriver
from selenium.webdriver.support.ui import Select
import selenium
import time

def get_data(state, district, loc_dict, count=0):

    '''
    The function will grab the rainfall data for the years it is available from
    a specific website and return lists containing the headers and data for each
    location.

    state(str): The specific state which has the district for which the data
                needs to be collected
    district(str): The district in the state for which the data needs to be
                   collected
    loc_dict(dict): Dictionary containing districts to pull data from based on
                    the region of larger states.
    count(int): Key for districts that are in the same region of CUDDAPAH

    '''

    #Initializing Selenium browser
    browser = webdriver.Firefox()
    #Making get request to Indian Meteorological Department website
    browser.get("http://hydro.imd.gov.in/hydrometweb/(S(wdk1wgqowpasuw55hpmgzg55))/DistrictRaifall.aspx")
    #Selecting drop down menu for states
    select = Select(browser.find_element_by_id('listItems'))
    #Taking care of the split up region of MAHARASHTRA

    if 'MAHARASHTRA' in state:
        st = 'MAHARASHTRA'
        dis = district
    else:
        st = state
        dis = district

    #Selecting relevant State
    select.select_by_visible_text(st)
    time.sleep(1)
    #Selecting drop down menu for Districts
    select2 = Select(browser.find_element_by_id('DistrictDropDownList'))
    #Selecting relevant District
    select2.select_by_visible_text(dis)

    browser.find_element_by_id('GoBtn').click()

    table = browser.page_source

    soup = BeautifulSoup(table, "lxml")
    table2 = soup.find('table', {'id': 'GridId'})

    #Parsing through the page source and creating a list for the headers in csv
    headers = []
    for th in table2.select("tr th"):
        if th.text.strip() != 'YEAR':
            headers.append(th.text.strip())
            #headers.append(th.text.strip())
        else:
            headers.append(th.text.strip())
    headers.append('Location')

    #Parsing through the page source and creating a list of lists containing the
    #rainfall information for the relevant district, state
    data = []
    for row in table2.select("tr + tr"):
        rows = []
        for i, td in enumerate(row.find_all("td")):
            if i % 2 == 0 or i == 1:
                rows.append(td.text.strip())
        if 'MAHARASHTRA' not in state and count:
            rows.append(loc_dict[district][count])
        elif 'MAHARASHTRA' not in state:
            rows.append(loc_dict[district])
        else:
            rows.append(state)

        data.append(rows[1:])
    browser.quit()

    return headers, data

if __name__ == '__main__':

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

    loc_dict = {'MAHARASHTRA1': 'MAHARASHTRA1', 'MAHARASHTRA2': 'MAHARASHTRA2',
                'MAHARASHTRA3': 'MAHARASHTRA3', 'MAHARASHTRA4': 'MAHARASHTRA4',
                'CUDDAPAH': {1:'DUVVURU', 2:'PORUMAMILLA', 3:'S MYDUKUR'}, 'WEST GODAVARI': 'ELURU',
                'KURNOOL':'KURNOOL', 'THENI': 'CUMBAM', 'KHAMMAM': 'SATHUPALLY',
                'EAST GODAVARI': 'RAJAHAMANDRY', 'PRAKASAM': 'MARKAPUR', 'KARIMNAGAR':'KARIMNAGAR',
                'WARANGAL': 'WARANGAL', 'GUNTUR': 'GUNTUR', 'BALLARI': 'BALLARI'}

    #Writing the tabular rainfall data to csv file weather_data_test.csv

    with open("weather_data_test.csv", "w") as f:
        wr = csv.writer(f)
        header, data = get_data('KARNATAKA', 'BALLARI', loc_dict)
        wr.writerow(header[2:])
        wr.writerows(data[2:])

        for i, z in enumerate(zip(states, districts)):
            state = z[0]
            district = z[1]

            #Ensuring the right district name is used for regions containing
            #multiple districts
            
            if i == 0:
                headers, data = get_data(state, district, loc_dict, count=1)
            if i == 7:
                headers, data = get_data(state, district, loc_dict, count=2)
            if i == 12:
                headers, data = get_data(state, district, loc_dict, count=3)
            else:
                headers, data = get_data(state, district, loc_dict)

            wr.writerows(data[2:])
            time.sleep(3)
