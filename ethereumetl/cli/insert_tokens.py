import click
import pandas as pd

from blockchainetl.logging_utils import logging_basic_config

logging_basic_config()


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-t', '--token-parquet', required=True, type=str,
              help='The Parquet file containing token addresses, one per line.')
@click.option('-P', '--postgres-connection-string', default='', show_default=False, type=str, help='Postgres connection string.')
def insert_tokens_from_parquet(token_parquet, postgres_connection_string):
    """Insert ERC20/ERC721 tokens to PostgreSQL from a Parquet file."""
    token_df = pd.read_parquet(token_parquet)

    print(token_df)