# MIT License
#
# Copyright (c) 2018 Evgeny Medvedev, evge.medvedev@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import csv
import logging
import os
import shutil
from time import time

from requests import HTTPError

from blockchainetl.jobs.exporters.in_memory_item_exporter import InMemoryItemExporter
from blockchainetl.jobs.exporters.postgres_item_exporter import PostgresItemExporter
from blockchainetl.file_utils import smart_open
from blockchainetl.jobs.exporters.multi_item_exporter import MultiItemExporter
from blockchainetl.streaming.postgres_utils import create_insert_statement_for_table
from ethereumetl.csv_utils import set_max_field_size_limit
from ethereumetl.jobs.export_blocks_job import ExportBlocksJob
from ethereumetl.jobs.export_geth_traces_job import ExportGethTracesJob
from ethereumetl.jobs.export_receipts_job import ExportReceiptsJob
from ethereumetl.jobs.export_token_transfers_job import ExportTokenTransfersJob
from ethereumetl.jobs.export_tokens_job import ExportTokensJob
from ethereumetl.jobs.export_contracts_job import ExportContractsJob
from ethereumetl.jobs.exporters.blocks_and_transactions_item_exporter import blocks_and_transactions_item_exporter
from ethereumetl.jobs.exporters.contracts_item_exporter import contracts_item_exporter
from ethereumetl.jobs.exporters.receipts_and_logs_item_exporter import receipts_and_logs_item_exporter
from ethereumetl.jobs.exporters.token_transfers_item_exporter import token_transfers_item_exporter
from ethereumetl.jobs.exporters.tokens_item_exporter import tokens_item_exporter
from ethereumetl.jobs.extract_contracts_job import ExtractContractsJob
from ethereumetl.providers.auto import get_provider_from_uri
from ethereumetl.streaming.enrich import enrich_contracts, enrich_logs, enrich_tokens
from ethereumetl.streaming.postgres_tables import BLOCKS, TRANSACTIONS, LOGS, TOKEN_TRANSFERS, CONTRACT_CREATIONS, TOKENS
from ethereumetl.thread_local_proxy import ThreadLocalProxy
from ethereumetl.web3_utils import build_web3
from ethereumetl.misc.historical_stata_unavailable_error import HistoricalStateUnavailableError


logger = logging.getLogger('export_all')


def is_log_filter_supported(provider_uri):
    return 'infura' not in provider_uri


def extract_csv_column_unique(input_path, output, column, other_columns = None):
    set_max_field_size_limit()
    with smart_open(input_path, 'r') as input_file, smart_open(output, 'w') as output_file:
        reader = csv.DictReader(input_file)
        seen = set()  # set for fast O(1) amortized lookup
        for row in reader:
            if row[column] in seen:
                continue
            seen.add(row[column])

            output = row[column]
            if other_columns:
                for other_column in other_columns:
                    output = output + "," + row[other_column]
            output_file.write(output + '\n')


def get_multi_item_exporter(item_exporters: list):
    valid_item_exporters = []

    for item_exporter in item_exporters:
        if item_exporter is not None:
            valid_item_exporters.append(item_exporter)

    return MultiItemExporter(valid_item_exporters)


