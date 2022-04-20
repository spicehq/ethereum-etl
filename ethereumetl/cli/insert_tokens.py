import click
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert

from ethereumetl.streaming.postgres_tables import TOKENS
from blockchainetl.logging_utils import logging_basic_config

logging_basic_config()


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-t', '--token-parquet', required=True, type=str,
              help='The Parquet file containing token addresses, one per line.')
@click.option('-P', '--postgres-connection-string', default='', show_default=False, type=str, help='Postgres connection string.')
def insert_tokens_from_parquet(token_parquet, postgres_connection_string):
    """Insert ERC20/ERC721 tokens to PostgreSQL from a Parquet file."""
    token_df = pd.read_parquet(token_parquet)

    token_df["block_timestamp"] = (token_df["block_timestamp"].astype(int) / 1e9).astype(int)

    engine = create_engine(postgres_connection_string,
                               echo=True, pool_recycle=3600)
    connection = engine.connect()

    insert_stmt = insert(TOKENS)

    insert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["address"],
        set_={
            "block_number": insert_stmt.excluded["block_number"],
            "block_timestamp": insert_stmt.excluded["block_timestamp"],
            "block_hash": insert_stmt.excluded["block_hash"]
        }
    )

    connection.execute(insert_stmt, token_df.to_dict('records'))