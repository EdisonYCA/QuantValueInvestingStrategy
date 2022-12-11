import numpy as np
import pandas as pd
import xlsxwriter
import requests
from scipy import stats
import math
import os
from api_token import IEX_CLOUD_TOKEN


def main():
    stocks = pd.read_csv("sp_500_stocks.csv")  # change to get_file function
    stocks = stocks[~stocks['Ticker'].isin(['DISCA', 'HFC', 'VIAC', 'WLTW'])]  # DELETE WHEN DONE WITH PROGRAM

    # creating dataframe
    stocks_batch = list(split_list(stocks["Ticker"], 100))
    stocks_batch_strings = []
    for i in range(0, len(stocks_batch)):
        stocks_batch_strings.append(','.join(stocks_batch[i]))

    columns = ["Stock", "Price", "Price to Earnings", "Numbers of Shares to Buy"]
    dataframe = pd.DataFrame(columns=columns)

    # append each stock as new row of information
    for stock_str in stocks_batch_strings:
        # call api at each batch
        api_endpoint = f"https://sandbox.iexapis.com/stable/stock/market/batch?symbols={stock_str}" \
                       f"&types=quote&token={IEX_CLOUD_TOKEN}"
        data = requests.get(api_endpoint).json()
        # append each row
        for stock in stock_str.split(','):
            row = pd.DataFrame([stock,
                                data[stock]['quote']['latestPrice'],
                                data[stock]['quote']['peRatio'],
                                "N/A"],
                               index=columns).T
            dataframe = pd.concat((dataframe, row), ignore_index=True)

    # removing glamour stocks
    dataframe.sort_values("Price to Earnings", inplace=True)
    # removes all rows that have negative earnings ratio
    dataframe = dataframe[dataframe["Price to Earnings"] > 0]
    # removes all rows that are not in top 50
    dataframe = dataframe[:50]
    # reset indices of each row
    dataframe.reset_index(inplace=True, drop=True)
    print(dataframe)

def get_file():
    """Prompt the user for a csv file containing a list of stocks
    and validate the file exists in the current directory"""
    while True:
        file_name = input("Enter the name of your csv file: ")
        if os.path.isfile(file_name):
            print("File opened successfully\n")
            return file_name
        else:
            print("This file does not exist. Please confirm the file is in this directory and try again.")


def split_list(lst, n):
    """Split list into sublist of n length"""
    for x in range(0, len(lst), n):
        yield lst[x: x+n]


if __name__ == "__main__":
    main()
