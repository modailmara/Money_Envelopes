"""
All the interaction with the database should go through here
"""
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound

from Database.Tables import Base, Bank, BankAccount

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
        return bank

    def get_all_banks(self):
        """

        :return: List of all the bank objects
        :rtype: list
        """
        with Session(self.__db_engine) as session:
            all_banks = session.execute(select(Bank)).scalars().all()
        return all_banks

    def add_bank_account(self, bank, name, account_number):
        """
        Add a bank account to the database
        :param bank:
        :type bank: Bank
        :param name:
        :type name: str
        :param account_number:
        :type account_number: str
        :return:
        :rtype:
        """
        with Session(self.__db_engine) as session:
            account = BankAccount(name=name, account_number=account_number, bank=bank)

            session.add(account)
            session.commit()
        return account

    def add_bulk_transactions(self, transactions_df):
        """

        :param transactions_df:
        :type transactions_df: pandas.DataFrame
        :return:
        :rtype:
        """
        pass