"""
Does the work of taking commands from the interface and translating them into DatabaseManager functions.
"""
import pandas as pd

from Database.DatabaseManager import DatabaseManager


class ParseData:
    """
    Takes MoneyEnvelope operations and forms them into DatabaseManager commands.
    """

    def __init__(self, db_filename=None):
        self._db = DatabaseManager(db_filename)

    def get_accounts_list(self):
        """
        Gets information for all the existing bank accounts in the database: name, number, bank_id

        :return: List of info for all accounts
        :rtype: list
        """
        return self._db.get_all_accounts()

    def get_accounts_summary_list(self):
        """
        Returns summary information about accounts and their transactions

        Summary data for an account is a tuple:
          - account name,
          - number of transactions,
          - balance,
          - date of earliest transaction,
          - date of most recent transaction

        :return:
        :rtype: list
        """
        accounts = self._db.get_all_accounts()
        summary_list = []
        for account in accounts:
            name = account[1]
            num_trans, balance, earliest_trans, latest_trans = self._db.get_account_summary(account[0])
            summary_list.append((name, balance, num_trans, earliest_trans, latest_trans))
        return summary_list

    def create_new_account(self, institution_number, bank_name, transit_number, account_number, account_name):
        """

        :param institution_number: Identification number of the bank
        :type institution_number: str
        :param bank_name: Name of the bank
        :type bank_name: str
        :param transit_number:
        :type transit_number: str
        :param account_number:
        :type account_number: str
        :param account_name:
        :type account_name: str
        :return:
        :rtype:
        """
        self._db.add_bank(bank_name, transit_number, institution_number)
        account = self._db.add_bank_account(institution_number, account_name, account_number)

        return account

    def import_transactions_file(self, account_number, transactions_filepath):
        """

        :param account_number: Number of the account to add the transactions
        :type account_number: str
        :param transactions_filepath:
        :type transactions_filepath: pathlib.Path
        """
        transactions_df = pd.read_csv(transactions_filepath)

        if 'Filter' in transactions_df.columns:
            # transactions from Scotiabank
            transactions_df['amount'] = -transactions_df['Amount']
            transactions_df['date'] = pd.to_datetime(transactions_df['Date'], format='%Y-%m-%d')
            transactions_df.fillna('', inplace=True)
            transactions_df['comment'] = transactions_df['Description'] + transactions_df['Sub-description']
        elif 'Unnamed: 3' in transactions_df.columns:
            # transactions from PCU
            transactions_df = pd.read_csv(transactions_filepath,
                                          names=['account', 'date', 'comment', 'type', 'out', 'in', 'balance'],
                                          parse_dates=['date'])
            transactions_df.fillna(0, inplace=True)
            transactions_df['amount'] = transactions_df['in'] - transactions_df['out']
        else:
            raise KeyError('Unrecognised transactions format in {}'.format(transactions_filepath))

        transactions_df['account_number'] = account_number
        transactions_df['reviewed'] = False

        self._db.add_bulk_transactions(transactions_df[['account_number', 'amount', 'date', 'reviewed', 'comment']])

    def get_bank_account_transactions(self, account_number):
        """
        Get all the transactions for a bank account
        :param account_number:
        :type account_number: str
        :return:
        :rtype:
        """
        transactions_df = self._db.get_account_transactions(account_number)

        return transactions_df

    def reset_database(self):
        """
        Clears the database of all data. Re-creates tables.
        """
        self._db.reset_database()
