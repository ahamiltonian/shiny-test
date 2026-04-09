"""  
Extract data from BC Municipal Tax Rates and Tax Burden Schedules 704 and 707 
available at: 
https://www2.gov.bc.ca/gov/content/governments/local-governments/facts-framework/statistics/tax-rates-tax-burden

Fields extracted:
  From Schedule 707 (Totals row):
    - Population
    - Total Taxable Value
    - Total Taxes Collected
    - Tax per Capita

  From Schedule 707 (per Property Class row):
    - Taxable Value
    - Tax Rate
    - Tax Class Multiple

  From Schedule 707 (per Property Class, nested under 'Property Classes'):

  From Schedule 704 (municipality row):
    - House Value
    - Total Variable Rate Taxes
    - Total Property Taxes and Charges
"""

import json
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MUNICIPALITIES = ['Squamish', 'Whistler', 'Pemberton']
START_YEAR = 2005
END_YEAR = 2025
DATA_DIR = Path('data')
RAW_DATA_DIR = DATA_DIR / 'raw/'
OUTPUT_FILE = DATA_DIR / 'municipal_data.json'

# Property classes to extract per-class data for (excludes Totals and Supportive Housing)
PROPERTY_CLASSES = [
    'Residential',
    'Utilities',
    'Major Industry',
    'Light Industry',
    'Business/Other',
    'Managed Forest',
    'Recreation',
    'Farm',
]


# ---------------------------------------------------------------------------
# Schedule 707 helpers
# ---------------------------------------------------------------------------

def scrape_707(year: int, municipalities: list[str]) -> dict:
    """Return a dict of {municipality: dict} with Totals-row and per-class fields from Schedule 707.

    Schedule 707 column positions (0-indexed, consistent across all years):
      0  - Municipality name (label varies: 'Municipality', 'Municipalities', etc.)
      3  - Population (label varies by year)
      4  - Property Class
      5  - Authenticated Roll General Taxable Values
      6  - Municipal Purposes Tax Rates
      7  - Tax Class Multiples
      10 - Total Municipal Taxes
      13 - Municipal Taxes Per Capita

    Note: 2005 and 2006 files have only one row per municipality (Residential only, no Totals row).
    In that case, aggregate values are read directly from that single row.
    """
    path = RAW_DATA_DIR / (f'schedule707_{year}.xlsx' if year > 2019 else f'schedule707_{year}.xls')

    # Read by column index to avoid year-varying header names
    df = pd.read_excel(path, header=1, usecols=[0, 3, 4, 5, 6, 7, 10, 13])

    # Forward-fill the municipality column — older files only populate it on the
    # first (Residential) row; subsequent property class rows are blank.
    df.iloc[:, 0] = df.iloc[:, 0].ffill()

    # Normalise column names
    cols = df.columns.tolist()
    muni_col       = cols[0]   # 'Municipality', 'Municipalities', 'Municipalities1', etc.
    pop_col        = cols[1]   # 'July 1, 20XX BC STATS Population Estimates...'
    prop_class_col = cols[2]   # 'Property Class'

    df.rename(columns={
        muni_col: 'Municipality',
        pop_col:  'Population',
        cols[3]:  'Taxable Value',
        cols[4]:  'Tax Rate',
        cols[5]:  'Tax Class Multiple',
        cols[6]:  'Total Taxes Collected',
        cols[7]:  'Tax per Capita',
    }, inplace=True)

    result = {}
    for muni in municipalities:
        muni_df = df[df['Municipality'] == muni].copy()
        if muni_df.empty:
            continue
        muni_df.set_index(prop_class_col, inplace=True)

        # Normalise index labels that vary across years
        muni_df.rename(index={'Business': 'Business/Other'}, inplace=True)

        # --- Totals row (aggregate fields) ---
        if 'Totals' in muni_df.index:
            totals = muni_df.loc['Totals']
        else:
            totals = muni_df.iloc[0]

        # Population is on the Residential row in older files, not the Totals row
        population = _val(totals.get('Population'))
        if population is None and 'Residential' in muni_df.index:
            population = _val(muni_df.loc['Residential'].get('Population'))

        row = {
            'Population':            population,
            'Total Taxable Value':   _val(totals.get('Taxable Value')),
            'Total Taxes Collected': _val(totals.get('Total Taxes Collected')),
            'Tax per Capita':        _val(totals.get('Tax per Capita')),
        }

        # --- Per-class fields — stored as a nested object ---
        property_classes = {}
        for prop_class in PROPERTY_CLASSES:
            if prop_class in muni_df.index:
                class_row = muni_df.loc[prop_class]
                property_classes[prop_class] = {
                    'Taxable Value':    _val(class_row.get('Taxable Value')),
                    'Tax Rate':         _val(class_row.get('Tax Rate')),
                    'Tax Multiple':     _val(class_row.get('Tax Class Multiple')),
                }
            else:
                property_classes[prop_class] = None

        row['Property Classes'] = property_classes
        result[muni] = row

    return result


# ---------------------------------------------------------------------------
# Schedule 704 helpers
# ---------------------------------------------------------------------------

def scrape_704(year: int, municipalities: list[str]) -> dict:
    """Return a dict of {municipality: dict} with representative house fields from Schedule 704.

    Schedule 704 column layout:
      0  - Municipalities
      3  - House Value
      9  - Total Res Variable Rate Taxes
      12 - Total Residential Property Taxes and Charges
    """
    path = RAW_DATA_DIR / (f'schedule704_{year}.xlsx' if year > 2019 else f'schedule704_{year}.xls')

    df = pd.read_excel(path, header=1, usecols=[0, 3, 9, 12])

    cols = df.columns.tolist()
    df.rename(columns={
        cols[0]: 'Municipality',
        cols[1]: 'House Value',
        cols[2]: 'Total Variable Rate Taxes',
        cols[3]: 'Total Property Taxes and Charges',
    }, inplace=True)

    result = {}
    for muni in municipalities:
        row = df[df['Municipality'] == muni]
        if row.empty:
            continue
        row = row.iloc[0]
        result[muni] = {
            'House Value':                      _val(row.get('House Value')),
            'Total Variable Rate Taxes':        _val(row.get('Total Variable Rate Taxes')),
            'Total Property Taxes and Charges': _val(row.get('Total Property Taxes and Charges')),
        }

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _val(v):
    """Convert numpy scalars and NaN to plain Python types for JSON serialisation."""
    if v is None:
        return None
    try:
        import math
        if math.isnan(float(v)):
            return None
    except (TypeError, ValueError):
        pass
    # Convert numpy scalar to native Python type
    return v.item() if hasattr(v, 'item') else v


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_dataset(municipalities: list[str] = MUNICIPALITIES,
                  start: int = START_YEAR,
                  end: int = END_YEAR) -> list[dict]:

    records = []

    for year in range(start, end + 1):
        print(f'Processing year {year}...')

        # Schedule 707
        try:
            data_707 = scrape_707(year, municipalities)
        except FileNotFoundError:
            print(f'  Schedule 707 not found for {year}, skipping.')
            data_707 = {}

        # Schedule 704
        try:
            data_704 = scrape_704(year, municipalities)
        except FileNotFoundError:
            print(f'  Schedule 704 not found for {year}, skipping.')
            data_704 = {}

        for muni in municipalities:
            record = {'Year': year, 'Municipality': muni}
            record.update(data_707.get(muni, {}))
            record.update(data_704.get(muni, {}))
            records.append(record)

    return records


if __name__ == '__main__':
    records = build_dataset()
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(records, f, indent=2)
    print(f'\nSaved {len(records)} records to {OUTPUT_FILE}')
