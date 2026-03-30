"""
All the interaction with the database should go through here
"""
import datetime

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound

from Database.Tables import Base, Bank, BankAccount, BankTransaction

# DB constants
DB_FILENAME = "modailmara-finances.db"


class DatabaseManager:
    """
    All interactions with the database
    """

    def __init__(self, db_filename=None):
        if db_filename is None:
            db_filename = DB_FILENAME
        self.__db_engine = create_engine("sqlite:///{}".format(db_filename))

        self.create_tables()

    def reset_database(self):
        """
        Delete everything, then re-create the tables.
        """
        self.clear_database()
        self.create_tables()

    def create_tables(self):
        """
        Creates all the database tables

        POST: all enums and tables are created in the database
        """
        Base.metadata.create_all(self.__db_engine, checkfirst=True)  # create all the tables

    def clear_database(self):
        """
        Clears the database of all data, types, and tables.

        PRE: database exists, may have some stuff in it
        POST: The database still exists but it has no data, tables, or types in it.
        """
        Base.metadata.drop_all(self.__db_engine, checkfirst=True)

    def add_bank(self, name, transit_number, institution_number):
        """
        Add a bank to the database
        :param name: Name of the bank
        :type name: str
        :param transit_number: Transit number for this bank organisation. 5 characters max
        :type transit_number: str
        :param institution_number: Unique institution number for the bank branch. 3 characters max
        :type institution_number: str
        """
        with Session(self.__db_engine) as session:
            try:
                bank = Bank(institution_number=institution_number, name=name, transit_number=transit_number)
                session.add(bank)
                session.commit()
            except IntegrityError:
                # already a bank with these details
                # ignore and do nothing
                pass
        return institution_number

    def get_all_banks(self):
        """

        :return: List of all the bank objects
        :rtype: list
        """
        with Session(self.__db_engine) as session:
            all_banks = session.execute(select(Bank)).scalars().all()
        return all_banks

    def get_all_accounts(self):
        """

        :return: List of all the account objects
        :rtype: list
        """
        account_details = []
        with Session(self.__db_engine) as session:
            for account in session.execute(select(BankAccount)).scalars().all():
                details = (account.account_number, account.name, account.bank_id)
                account_details.append(details)
        return account_details

    def add_bank_account(self, institution_number, name, account_number):
        """
        Add a bank account to the database. The new bank account is held by an existing bank.

        :param bank: institution_number of The bank that holds the new account
        :type bank: str
        :param name: The name of the new account
        :type name: str
        :param account_number: Unique number to identify the account
        :type account_number: str
        """
        with Session(self.__db_engine) as session:
            # bank = session.query(Bank).get(institution_number)
            account = BankAccount(name=name, account_number=account_number, bank_id=institution_number)

            session.add(account)
            session.commit()
        return account

    def add_bulk_transactions(self, transactions_df):
        """
        Adds all transactions in transactions_df (one per row) to the BankTransaction table.

        Assumes:
          - BankTransaction, BankAccount tables exist
          - the account number(s) in the transactions refer to existing accounts
        :param transactions_df:
        :type transactions_df: pandas.DataFrame
        :return:
        :rtype:
        """
        with Session(self.__db_engine) as session:
            # transactions_df.to_sql('BankTransaction', self.__db_engine, if_exists='append', index=False)
            transactions_dict = transactions_df.to_dict('records')
            stmt = insert(BankTransaction).values(transactions_dict)
            stmt = stmt.on_conflict_do_nothing(index_elements=["account_number", 'amount', 'date', 'comment'])

            session.execute(stmt)
            session.commit()

    def get_account_transactions(self, account_number):
        """

        :param account_number:
        :type account_number:
        :return:
        :rtype:
        """
        # with Session(self.__db_engine) as session:
        stmt = select(BankTransaction)\
            .where(BankTransaction.account_number == account_number)\
            .order_by(BankTransaction.date)
        transactions_df = pd.read_sql(stmt, self.__db_engine)

        return transactions_df

    def get_account_summary(self, account_number):
        """

        :param account_number:
        :type account_number:
        :return:
        :rtype:
        """
        with Session(self.__db_engine) as session:
            stmt = (
                select(func.count(), func.sum(BankTransaction.amount),
                       func.min(BankTransaction.date), func.max(BankTransaction.date))
                .select_from(BankTransaction)
                .where(BankTransaction.account_number == account_number)
            )
            result = session.execute(stmt).all()[0]
        return result
