from pathlib import Path
import pandas as pd
import os
from pathlib import Path
import shutil

import click


@click.command()
@click.version_option(version='0.1.0-compactor')
@click.option('-s', '--start-block', required=True, type=int)
@click.option('-e', '--end-block', required=True, type=int)
@click.option('-o', '--output-dir', required=True, type=Path)
def compact(start_block, end_block, output_dir):
    dirs_to_remove = []
    os.stat(output_dir)


compact()
