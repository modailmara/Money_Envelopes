""""""

import unittest

from sqlalchemy.orm import Session

from Database import Tables
from Database.DatabaseManager import DatabaseManager


class TestDatabase(unittest.TestCase):

    def setUp(self) -> None:
        self.db = DatabaseManager(db_filename='testing.db')

        self.db.reset_database()

    def tearDown(self) -> None:
        self.db.clear_database()

    # ------------------- Bank ---------------------------------------

    def test_add_bank(self):
        bank_name = 'name'
        transit_number = '01234'
        institution_number = '012'

        self.db.add_bank(bank_name, transit_number, institution_number)

        self.check_one_instance_of_bank(bank_name, transit_number, institution_number)

    def check_one_instance_of_bank(self, bank_name, transit_number, institution_number):
        # see if the bank is there and it's the only one
        all_banks = self.db.get_all_banks()
        self.assertEqual(len(all_banks), 1)
        bank = all_banks[0]
        self.assertEqual(bank.name, bank_name)
        self.assertEqual(bank.transit_number, transit_number)
        self.assertEqual(bank.institution_number, institution_number)

    def test_add_bank_twice(self):
        """
        Test adding the same bank twice.
        Should just ignore - no errors, one bank entry exists
        """
        bank_name = 'name'
        transit_number = '01234'
        institution_number = '012'

        self.db.add_bank(bank_name, transit_number, institution_number)

        self.db.add_bank(bank_name, transit_number, institution_number)

        self.check_one_instance_of_bank(bank_name, transit_number, institution_number)

    # ------------------- Bank Account ---------------------------------------

    def test_add_bank_account(self):
        all_accounts = self.db.get_all_bank_accounts()
        self.assertEqual(0, len(all_accounts))  # no accounts yet

        bank_name = 'name'
        transit_number = '01234'
        institution_number = '012'

        bank = self.db.add_bank(bank_name, transit_number, institution_number)

        account_name = 'account name'
        account_number = '0123456789'

        account = self.db.add_bank_account(bank, name=account_name, account_number=account_number)

        all_accounts = self.db.get_all_bank_accounts()

        self.assertEqual(1, len(all_accounts))  # 1 account now we've made it
        # check details (account.account_number, account.name, account.bank_id)
        self.assertEqual(account_number, all_accounts[0][0])
        self.assertEqual(account_name, all_accounts[0][1])
        self.assertEqual(institution_number, all_accounts[0][2])

    def test_add_bulk_bank_account_transactions(self):
        bank_name = 'name'
        transit_number = '01234'
        institution_number = '012'
        bank = self.db.add_bank(bank_name, transit_number, institution_number)
        account_name = 'account name'
        account_number = '0123456789'
        self.db.add_bank_account(bank, name=account_name, account_number=account_number)

        # set up the transactions·
        bulk_dict = {
            'account_number': [account_number, account_number, account_number],
            'amount': [],
            'date': [],
            'comment': []
        }
        self.assertFalse()

    def test_get_oldest_unreviewed_bank_account_transactions(self):
        self.assertFalse()

    def test_mark_bank_account_transaction_reviewed(self):
        self.assertFalse()

    def test_get_bank_account_summary(self):
        self.assertFalse()

    # ------------------- Envelope ---------------------------------------

    def test_add_envelope(self):
        self.assertFalse()

    def test_get_envelope_summary(self):
        self.assertFalse()

    def test_add_envelope_transaction(self):
        self.assertFalse()

    # ------------------- Macro ---------------------------------------


