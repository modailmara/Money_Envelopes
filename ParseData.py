"""
Does the work of taking commands from the interface and translating them into DatabaseManager functions.
"""

from Database.DatabaseManager import DatabaseManager


class ParseData:
    """
    Takes MoneyEnvelope operations and forms them into DatabaseManager commands.
    """

    def __init__(self, db_filename=None):
        self.__db = DatabaseManager(db_filename)

    def get_accounts_list(self):
        """
        Gets summary data for all the existing accounts in the database.

        Summary data for an account is:
          - account name,
          - balance,
          - number of transactions,
          - date of earliest transaction,
          - date of most recent transaction

        :return: List of summary data for all accounts
        :rtype: list
        """
        return []

    def create_new_account(self, institution_number, bank_name, transit_number, account_number, account_name):
        """

        :param institution_number:
        :type institution_number:
        :param bank_name:
        :type bank_name:
        :param transit_number:
        :type transit_number:
        :param account_number:
        :type account_number:
        :param account_name:
        :type account_name:
        :return:
        :rtype:
        """
        bank = self.__db.add_bank(bank_name, transit_number, institution_number)
        self.__db.add_bank_account(bank, account_name, account_number)

    def import_transactions_file(self, account_number, filename):
        """

        :param account_number:
        :type account_number: str
        :param filename:
        :type filename:
        :return:
        :rtype:
        """
        pass