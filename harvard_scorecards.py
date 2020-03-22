import os
import pandas as pd

HARVARD_SCORECARD_REPLACE = {
    'HRR': 'hrr',
    'Adult Population': 'adult_pop',
    'Population 65+': 'senior_pop',
    'Total Hospital Beds': 'total_hosp_beds',
    'Total ICU Beds': 'total_icu_beds',
    'Available Hospital Beds': 'avail_hosp_beds',
    'Available ICU Beds': 'avail_icu_beds',
    'Hospital Beds Needed': 'needed_hosp_beds',
    'ICU Beds Needed': 'needed_icu_beds',
    ', ': '_',
    'Six Months': '6mo',
    'Twelve Months': '12mo',
    'Eighteen Months': '18mo'
}
TIME_SCALES = ['6mo', '12mo', '18mo']

def load_harvard_scenarios(scorecards_dir: str,
                          state_code: str = 'MA'):
    """Loads scenarios from Harvard Global Health scenario scorecards.

    Expected filenames: hrr_scorecard_<percent of population>.csv
    """
    # Load scorecards.
    states = {}
    for filename in os.listdir(scorecards_dir):
        if filename.startswith('hrr_scorecard_') and filename.endswith('.csv'):
            pop_percent = filename.replace('hrr_scorecard_', '').replace('.csv', '')
            df = pd.read_csv(os.path.join(scorecards_dir, filename))
            if '*Based on a 50% reduction in occupancy' in df.iloc[-1]['HRR']:
                df = df.drop([len(df) - 1, len(df) - 2])
            state = df[df['HRR'].str.contains(f', {state_code}')]
            drop_cols = [col for col in state.columns
                         if 'Percentage of' in col or
                            'Potentially' in col or
                            'Projected' in col
                        ]
            state = state.drop(columns=drop_cols)
            
            for col in state.columns:
                if col != 'HRR':
                    state[col] = state[col].astype(str) \
                                           .str.replace(',', '').astype(float)
            
            fixed_cols = {}
            for col in state.columns:
                fixed_col = col
                for find, replace in HARVARD_SCORECARD_REPLACE.items():
                    fixed_col = fixed_col.replace(find, replace)
                fixed_cols[col] = fixed_col
            state = state.rename(columns=fixed_cols)
            state['normal_hosp_util'] = 1 - (state['avail_hosp_beds'] / state['total_hosp_beds'])
            state['normal_icu_util'] = 1 - (state['avail_icu_beds'] / state['total_icu_beds'])
            states[pop_percent] = state

    # Split scorecards into scenarios based on time scale.
    state_scenarios = {}
    for pop_percent, state in states.items():
        for outer_ts in TIME_SCALES:
            df = state.copy()
            drop_cols = []
            fixed_cols = {}
            for col in df.columns:
                for inner_ts in TIME_SCALES:
                    if inner_ts != outer_ts and inner_ts in col:
                        # Column from different scenario -- remove.
                        drop_cols.append(col)
                    elif inner_ts == outer_ts:
                        # Column from current scenario -- normalize.
                        fixed_cols[col] = col.replace(f'_{outer_ts}', '')
            df = df.drop(columns=drop_cols).rename(columns=fixed_cols)
            state_scenarios[f'{pop_percent}_infected_{outer_ts}'] = df
    return state_scenarios