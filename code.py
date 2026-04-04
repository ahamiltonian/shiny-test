import pandas as pd
import seaborn as sns

# seaborn settings
sns.set_theme(style="whitegrid")

MUNICIPALITIES = ['Squamish', 'Whistler', 'Pemberton']

# data cleaning
def scrape_schedule707(filename, municipalities=None):
    """ Extract info for a list of municipalities from a single Schedule 707 file.
        municipalities: list of municipality names, or None to return all.
        Returns a dict of DataFrames keyed by municipality name.
    """
    print(f'scraping {filename}')
    df = pd.read_excel(filename, header=1, usecols='A,D,E,F,G,H,K,L,M,N')

    if municipalities is None:
        municipalities = df['Municipalities'].dropna().unique().tolist()

    result = {}
    for muni in municipalities:
        muni_df = df[df['Municipalities'] == muni].copy()
        muni_df.drop('Municipalities', axis='columns', inplace=True)
        muni_df.set_index('Property Class', inplace=True)
        if 'Supportive Housing' in muni_df.index:
            muni_df.drop('Supportive Housing', axis='index', inplace=True)

        # rename the population column (name varies by year) to a consistent name
        pop_col = [c for c in muni_df.columns if 'Population' in str(c)][0]
        muni_df.rename(columns={pop_col: 'Population'}, inplace=True)

        muni_df.rename(columns={'Authenticated Roll General Taxable Values': 'Current Net Taxable Value',
                                 'Municipal Purposes Tax Rates': 'Rates',
                                 'Total Municipal Taxes': 'Tax Revenue',
                                 'Tax Class Multiples': 'Ratios',
                                 'Municipal Taxes Per Capita': 'Municipal Taxes Per Capita'},
                        index={'Business/Other': 'Business',
                               'Managed Forest': 'Forest'},
                        inplace=True)

        result[muni] = muni_df

    return result

# read all years
def scrape_schedule707_all(municipalities=None, start=2015, end=2025):
    """ Extract info for a list of municipalities for a range of years.
        municipalities: list of municipality names, or None to return all.
        Returns a nested dict: data[year][municipality] = DataFrame.
    """
    data = {}

    for year in range(start, end+1):
        if year > 2019:
            filename = f'data/schedule707_{year}.xlsx'
        else:
            filename = f'data/schedule707_{year}.xls'

        print(f'scraping year {year}')
        data[year] = scrape_schedule707(filename, municipalities)

    return data


schedule707 = scrape_schedule707_all(municipalities=MUNICIPALITIES)
years = sorted(schedule707.keys())

# build long-format plot_df with one row per year per municipality
rows = []
for muni in MUNICIPALITIES:
    for y in years:
        muni_df = schedule707[y][muni]
        rows.append({
            'Year': y,
            'Municipality': muni,
            'Total Property Value ($ billions)': muni_df['Current Net Taxable Value']['Totals'] / 1e9,
            'Tax Revenue ($ millions)': muni_df['Tax Revenue']['Totals'] / 1e6,
            'Population': muni_df['Population']['Totals'],
            'Municipal Taxes per Capita': muni_df['Municipal Taxes Per Capita']['Totals'],
        })

plot_df = pd.DataFrame(rows)


def plot_data(var, municipalities):
    if isinstance(municipalities, str):
        municipalities = [municipalities]
    df = plot_df[plot_df['Municipality'].isin(municipalities)]
    col_map = {
        'Total Property Value':       'Total Property Value ($ billions)',
        'Total Municipal Taxes':      'Tax Revenue ($ millions)',
        'Population':                 'Population',
        'Municipal Taxes per Capita': 'Municipal Taxes per Capita',
    }
    sns.lineplot(data=df, x='Year', y=col_map[var], hue='Municipality', marker='o')