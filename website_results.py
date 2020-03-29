import papermill as pm

datestamp = '20200329'

ma_runs = [
    {
        'state_code': 'MA',
        'results_label': f'{datestamp}_euclidean',
        'ed_inst_max_utilization_pct': util
    } for util in (0.2, 0.3, 0.4, 0.5)
]
other_runs = [
    {
        'state_code': code,
        'results_label': f'{datestamp}_travel_time',
        'ed_inst_max_utilization_pct': 0.4
    } for code in ('NY', 'MI')
]
runs = ma_runs + other_runs

if __name__ == '__main__':
    for run in runs:
        pm.execute_notebook(
            'University-hospital bed assignment.ipynb',
            'results.ipynb',
            parameters=run
    )
