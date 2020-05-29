"""Common configurations and utility functions for data loading scripts."""
import os
import pathlib

# USA Contiguous Albers Equal Area Conic
PROJ = 'esri:102003'

def path(dataset):
    """Gets the full absolute path of a dataset."""
    return os.path.join(
        pathlib.Path(__file__).parent.absolute(),
        'data',
        dataset
    )
