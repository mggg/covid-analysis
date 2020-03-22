import os
import click
import pandas as pd
from universities import preprocess_universities
from scorecards import preprocess_scorecards

dir_path = os.path.dirname(os.path.realpath(__file__))

@click.option('--universities-file', required=True,
            default=os.path.join(dir_path, 'data', 'ma_dorm_capacity.csv'))
@click.option('--scorecards-dir', required=True,
              default=os.path.join(dir_path, 'data', 'HarvardGlobalHealth'))
@click.option('--min-dorm-beds', type=float, default=0)
@click.option('--min-endowment', type=float, default=0)
def main(universities_file, scorecards_dir, min_dorm_beds, min_endowment):
    universities_df = preprocess_universities(universities_file, min_endowment, min_dorm_beds)