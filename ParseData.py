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
        Gets information for all the existing bank accounts in the database: number, name, bank_id

        :return: List of info for all accounts
        :rtype: list
        """
        return self._db.get_all_accounts()

    def get_accounts_summary_list(self):
        """
        Returns summary information about accounts and their transactions

        Summary data for an account is a tuple:
          - account name,
          - balance,
          - number of transactions,
          - date of earliest transaction,
          - date of most recent transaction

        :return: List of tuples (name, balance, #trans, earliest date, latest date)
        :rtype: list
        """
        accounts = self._db.get_all_accounts()
        summary_list = []
        for account in accounts:
            name = account[1]
            num_trans, balance, earliest_trans, latest_trans = self._db.get_account_summary(account[0])
            summary_list.append((name, balance, num_trans, earliest_trans, latest_trans))
        return summary_list

    def get_envelopes_summary_list(self):
        """
        Returns summary information about envelopes and their transactions

        Summary data for an account is a tuple:
          - envelope name,
          - balance,
          - number of transactions,
          - date of earliest transaction,
          - date of most recent transaction

        :return: List of tuples (name, balance, #trans, earliest date, latest date)
        :rtype: list
        """
        envelopes = self._db.get_all_envelopes()
        summary_list = []
        for envelope in envelopes:
            name = envelope[0]
            num_trans, balance, earliest_trans, latest_trans = self._db.get_envelope_summary(envelope[0])
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
        :return: The new account object
        :rtype: BankAccount object
        """
        self._db.add_bank(bank_name, transit_number, institution_number)
        account = self._db.add_bank_account(institution_number, account_name, account_number)

        return account

    def create_new_envelope(self, name, description):
        """
        Creates a new envelope

        :param name: Name of the envelope
        :type name: str
        :param description: Optional description of the envelope
        :type description: str
        :return:
        :rtype:
        """
        self._db.add_envelope(name, description)

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

        self._db.add_bulk_bank_transactions(
            transactions_df[['account_number', 'amount', 'date', 'reviewed', 'comment']])

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

    def get_oldest_unreviewed_bank_transactions(self, number):
        """
        Get a list of the oldest unreviewed bank transactions, regardless of account.

        Returns a list of tuples:
          - account name
          - account number
          - amount
          - date
          - comment

        :param number: Maximum number of transactions to return
        :type number: int
        :return: List of tuples with transaction information
        :rtype: list
        """
        # get the accounts details
        account_detail_dict = {number: name for number, name, _ in self.get_accounts_list()}
        # get all the transactions
        transactions_df = self._db.get_oldest_unreviewed_bank_transactions()

        # turn into the list of tuples
        trans_list = []
        for _, row in transactions_df.iloc[:number, :].iterrows():
            account_name = account_detail_dict[row.account_number]
            trans_info = (account_name, row.account_number, row.amount, row.date, row.comment)
            trans_list.append(trans_info)

        return trans_list

    def assign_transaction_to_envelope(self, account_number, amount, date, comment, envelope_name):
        """
        Assign a bank transaction to an envelope.
        Actually just creates a new envelope transaction. Bank transactions are immutable once input from files.

        :param amount:
        :type amount:
        :param date:
        :type date:
        :param comment:
        :type comment:
        :param envelope_name:
        :type envelope_name:
        """
        self._db.add_envelope_transaction(envelope_name, amount, date, comment)

        self.mark_reviewed(account_number, amount, date, comment)

    def mark_reviewed(self, account_number, amount, date, comment):
        """
        Marks a bank transaction as reviewed

        :param account_number: Account number that the transaction belongs to
        :type account_number: str
        :param amount: Amount of the transaction
        :type amount: float
        :param date: Date of the transaction
        :type date: datetime.datetime
        :param comment: Comment for the transaction
        :type comment: str
        """
        self._db.mark_bank_transaction_reviewed(account_number, amount, date, comment)

    def reset_database(self):
        """
        Clears the database of all data. Re-creates tables.
        """
        self._db.reset_database()
