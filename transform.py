import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
#from mpl_toolkits.basemap import Basemap
from pandas.plotting import scatter_matrix
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split
import time
from datetime import datetime
from sklearn.preprocessing import StandardScaler


def transform_orginal(df, location_df):
    '''
    The function performs a series of transformations to the input DataFrame:
        - The misspelled location names were corrected
        - New columns were created, Year, Sow Month, Sowing Week, etc
        - A new response column/variable was made by dividing the dried yield by
          the standing area of the field
        - The datetime variables were converted to days since the start of the
          respective year
        - The location of MAHARASHTRA was split into 5 smaller locations, due to
          the large size of the state

    df (DataFrame): DataFrame containing the crop data. The different seasons,
                    varieties, locations, size of farms along with the dry and
                    gross yield.

    location_df (DataFrame): DataFrame containing the latitude and longitude for
                             the different villages present in MAHARASHTRA.

    '''
    location_df.drop(columns='Unnamed: 0', inplace=True)

    #Starting the transformations that are made to the input df
    df.loc[df['Location'] == 'BELLARY', 'Location'] =  'BALLARI'
    df['YEAR'] = df['Sown \nDate'].apply(lambda x: x.year)
    df['Sow Month'] = df['Sown \nDate'].apply(lambda x: x.month)
    df['Sowing Week'] = df['Sowing Week'].apply(lambda x: x[-6])
    df['Days Till Harvest'] = (df['Harvest Date'] - df['Sown \nDate']).dt.days
    df['Sowing Week of Year'] = df[['Sowing Week', 'Sow Month']].apply(
                                        lambda x: int(x['Sowing Week']) +
                                        (int(x['Sow Month']) * 4), axis=1)

    df['Dry Yield Per Acre'] = (df['Dried Yield (Metric Tons)'] /
                                df['Standing Area \n(Acres)'] )

    df['Sown \nDate'] = df['Sown \nDate'].apply(lambda x:
                                              int(
                                                    time.mktime(
                                                    x.timetuple())
                                                    / 86400
                                                 )
                                                 -
                                              int(
                                                    time.mktime(
                                                    datetime(
                                                    x.timetuple()[0],
                                                    1, 1).timetuple()
                                                    )
                                                    / 86400
                                                 )
                                              )

    #Using KMeans clustering to split location MAHARASHTRA into 5 sub-locations
    cluster_dict = {0:'3', 1:'4', 2:'1', 3:'', 4:'2'}

    km = KMeans(n_clusters=5, random_state=0, n_init=15, max_iter=400, n_jobs=-1)
    x = location_df[['Latitude', 'Longitude']]
    km.fit(x)
    clusters = km.predict(x)
    cluster_list = [x.values[clusters == i] for i in range(5)]
    full_cluster_list = [location_df.values[clusters == i] for i in range(5)]

    vil_names = [location_df[clusters == i]['Village'].values for i in range(5)]

    #Changing names of locations from MAHARASHTRA to their respective
    #sub-location
    for i in range(5):
        #df2.loc[df2['Village'].values in vil_names[i], 'Location'] = 'MAHARASHTRA'+ cluster_dict[i]
        df['Location'] = df['Village'].apply(lambda x:
                                             ('MAHARASHTRA'+ cluster_dict[i])
                                             if x in vil_names[i]
                                             else
                                             df[df['Village'] == x]['Location'].values[0],
                                             0)

    return df


