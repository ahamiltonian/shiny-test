import json
import pandas as pd
import seaborn as sns
from pathlib import Path

sns.set_theme(style="whitegrid")


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_municipal_data(path: str | Path = 'data/municipal_data.json') -> pd.DataFrame:
    """Load municipal_data.json into a flat DataFrame.

    Top-level scalar fields become columns directly.
    Nested Property Classes are flattened to columns like:
        'Residential Tax Rate', 'Residential Taxable Value', 'Residential Tax Multiple', ...
    """
    with open(path) as f:
        records = json.load(f)

    rows = []
    for r in records:
        row = {
            'Year':                             r['Year'],
            'Municipality':                     r['Municipality'],
            'Population':                       r.get('Population'),
            'Total Taxable Value':              r.get('Total Taxable Value'),
            'Total Taxes Collected':            r.get('Total Taxes Collected'),
            'Tax per Capita':                   r.get('Tax per Capita'),
            'House Value':                      r.get('House Value'),
            'Total Variable Rate Taxes':        r.get('Total Variable Rate Taxes'),
            'Total Property Taxes and Charges': r.get('Total Property Taxes and Charges'),
        }
        for cls, vals in (r.get('Property Classes') or {}).items():
            if vals is None:
                continue
            row[f'{cls} Taxable Value'] = vals.get('Taxable Value')
            row[f'{cls} Tax Rate']      = vals.get('Tax Rate')
            row[f'{cls} Tax Multiple']  = vals.get('Tax Multiple')
        rows.append(row)

    df = pd.DataFrame(rows)
    df['Year'] = df['Year'].astype(int)
    return df


plot_df = load_municipal_data()

# ---------------------------------------------------------------------------
# Column groups exposed to plot_data
# ---------------------------------------------------------------------------

# Human-readable label -> actual column name
PLOT_VARIABLES: dict[str, str] = {
    # --- Overview ---
    'Population':                          'Population',
    'Total Taxable Value':                 'Total Taxable Value',
    'Total Taxes Collected':               'Total Taxes Collected',
    'Tax per Capita':                      'Tax per Capita',
    'House Value':                         'House Value',
    'Total Variable Rate Taxes':           'Total Variable Rate Taxes',
    'Total Property Taxes and Charges':    'Total Property Taxes and Charges',
    # --- Property class tax rates ---
    'Residential Tax Rate':                'Residential Tax Rate',
    'Utilities Tax Rate':                  'Utilities Tax Rate',
    'Major Industry Tax Rate':             'Major Industry Tax Rate',
    'Light Industry Tax Rate':             'Light Industry Tax Rate',
    'Business/Other Tax Rate':             'Business/Other Tax Rate',
    'Managed Forest Tax Rate':             'Managed Forest Tax Rate',
    'Recreation Tax Rate':                 'Recreation Tax Rate',
    'Farm Tax Rate':                       'Farm Tax Rate',
    # --- Property class taxable values ---
    'Residential Taxable Value':           'Residential Taxable Value',
    'Utilities Taxable Value':             'Utilities Taxable Value',
    'Major Industry Taxable Value':        'Major Industry Taxable Value',
    'Light Industry Taxable Value':        'Light Industry Taxable Value',
    'Business/Other Taxable Value':        'Business/Other Taxable Value',
    'Managed Forest Taxable Value':        'Managed Forest Taxable Value',
    'Recreation Taxable Value':            'Recreation Taxable Value',
    'Farm Taxable Value':                  'Farm Taxable Value',
    # --- Property class tax multiples ---
    'Residential Tax Multiple':            'Residential Tax Multiple',
    'Utilities Tax Multiple':              'Utilities Tax Multiple',
    'Major Industry Tax Multiple':         'Major Industry Tax Multiple',
    'Light Industry Tax Multiple':         'Light Industry Tax Multiple',
    'Business/Other Tax Multiple':         'Business/Other Tax Multiple',
    'Managed Forest Tax Multiple':         'Managed Forest Tax Multiple',
    'Recreation Tax Multiple':             'Recreation Tax Multiple',
    'Farm Tax Multiple':                   'Farm Tax Multiple',
}


# ---------------------------------------------------------------------------
# Plot function
# ---------------------------------------------------------------------------

def plot_data(var: str, municipalities: str | list[str]) -> None:
    """Plot a variable over time for one or more municipalities."""
    if isinstance(municipalities, str):
        municipalities = [municipalities]

    if var not in PLOT_VARIABLES:
        raise ValueError(
            f"Unknown variable '{var}'. Choose from:\n  " +
            "\n  ".join(PLOT_VARIABLES)
        )

    col = PLOT_VARIABLES[var]
    df  = plot_df[plot_df['Municipality'].isin(municipalities)][['Year', 'Municipality', col]].dropna()

    sns.lineplot(data=df, x='Year', y=col, hue='Municipality', marker='o')