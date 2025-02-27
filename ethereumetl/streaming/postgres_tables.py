#  MIT License
#
#  Copyright (c) 2020 Evgeny Medvedev, evge.medvedev@gmail.com
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

from sqlalchemy import Table, Column, Integer, BigInteger, Boolean, String, Numeric, \
    MetaData, PrimaryKeyConstraint, VARCHAR, TIMESTAMP
from sqlalchemy.dialects.postgresql import ARRAY

metadata = MetaData()

# SQL schema is here https://github.com/blockchain-etl/ethereum-etl-postgres/tree/master/schema

BLOCKS = Table(
    'blocks', metadata,
    Column('timestamp', BigInteger),
    Column('number', BigInteger),
    Column('hash', String, primary_key=True),
    Column('parent_hash', String),
    Column('nonce', String),
    Column('sha3_uncles', String),
    Column('logs_bloom', String),
    Column('transactions_root', String),
    Column('state_root', String),
    Column('receipts_root', String),
    Column('miner', String),
    Column('difficulty', Numeric(38, 9)),
    Column('total_difficulty', Numeric(38, 9)),
    Column('size', BigInteger),
    Column('extra_data', String),
    Column('gas_limit', BigInteger),
    Column('gas_used', BigInteger),
    Column('transaction_count', BigInteger),
    Column('base_fee_per_gas', BigInteger),
)

TRANSACTIONS = Table(
    'transactions', metadata,
    Column('hash', String, primary_key=True),
    Column('nonce', BigInteger),
    Column('transaction_index', BigInteger),
    Column('from_address', String),
    Column('to_address', String),
    Column('value', Numeric(38)),
    Column('gas', BigInteger),
    Column('gas_price', BigInteger),
    Column('input', String),
    Column('receipt_cumulative_gas_used', BigInteger),
    Column('receipt_gas_used', BigInteger),
    Column('receipt_contract_address', String),
    Column('receipt_root', String),
    Column('receipt_status', BigInteger),
    Column('block_timestamp', BigInteger),
    Column('block_number', BigInteger),
    Column('block_hash', String),
    Column('max_fee_per_gas', BigInteger),
    Column('max_priority_fee_per_gas', BigInteger),
    Column('transaction_type', BigInteger),
    Column('receipt_effective_gas_price', BigInteger),
)

LOGS = Table(
    'logs', metadata,
    Column('log_index', BigInteger, primary_key=True),
    Column('transaction_hash', String, primary_key=True),
    Column('transaction_index', BigInteger),
    Column('address', String),
    Column('topics', String),
    Column('data', String),
    Column('block_timestamp', BigInteger),
    Column('block_number', BigInteger),
    Column('block_hash', String),
)

TOKEN_TRANSFERS = Table(
    'token_transfers', metadata,
    Column('token_address', String),
    Column('from_address', String),
    Column('to_address', String),
    Column('value', String),
    Column('transaction_hash', String, primary_key=True),
    Column('log_index', BigInteger, primary_key=True),
    Column('block_timestamp', BigInteger),
    Column('block_number', BigInteger),
    Column('block_hash', String),
)

TRACES = Table(
    'traces', metadata,
    Column('transaction_hash', String),
    Column('transaction_index', BigInteger),
    Column('from_address', String),
    Column('to_address', String),
    Column('value', Numeric(38)),
    Column('input', String),
    Column('output', String),
    Column('trace_type', String),
    Column('call_type', String),
    Column('reward_type', String),
    Column('gas', BigInteger),
    Column('gas_used', BigInteger),
    Column('subtraces', BigInteger),
    Column('trace_address', String),
    Column('error', String),
    Column('status', Integer),
    Column('block_timestamp', TIMESTAMP),
    Column('block_number', BigInteger),
    Column('block_hash', String),
    Column('trace_id', String, primary_key=True),
)

CONTRACT_CREATIONS = Table(
    'contract_creations', metadata,
    Column('address', String, primary_key=True),
    Column('bytecode', String),
    Column('function_sighashes', String),
    Column('is_erc20', Boolean),
    Column('is_erc721', Boolean),
    Column('block_number', BigInteger),
    Column('block_timestamp', BigInteger),
    Column('block_hash', String),
)

RECEIPTS = Table(
    'receipts', metadata,
    Column('transaction_hash', String),
    Column('transaction_index', BigInteger),
    Column('block_hash', String),
    Column('block_number', BigInteger),
    Column('cumulative_gas_used', BigInteger),
    Column('gas_used', BigInteger),
    Column('contract_address', String),
    Column('root', String),
    Column('status', BigInteger),
    Column('effective_gas_price', BigInteger),
)

TOKENS = Table(
    'tokens', metadata,
    Column('address', String, primary_key=True),
    Column('name', String),
    Column('symbol', String),
    Column('decimals', Integer),
    Column('total_supply', String),
    Column('block_number', BigInteger, info={"immutable": True}),
    Column('block_timestamp', BigInteger, info={"immutable": True}),
    Column('block_hash', String, info={"immutable": True}),
    Column('updated_block_number', BigInteger),
    Column('updated_block_timestamp', BigInteger),
    Column('updated_block_hash', String),
)
