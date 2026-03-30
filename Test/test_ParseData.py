import unittest
from pathlib import Path
import pandas as pd

from ParseData import ParseData

TEST_DATA_DIR = Path('.') / 'test_data'


class TestParseData(unittest.TestCase):

    def setUp(self) -> None:
        self.parse_data = ParseData(db_filename='testing.db')
        self.parse_data._db.reset_database()

    def test_create_list_accounts(self):
        """
        Tests creating new accounts and getting the list of existing accounts.
        """
        # test that the list of accounts is initially empty
        account_list = self.parse_data.get_accounts_list()
        self.assertEqual(0, len(account_list))  # add assertion here

        bank_details = {
            'institution_number': 'in01',
            'bank_name': 'bank one',
            'transit_number': 't01',
        }

        # add one account and test we get the right details back
        account_one_details = {
            'account_number': 'acc01',
            'account_name': 'first account'
        }
        self.parse_data.create_new_account(bank_details['institution_number'], bank_details['bank_name'],
                                           bank_details['transit_number'], account_one_details['account_number'],
                                           account_one_details['account_name'])
        account_list = self.parse_data.get_accounts_list()
        self.assertEqual(1, len(account_list))  # confirm the list only has one account
        self.check_account_details(account_list[0], account_one_details)  # check the account details are correct

        # add another account and test we get the right details back
        account_two_details = {
            'account_number': 'acc02',
            'account_name': 'second account'
        }
        self.parse_data.create_new_account(bank_details['institution_number'], bank_details['bank_name'],
                                           bank_details['transit_number'], account_two_details['account_number'],
                                           account_two_details['account_name'])
        account_list = self.parse_data.get_accounts_list()
        self.assertEqual(2, len(account_list))  # confirm there are two accounts in the list
        self.check_account_details(account_list[0], account_one_details)  # check the account details are correct
        self.check_account_details(account_list[1], account_two_details)  # check the account details are correct

    def test_import_scotia(self):
        """
        Test importing transactions from a file downloaded from ScotiaBank
        """
        # create a bank account to hold the transactions
        bank_details = {
            'institution_number': 'in01',
            'bank_name': 'bank one',
            'transit_number': 't01',
        }
        account_one_details = {
            'account_number': 'scotia01',
            'account_name': 'scotia account'
        }
        self.parse_data.create_new_account(bank_details['institution_number'], bank_details['bank_name'],
                                           bank_details['transit_number'], account_one_details['account_number'],
                                           account_one_details['account_name'])

        # import the transactions file
        self.parse_data.import_transactions_file(account_one_details['account_number'],
                                                 TEST_DATA_DIR / 'visa-5-2025.csv')
        transactions_df = self.parse_data.get_bank_account_transactions(account_one_details['account_number'])
        # check the number of transactions
        self.assertEqual(4, len(transactions_df))

        # test that repeat transactions aren't stored
        self.parse_data.import_transactions_file(account_one_details['account_number'],
                                                 TEST_DATA_DIR / 'visa-5-2025.csv')
        transactions_df = self.parse_data.get_bank_account_transactions(account_one_details['account_number'])
        # check the number of transactions
        self.assertEqual(4, len(transactions_df))

    def test_import_pcu(self):
        """
        Test importing transactions from a file downloaded from Provincial Credit Union
        """
        # create a bank account to hold the transactions
        bank_details = {
            'institution_number': 'in01',
            'bank_name': 'bank one',
            'transit_number': 't01',
        }
        account_one_details = {
            'account_number': 'pcu01',
            'account_name': 'pcu account'
        }
        self.parse_data.create_new_account(bank_details['institution_number'], bank_details['bank_name'],
                                           bank_details['transit_number'], account_one_details['account_number'],
                                           account_one_details['account_name'])

        # import the transactions file
        self.parse_data.import_transactions_file(account_one_details['account_number'],
                                                 TEST_DATA_DIR / 'operating-7-2025.csv')

        transactions_df = self.parse_data.get_bank_account_transactions(account_one_details['account_number'])

        # check the number of transactions
        self.assertEqual(8, len(transactions_df))

    def test_get_accounts_summary_list(self):
        """

        :return:
        :rtype:
        """
        # check it works for no accounts
        summary_list = self.parse_data.get_accounts_summary_list()
        self.assertEqual(0, len(summary_list))

        # create a bank account to hold the transactions
        bank_details = {
            'institution_number': 'in01',
            'bank_name': 'PCU',
            'transit_number': 't01',
        }
        account_one_details = {
            'account_number': 'pcu01',
            'account_name': 'pcu account one',
            'input filepath': TEST_DATA_DIR / 'operating-7-2025.csv'
        }
        self.parse_data.create_new_account(bank_details['institution_number'], bank_details['bank_name'],
                                           bank_details['transit_number'], account_one_details['account_number'],
                                           account_one_details['account_name'])

        summary_list = self.parse_data.get_accounts_summary_list()
        self.assertEqual(1, len(summary_list))

        account_two_details = {
            'account_number': 'pcu02',
            'account_name': 'pcu account two',
            'input filepath': TEST_DATA_DIR / 'operating-2-2026.csv'
        }
        self.parse_data.create_new_account(bank_details['institution_number'], bank_details['bank_name'],
                                           bank_details['transit_number'], account_two_details['account_number'],
                                           account_two_details['account_name'])

        # import the transactions file
        self.parse_data.import_transactions_file(account_one_details['account_number'],
                                                 account_one_details['input filepath'])
        self.parse_data.import_transactions_file(account_two_details['account_number'],
                                                 account_two_details['input filepath'])

        summary_list = self.parse_data.get_accounts_summary_list()
        self.assertEqual(2, len(summary_list))

        # check the summary details
        account_details = [account_one_details, account_two_details]
        for num, summary in enumerate(summary_list):
            self.assertEqual(5, len(summary))  # number of results: name, #trans, balance, min date, max date
            self.assertEqual(account_details[num]['account_name'], summary[0])  # correct account name
            # load the file - assumes PCU file
            input_df = pd.read_csv(account_details[num]['input filepath'],
                                   names=['account', 'date', 'comment', 'type', 'out', 'in', 'balance'],
                                   parse_dates=['date'])

            self.assertEqual(len(input_df), summary[1])  # number of transactions
            self.assertAlmostEqual(input_df['in'].sum() - input_df['out'].sum(), summary[2], places=2)  # balance
            self.assertEqual(input_df.date.min(), summary[3])  # min date
            self.assertEqual(input_df.date.max(), summary[4])  # max date

    def check_account_details(self, account, account_details):
        self.assertEqual(account_details['account_number'], account.account_number)
        self.assertEqual(account_details['account_name'], account.name)


if __name__ == '__main__':
    unittest.main()
