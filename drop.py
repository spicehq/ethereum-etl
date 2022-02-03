from operator import index
import pandas as pd

import click


@click.group()
@click.version_option(version='1.10.0-spicehq/release/v1')
@click.pass_context
def cli(ctx):
    pass

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-f', '--filename', required=True, type=str, help='Filename to the csv file')
@click.option('-c', '--column-to-drop', required=True, type=str, help='The column to drop')
def transform_csv(filename, column_to_drop):

  # read_csv function which is used to read the required CSV file
  data = pd.read_csv(filename)

  # drop function which is used in removing or deleting rows or columns from the CSV files
  data.drop(column_to_drop, inplace=True, axis=1)
    
  data.to_csv(filename, index=False)

def drop_index(filename):
  data = pd.read_csv(filename, index_col=0)
  data.to_csv(filename, index=False)

cli.add_command(transform_csv, "transform_csv")

cli()