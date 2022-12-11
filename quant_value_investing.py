import numpy as np
import pandas as pd
import xlsxwriter
import requests
from scipy.stats import percentileofscore as score
from statistics import mean
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

    columns = ["Stock",
               "Price",
               "Price to Earnings",
               "Price to Earnings Percentile",
               "Price to Book",
               "Price to Book Percentile",
               "Price to Sales",
               "Price to Sales Percentile",
               "EV/EBITDA",
               "EV/EBITDA Percentile",
               "EV/GP",
               "EV/GP Percentile",
               "Robust Score",
               "Number of Shares to Buy"]
    dataframe = pd.DataFrame(columns=columns)

    # append each stock as new row of information
    for stock_str in stocks_batch_strings:
        # call api at each batch
        api_endpoint = f"https://sandbox.iexapis.com/stable/stock/market/batch?symbols={stock_str}" \
                       f"&types=quote,advanced-stats&token={IEX_CLOUD_TOKEN}"
        data = requests.get(api_endpoint).json()
        # append each row
        for stock in stock_str.split(','):
            row = pd.DataFrame([stock,
                                data[stock]['quote']['latestPrice'],
                                data[stock]['quote']['peRatio'],
                                "N/A",
                                data[stock]['advanced-stats']['priceToBook'],
                                "N/A",
                                data[stock]['advanced-stats']['priceToSales'],
                                "N/A",
                                calculate_ev_to_ebidta(data[stock]['advanced-stats']['enterpriseValue'],
                                                       data[stock]['advanced-stats']['EBITDA']),
                                "N/A",
                                calculate_ev_to_gp(data[stock]['advanced-stats']['enterpriseValue'],
                                                   data[stock]['advanced-stats']['grossProfit']),
                                "N/A",
                                "N/A",
                                "N/A"],
                               index=columns).T
            dataframe = pd.concat((dataframe, row), ignore_index=True)
    # fill missing nan values
    for column in dataframe.columns[2:12:2]:
        dataframe[column].fillna(dataframe[column].mean(), inplace=True)

    # calculating percentiles
    metrics = {
               "Price to Earnings": "Price to Earnings Percentile",
               "Price to Book": "Price to Book Percentile",
               "Price to Sales": "Price to Sales Percentile",
               "EV/EBITDA": "EV/EBITDA Percentile",
               "EV/GP": "EV/GP Percentile"}

    for metric in metrics:
        for i in dataframe.index:
            dataframe.loc[i, metrics[metric]] = score(dataframe[metric], dataframe.loc[i, metric]) / 100

    # calculating RV scores
    for i in dataframe.index:
        percentiles = []
        for column in dataframe.columns[3:12:2]:
            percentiles.append(dataframe.loc[i, column])
        dataframe.loc[i, "Robust Score"] = mean(percentiles)

    # removing glamour stocks and selecting best value stocks
    dataframe.sort_values("Robust Score", inplace=True)
    # drop all stocks not in top 50
    dataframe = dataframe[:50]
    # reset indices of each row
    dataframe.reset_index(inplace=True, drop=True)

    # calculating number of shares to buy
    portfolio_size = get_portfolio_input()
    position_size = portfolio_size / len(dataframe.index)  # amount user should invest in each stock
    for i in range(0, len(dataframe.index)):
        stock_price = dataframe.loc[i, "Price"]
        dataframe.loc[i, "Number of Shares to Buy"] = math.floor(position_size / stock_price)

    # save output to excel
    format_excel_output(dataframe)


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
    """split lst into sub-lists of n"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def calculate_ev_to_ebidta(enterprise_value, ebitda):
    """Calculate enterprise value to ebidta of a company"""
    try:
        return enterprise_value / ebitda
    except TypeError:  # accommodate for companies that do not report ev or ebitda
        return np.NaN


def calculate_ev_to_gp(enterprise_value, gross_profit):
    """Calculate enterprise value to gross profit"""
    try:
        return enterprise_value / gross_profit
    except TypeError:  # accommodate for companies that do not report ev or gross profit
        return np.NaN


def get_portfolio_input():
    """Get the amount of a users portfolio"""
    while True:
        try:
            portfolio_amount = float(input("Enter the value of your portfolio: "))
            if type(portfolio_amount) == float:
                return portfolio_amount
        except ValueError:
            print("\nPortfolio amount must be a decimal.")


def format_excel_output(dataframe):
    """saves and formats dataframe into an Excel file"""
    writer = pd.ExcelWriter('Value Strategy.xlsx', engine='xlsxwriter')
    dataframe.to_excel(writer, 'Value Strategy', index=False)

    background_color = '#ffffff'
    font_color = '#000000'

    string_format = writer.book.add_format(  # format for strings
        {
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

    dollar_format = writer.book.add_format(  # format for currency
        {
            'num_format': '$0.00',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

    integer_format = writer.book.add_format(  # format for integers
        {
            'num_format': '0',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

    float_format = writer.book.add_format(  # format for floats
        {
            'num_format': '0.0',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

    percent_format = writer.book.add_format(  # format for percentages
        {
            'num_format': "0.0%",
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

    columns_formats = {  # format for column names
       'A': ["Stock", string_format],
       'B': ["Price", dollar_format],
       'C': ["Price to Earnings", float_format],
       'D': ["Price to Earnings Percentile", percent_format],
       'E': ["Price to Book", float_format],
       'F': ["Price to Book Percentile", percent_format],
       'G': ["Price to Sales", float_format],
       'H': ["Price to Sales Percentile", percent_format],
       'I': ["EV/EBITDA", float_format],
       'J': ["EV/EBITDA Percentile", percent_format],
       'K': ["EV/GP", float_format],
       'L': ["EV/GP Percentile", percent_format],
       'M': ["Robust Score", percent_format],
       'N': ["Number of Shares to Buy", integer_format]
    }

    for column in columns_formats.keys():
        writer.sheets['Value Strategy'].set_column(f'{column}:{column}', 30, columns_formats[column][1])
        writer.sheets['Value Strategy'].write(f'{column}1', columns_formats[column][0], columns_formats[column][1])
    writer.close()

    print("Output has been place in: 'Value Strategy.xlsx'")


if __name__ == "__main__":
    main()