def export_all_common(partitions, output_dir, postgres_connection_string, provider_uri, max_workers, batch_size, skip_geth_traces):

    for batch_start_block, batch_end_block, partition_dir in partitions:
        # # # start # # #

        start_time = time()

        padded_batch_start_block = str(batch_start_block).zfill(8)
        padded_batch_end_block = str(batch_end_block).zfill(8)
        block_range = '{padded_batch_start_block}-{padded_batch_end_block}'.format(
            padded_batch_start_block=padded_batch_start_block,
            padded_batch_end_block=padded_batch_end_block,
        )
        file_name_suffix = '{padded_batch_start_block}_{padded_batch_end_block}'.format(
            padded_batch_start_block=padded_batch_start_block,
            padded_batch_end_block=padded_batch_end_block,
        )

        # # # blocks_and_transactions # # #

        blocks_output_dir = '{output_dir}/blocks{partition_dir}'.format(
            output_dir=output_dir,
            partition_dir=partition_dir,
        )
        os.makedirs(os.path.dirname(blocks_output_dir), exist_ok=True)

        transactions_output_dir = '{output_dir}/transactions{partition_dir}'.format(
            output_dir=output_dir,
            partition_dir=partition_dir,
        )
        os.makedirs(os.path.dirname(transactions_output_dir), exist_ok=True)

        blocks_file = '{blocks_output_dir}/blocks_{file_name_suffix}.csv'.format(
            blocks_output_dir=blocks_output_dir,
            file_name_suffix=file_name_suffix,
        )
        transactions_file = '{transactions_output_dir}/transactions_{file_name_suffix}.csv'.format(
            transactions_output_dir=transactions_output_dir,
            file_name_suffix=file_name_suffix,
        )
        logger.info('Exporting blocks {block_range} to {blocks_file}'.format(
            block_range=block_range,
            blocks_file=blocks_file,
        ))
        logger.info('Exporting transactions from blocks {block_range} to {transactions_file}'.format(
            block_range=block_range,
            transactions_file=transactions_file,
        ))

        blocks_and_transactions_file_exporter = blocks_and_transactions_item_exporter(
            blocks_file, transactions_file)

        postgres_exporter = None
        if postgres_connection_string:
            postgres_exporter = PostgresItemExporter(
                postgres_connection_string, item_type_to_insert_stmt_mapping={
                    'block': create_insert_statement_for_table(BLOCKS),
                    'transaction': create_insert_statement_for_table(TRANSACTIONS),
                    'log': create_insert_statement_for_table(LOGS),
                    'token_transfer': create_insert_statement_for_table(TOKEN_TRANSFERS),
                    'contract': create_insert_statement_for_table(CONTRACT_CREATIONS),
                },
            )

        inmemory_exporter = InMemoryItemExporter(item_types=[
            'block', 'transaction', 'log', 'token_transfer', 'contract', 'receipt', 'geth_trace'])

        job = ExportBlocksJob(
            start_block=batch_start_block,
            end_block=batch_end_block,
            batch_size=batch_size,
            batch_web3_provider=ThreadLocalProxy(
                lambda: get_provider_from_uri(provider_uri, batch=True)),
            max_workers=max_workers,
            item_exporter=inmemory_exporter,
            export_blocks=blocks_file is not None,
            export_transactions=transactions_file is not None)
        job.run()
        blocks = inmemory_exporter.get_items('block')
        transactions = inmemory_exporter.get_items('transaction')
        # transactions = enrich_transactions(blocks, transactions)
        blocks_and_transactions_exporters = get_multi_item_exporter(
            [blocks_and_transactions_file_exporter, postgres_exporter])
        blocks_and_transactions_exporters.open()
        blocks_and_transactions_exporters.export_items(blocks)
        blocks_and_transactions_exporters.export_items(transactions)
        blocks_and_transactions_exporters.close()

        # # # token_transfers # # #

        token_transfers_file = None
        if is_log_filter_supported(provider_uri):
            token_transfers_output_dir = '{output_dir}/token_transfers{partition_dir}'.format(
                output_dir=output_dir,
                partition_dir=partition_dir,
            )
            os.makedirs(os.path.dirname(
                token_transfers_output_dir), exist_ok=True)

            token_transfers_file = '{token_transfers_output_dir}/token_transfers_{file_name_suffix}.csv'.format(
                token_transfers_output_dir=token_transfers_output_dir,
                file_name_suffix=file_name_suffix,
            )
            logger.info('Exporting ERC20 transfers from blocks {block_range} to {token_transfers_file}'.format(
                block_range=block_range,
                token_transfers_file=token_transfers_file,
            ))

            token_transfers_file_exporter = token_transfers_item_exporter(
                token_transfers_file)

            job = ExportTokenTransfersJob(
                start_block=batch_start_block,
                end_block=batch_end_block,
                batch_size=batch_size,
                web3=ThreadLocalProxy(lambda: build_web3(
                    get_provider_from_uri(provider_uri))),
                item_exporter=inmemory_exporter,
                max_workers=max_workers)
            job.run()
            token_transfers = inmemory_exporter.get_items('token_transfer')
            # token_transfers = enrich_token_transfers(blocks, token_transfers)
            token_transfers_exporters = get_multi_item_exporter(
                [token_transfers_file_exporter, postgres_exporter])
            token_transfers_exporters.open()
            token_transfers_exporters.export_items(token_transfers)
            token_transfers_exporters.close()

        # # # receipts_and_logs # # #

        cache_output_dir = '{output_dir}/.tmp{partition_dir}'.format(
            output_dir=output_dir,
            partition_dir=partition_dir,
        )
        os.makedirs(os.path.dirname(cache_output_dir), exist_ok=True)

        transaction_hashes_file = '{cache_output_dir}/transaction_hashes_{file_name_suffix}.csv'.format(
            cache_output_dir=cache_output_dir,
            file_name_suffix=file_name_suffix,
        )
        logger.info('Extracting hash column from transaction file {transactions_file}'.format(
            transactions_file=transactions_file,
        ))
        extract_csv_column_unique(
            transactions_file, transaction_hashes_file, 'hash')

        receipts_output_dir = '{output_dir}/receipts{partition_dir}'.format(
            output_dir=output_dir,
            partition_dir=partition_dir,
        )
        os.makedirs(os.path.dirname(receipts_output_dir), exist_ok=True)

        logs_output_dir = '{output_dir}/logs{partition_dir}'.format(
            output_dir=output_dir,
            partition_dir=partition_dir,
        )
        os.makedirs(os.path.dirname(logs_output_dir), exist_ok=True)

        receipts_file = '{receipts_output_dir}/receipts_{file_name_suffix}.csv'.format(
            receipts_output_dir=receipts_output_dir,
            file_name_suffix=file_name_suffix,
        )
        logs_file = '{logs_output_dir}/logs_{file_name_suffix}.csv'.format(
            logs_output_dir=logs_output_dir,
            file_name_suffix=file_name_suffix,
        )
        logger.info('Exporting receipts and logs from blocks {block_range} to {receipts_file} and {logs_file}'.format(
            block_range=block_range,
            receipts_file=receipts_file,
            logs_file=logs_file,
        ))

        with smart_open(transaction_hashes_file, 'r') as transaction_hashes:

            receipts_and_logs_file_exporter = receipts_and_logs_item_exporter(
                receipts_file, logs_file)

            job = ExportReceiptsJob(
                transaction_hashes_iterable=(
                    transaction_hash.strip() for transaction_hash in transaction_hashes),
                batch_size=batch_size,
                batch_web3_provider=ThreadLocalProxy(
                    lambda: get_provider_from_uri(provider_uri, batch=True)),
                max_workers=max_workers,
                item_exporter=inmemory_exporter,
                export_receipts=receipts_file is not None,
                export_logs=logs_file is not None)
            job.run()
            logs = inmemory_exporter.get_items('log')

            logs = enrich_logs(blocks, logs)
            receipts_and_logs_exporters = get_multi_item_exporter(
                [receipts_and_logs_file_exporter, postgres_exporter])
            receipts_and_logs_exporters.open()
            receipts_and_logs_exporters.export_items(
                inmemory_exporter.get_items('receipt'))
            receipts_and_logs_exporters.export_items(logs)
            receipts_and_logs_exporters.close()

        # # # geth traces # # #

        geth_traces_available = False
        if not skip_geth_traces:
            logger.info('Exporting geth traces from blocks {block_range}'.format(
                block_range=block_range
            ))

            geth_traces_available = True
            job = ExportGethTracesJob(
                start_block=batch_start_block,
                end_block=batch_end_block,
                batch_size=batch_size,
                batch_web3_provider=ThreadLocalProxy(
                        lambda: get_provider_from_uri(provider_uri, batch=True)),
                max_workers=max_workers,
                item_exporter=inmemory_exporter
            )
            try:
                job.run()
            except HistoricalStateUnavailableError:
                geth_traces_available = False
            except HTTPError:
                geth_traces_available = False

        contracts_output_dir = '{output_dir}/contracts{partition_dir}'.format(
            output_dir=output_dir,
            partition_dir=partition_dir,
        )
        os.makedirs(os.path.dirname(contracts_output_dir), exist_ok=True)

        contracts_file = '{contracts_output_dir}/contracts_{file_name_suffix}.csv'.format(
            contracts_output_dir=contracts_output_dir,
            file_name_suffix=file_name_suffix,
        )
        logger.info('Exporting contracts from blocks {block_range} to {contracts_file}'.format(
            block_range=block_range,
            contracts_file=contracts_file,
        ))

        if geth_traces_available:
            # # # contracts (geth traces) # # #
            contracts_file_exporter = contracts_item_exporter(contracts_file)

            geth_traces = inmemory_exporter.get_items('geth_trace')

            job = ExtractContractsJob(
                traces_iterable=geth_traces,
                batch_size=batch_size,
                item_exporter=inmemory_exporter,
                max_workers=max_workers)
            job.run()
            contracts = inmemory_exporter.get_items('contract')
            contracts = enrich_contracts(blocks, contracts)
            contracts_exporters = get_multi_item_exporter(
                [contracts_file_exporter, postgres_exporter])
            contracts_exporters.open()
            contracts_exporters.export_items(contracts)
            contracts_exporters.close()

        else:
            # # # contracts (no-geth traces) # # #
            contract_addresses_file = '{cache_output_dir}/contract_addresses_{file_name_suffix}.csv'.format(
                cache_output_dir=cache_output_dir,
                file_name_suffix=file_name_suffix,
            )
            logger.info('Extracting contract_address from receipt file {receipts_file}'.format(
                receipts_file=receipts_file
            ))
            extract_csv_column_unique(
                receipts_file, contract_addresses_file, 'contract_address')

            with smart_open(contract_addresses_file, 'r') as contract_addresses_file:
                contracts_file_exporter = contracts_item_exporter(contracts_file)

                contract_addresses = (contract_address.strip() for contract_address in contract_addresses_file
                                    if contract_address.strip())

                job = ExportContractsJob(
                    contract_addresses_iterable=contract_addresses,
                    batch_size=batch_size,
                    batch_web3_provider=ThreadLocalProxy(
                        lambda: get_provider_from_uri(provider_uri, batch=True)),
                    item_exporter=inmemory_exporter,
                    max_workers=max_workers)
                job.run()
                contracts = inmemory_exporter.get_items('contract')
                for contract in contracts:
                    contract_block_number = next((transaction["block_number"]
                                                for transaction in transactions if transaction["receipt_contract_address"] == contract["address"]))
                    contract['block_number'] = contract_block_number
                contracts = enrich_contracts(blocks, contracts)
                contracts_exporters = get_multi_item_exporter(
                    [contracts_file_exporter, postgres_exporter])
                contracts_exporters.open()
                contracts_exporters.export_items(contracts)
                contracts_exporters.close()

        inmemory_exporter.close()

        # # # finish # # #
        shutil.rmtree(os.path.dirname(cache_output_dir), ignore_errors=True)
        end_time = time()
        time_diff = round(end_time - start_time, 5)
        logger.info('Exporting blocks {block_range} took {time_diff} seconds'.format(
            block_range=block_range,
            time_diff=time_diff,
        ))
