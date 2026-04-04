import pandas as pd
import seaborn as sns

# seaborn settings
sns.set_theme(style="whitegrid")

# data cleaning
def scrape_schedule707(filename):
    """ extract Squamish info for a single year from a Schedule 707 file.
        return dataframe
    """
    print(f'scraping {filename}')
    df = pd.read_excel(filename, header=1, usecols='A,D,E,F,G,H,K,L,M,N')
    squamish = df[ df['Municipalities'] == 'Squamish'].copy()
    squamish.drop('Municipalities', axis='columns', inplace=True)
    squamish.set_index('Property Class', inplace=True)
    squamish.drop('Supportive Housing', axis='index', inplace=True)

    # rename the population column (name varies by year) to a consistent name
    pop_col = [c for c in squamish.columns if 'Population' in str(c)][0]
    squamish.rename(columns={pop_col: 'Population'}, inplace=True)

    squamish.rename(columns={'Authenticated Roll General Taxable Values': 'Current Net Taxable Value',
                             'Municipal Purposes Tax Rates': 'Rates',
                             'Total Municipal Taxes': 'Tax Revenue',
                             'Tax Class Multiples': 'Ratios',
                             'Municipal Taxes Per Capita': 'Municipal Taxes Per Capita'},
                    index={'Business/Other': 'Business',
                           'Managed Forest': 'Forest'},
                    inplace=True)

    return squamish

# read all years
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
population = [schedule707[y]['Population']['Totals'] for y in years]
per_capita = [schedule707[y]['Municipal Taxes Per Capita']['Totals'] for y in years]

plot_df = pd.DataFrame({
    'Year': years,
    'Total Property Value ($ billions)': [v / 1e9 for v in value],
    'Tax Revenue ($ millions)': [r / 1e6 for r in revenue],
    'Population (thousands)': [p / 1e3 for p in population],
    'Municipal Taxes per Capita': per_capita
})

def plot_data(var):
    if( var=='Total Property Value' ):
        sns.lineplot(data=plot_df, x='Year', y='Total Property Value ($ billions)', marker='o')
    elif( var=='Total Municipal Taxes'):
        sns.lineplot(data=plot_df, x='Year', y='Tax Revenue ($ millions)', marker='o')
    elif( var=='Population'):
        sns.lineplot(data=plot_df, x='Year', y='Population (thousands)', marker='o')
    elif( var=='Municipal Taxes per Capita'):
        sns.lineplot(data=plot_df, x='Year', y='Municipal Taxes per Capita', marker='o')

#plot_value()
#plot_revenue()