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


from ethereumetl.domain.transaction import EthTransaction
from ethereumetl.utils import hex_to_dec, to_normalized_address


class EthTransactionMapper:
    @staticmethod
    def json_dict_to_transaction(json_dict, **kwargs):
        transaction = EthTransaction()
        transaction.hash = json_dict.get('hash')
        transaction.nonce = hex_to_dec(json_dict.get('nonce'))
        transaction.transaction_index = hex_to_dec(json_dict.get('transactionIndex'))
        transaction.from_address = to_normalized_address(json_dict.get('from'))
        transaction.to_address = to_normalized_address(json_dict.get('to'))
        transaction.value = hex_to_dec(json_dict.get('value'))
        transaction.gas = hex_to_dec(json_dict.get('gas'))
        transaction.gas_price = hex_to_dec(json_dict.get('gasPrice'))
        transaction.input = json_dict.get('input')
        transaction.block_timestamp = kwargs.get('block_timestamp')
        transaction.block_number = hex_to_dec(json_dict.get('blockNumber'))
        transaction.block_hash = json_dict.get('blockHash')
        transaction.max_fee_per_gas = hex_to_dec(json_dict.get('maxFeePerGas'))
        transaction.max_priority_fee_per_gas = hex_to_dec(json_dict.get('maxPriorityFeePerGas'))
        transaction.transaction_type = hex_to_dec(json_dict.get('type'))
        if 'receipt' in json_dict:
            receipt_dict = json_dict.get('receipt')
            transaction.receipt_cumulative_gas_used = hex_to_dec(receipt_dict.get('cumulativeGasUsed'))
            transaction.receipt_gas_used = hex_to_dec(receipt_dict.get('gasUsed'))
            transaction.receipt_contract_address = to_normalized_address(receipt_dict.get('contractAddress'))
            transaction.receipt_root = receipt_dict.get('root')
            transaction.receipt_status = hex_to_dec(receipt_dict.get('status'))
            transaction.receipt_effective_gas_price = hex_to_dec(receipt_dict.get('effectiveGasPrice'))
        return transaction

    @staticmethod
    def transaction_to_dict(transaction: EthTransaction):
        return {
            'type': 'transaction',
            'hash': transaction.hash,
            'nonce': transaction.nonce,
            'transaction_index': transaction.transaction_index,
            'from_address': transaction.from_address,
            'to_address': transaction.to_address,
            'value': transaction.value,
            'gas': transaction.gas,
            'gas_price': transaction.gas_price,
            'input': transaction.input,
            'receipt_cumulative_gas_used': transaction.receipt_cumulative_gas_used,
            'receipt_gas_used': transaction.receipt_gas_used,
            'receipt_contract_address': transaction.receipt_contract_address,
            'receipt_root': transaction.receipt_root,
            'receipt_status': transaction.receipt_status,
            'receipt_effective_gas_price': transaction.receipt_effective_gas_price,
            'block_timestamp': transaction.block_timestamp,
            'block_number': transaction.block_number,
            'block_hash': transaction.block_hash,
            'max_fee_per_gas': transaction.max_fee_per_gas,
            'max_priority_fee_per_gas': transaction.max_priority_fee_per_gas,
            'transaction_type': transaction.transaction_type
        }
