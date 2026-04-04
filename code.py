import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="whitegrid")

# rs = np.random.RandomState(365)
# values = rs.randn(365, 4).cumsum(axis=0)
# dates = pd.date_range("1 1 2016", periods=365, freq="D")
# data = pd.DataFrame(values, dates, columns=["A", "B", "C", "D"])
# data = data.rolling(7).mean()

# sns.lineplot(data=data, palette="tab10", linewidth=2.5)


def scrape_schedule707(filename):
    """ extract Squamish info for a single year from a Schedule 707 file.
        return dataframe
    """
    print(f'scraping {filename}')
    df = pd.read_excel(filename, header=1, usecols='A,E,F,G,H,K,L,M')
    squamish = df[ df['Municipalities'] == 'Squamish'].copy()
    squamish.drop('Municipalities', axis='columns', inplace=True)
    squamish.set_index('Property Class', inplace=True)
    squamish.drop('Supportive Housing', axis='index', inplace=True)
    squamish.rename(columns={'Authenticated Roll General Taxable Values': 'Current Net Taxable Value',
                             'Municipal Purposes Tax Rates': 'Rates',
                             'Total Municipal Taxes': 'Tax Revenue',
                             'Tax Class Multiples': 'Ratios'},
                    index={'Business/Other': 'Business',
                           'Managed Forest': 'Forest'},
                    inplace=True)

    return squamish

def scrape_schedule707_all(start=2015, end=2025):
    """ extract Squamish info for a range of years from a directory of Schedule 707 files.
        return dictionary of dataframes, indexed by year.
    """
    data = {}

    years = range(start, end+1)

    for year in years:
        if year > 2019:
            filename = f'data/schedule707_{year}.xlsx'
        else:
            filename = f'data/schedule707_{year}.xls'

        print(f'scraping year {year}')
        data[year] = scrape_schedule707(filename)

    return data



schedule707 = scrape_schedule707_all()
years = sorted(schedule707.keys())
value = [schedule707[y]['Current Net Taxable Value']['Totals'] for y in years]
revenue = [schedule707[y]['Tax Revenue']['Totals'] for y in years]

plot_df = pd.DataFrame({'Year': years, 'Current Net Taxable Value': value, 'Tax Revenue': revenue})

def plot_data(var):
    if( var=='value' ):
        sns.lineplot(data=plot_df, x='Year', y='Current Net Taxable Value', marker='o')
    elif( var=='revenue'):
        sns.lineplot(data=plot_df, x='Year', y='Tax Revenue', marker='o')

#plot_value()
#plot_revenue()