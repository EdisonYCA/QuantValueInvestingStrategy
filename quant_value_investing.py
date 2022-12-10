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

    # creating dataframe
    # api_endpoint = f"https://sandbox.iexapis.com/stable/stock/AAL/quote?token={IEX_CLOUD_TOKEN}"
    # data = requests.get(api_endpoint).json()
    stocks_batch = list(split_list(stocks["Ticker"], 100))
    stocks_batch_strings = []
    for i in range(0, len(stocks_batch)):
        print(stocks_batch[i])


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