def merge_transform(df, rainfall_df, altitude_df, lat_lon_df):
    '''
    The function takes in a DataFrame and weather, location DataFrames and
    returns a merged DataFrame which contains all the input DataFrames

    df(DataFrame): The DataFrame containing the crop and farm information
    rainfall_df(DataFrame): The DataFrame containing the rainfall data for the
                            different locations
    altitude_df(DataFrame): The DataFrame containing the elevation data for the
                            different locations
    lat_lon_df(DataFrame): The DataFrame containing the latitude and longitude
                           data for the different locations
    '''

    lat_lon_df.drop(columns='Unnamed: 0', inplace=True)
    #altitude_df.drop(columns='Unnamed: 0', inplace=True)

    location_df = lat_lon_df[lat_lon_df['Location'] == 'MAHARASHTRA']

    cluster_dict = {0:'3', 1:'4', 2:'1', 3:'', 4:'2'}

    km = KMeans(n_clusters=5, random_state=0, n_init=15, max_iter=400, n_jobs=-1)
    x = location_df[['Latitude', 'Longitude']]
    km.fit(x)
    clusters = km.predict(x)
    cluster_list = [x.values[clusters == i] for i in range(5)]
    full_cluster_list = [location_df.values[clusters == i] for i in range(5)]

    vil_names = [location_df[clusters == i]['Village'].values for i in range(5)]

    #Renaming the locations in the other DataFrames according to the
    #sub-locations from transform_original()
    for data in [lat_lon_df, altitude_df]:
        for i in range(5):
            #df2.loc[df2['Village'].values in vil_names[i], 'Location'] = 'MAHARASHTRA'+ cluster_dict[i]
            data['Location'] = data['Village'].apply(lambda x:
                                                 ('MAHARASHTRA'+ cluster_dict[i])
                                                 if x in vil_names[i]
                                                 else
                                                 df[df['Village'] == x]['Location'].values[0],
                                                 0)

    rain_org_df = pd.merge(df, rainfall_df, on=['Location', 'YEAR'])

    #The Rainfall is aggregated based on the rainfall received during the first
    #three months after the crop has been sown
    rain_org_df['Rainfall'] = rain_org_df.apply(lambda x:
                                                (x[str(x['Sow Month'])] +
                                                 x[str(x['Sow Month'] + 1)] +
                                                 x[str(x['Sow Month'] + 2)])

                                                if x['Sow Month'] < 11
                                                else

                                                (x[str(x['Sow Month'])] +
                                                x[str(x['Sow Month'] + 1)] +
                                                6.05)

                                                if x['Sow Month'] < 12
                                                else

                                                (x[str(x['Sow Month'])] + 7.05),
                                                 axis=1)

    inter_df = pd.merge(rain_org_df, altitude_df, on=['Village'])
    final_df = pd.merge(inter_df, lat_lon_df, on=['Village'])

    return final_df.drop(columns=[str(i) for i in range(1, 13)])

def featurize(df, X_cols, y_col, dummy_cols, split=True):
    '''
    This functions takes in an input DataFrame along with lists of column names
    that will be used in creating the feature matrix and the response variable.
    Returns standardized and dummy encoded X and y or
    X_train, X_test, y_train, y_test based on the value of "split"

    df(DataFrame): The input DataFrame on which the standardization and dummy
                   encoding is performed
    X_cols(list): The list of strings that represents the column names that will
                  be part of the feature matrix, X
    y_col(string): String representing the column name that will be used as the
                   response
    dummy_cols(list): List of strings that represent the column names that will
                      dummy encoded in the feature matrix, X
    split(bool): If True, X and y will be split into Train and Test

    '''
    #X_initial = df[X_cols]
    #y = df[y_col]


    #X = pd.get_dummies(X_initial, columns=dummy_cols)

    #Initializing sklearn StandardScaler
    ss = StandardScaler()
    X_initial = df[X_cols]
    y = df[y_col]
    ss.fit(X_initial)
    X_scaled = pd.DataFrame(ss.transform(X_initial), columns=X_cols)

    #Adding the dummy_col column to the scaled DataFrame
    X_new = pd.concat([X_scaled, df[dummy_cols].astype(str)], axis=1)

    #Dummy encoding the scaled DataFrame
    X = pd.get_dummies(X_new, columns=dummy_cols)
    X.dropna(inplace=True)

    if not split:
        return X, y

    X_train, X_test, y_train, y_test = train_test_split(X, y)

    return X_train, X_test, y_train, y_test

def groups(df, X_cols, y_col, dummy_cols, group_by='Location'):
    '''
    This functions takes in an input DataFrame and returns a dictionary that has
    the locations as keys and X and y for each location as values 

    df(DataFrame): The input DataFrame using which the data is grouped
    X_cols(list): The list of strings that represents the column names that will
                  be part of the feature matrix, X
    y_col(string): String representing the column name that will be used as the
                   response
    dummy_cols(list): List of strings that represent the column names that will
                      dummy encoded in the feature matrix, X
    group_by(string): Column name that the data will be grouped by

    '''
    group = pd.groupby(by='Location')
    grp_dict = {}

    for i, grp in group:
        grp_dict[i] = featurize(grp, X_cols, y_col, dummy_cols)

    return grp_dict



#AFTER merge_transform, THE DATAFRAME HAS BEEN MERGED WITH RAINFALL AND ALTITUDE
#THE RAINFALL HAS BEEN CALCULATED AND MERGED ON LOCATION AND YEAR, THE ALT IS
# MERGED ON JUST LOCATION.
