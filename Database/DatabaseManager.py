"""
All the interaction with the database should go through here
"""
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, select, delete
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound

from Database.Tables import Base, Bank, BankAccount, BankTransaction, Envelope, EnvelopeTransaction, \
    Macro, MacroTransaction

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

    # ------------------- Bank ---------------------------------------

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

    # ------------------- Bank Account ---------------------------------------

    def add_bank_account(self, institution_number, name, account_number):
        """
        Add a bank account to the database. The new bank account is held by an existing bank.

        :param institution_number: institution_number of The bank that holds the new account
        :type institution_number: str
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

    def get_all_bank_accounts(self):
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

    def add_bulk_bank_account_transactions(self, transactions_df):
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

    def get_bank_account_transactions(self, account_number):
        """

        :param account_number: Number identifying the account to get the transactions from
        :type account_number: str
        :return: Dataframe of all the transactions
        :rtype:
        """
        # with Session(self.__db_engine) as session:
        stmt = select(BankTransaction)\
            .where(BankTransaction.account_number == account_number)\
            .order_by(BankTransaction.date)
        transactions_df = pd.read_sql(stmt, self.__db_engine)

        return transactions_df

    def get_oldest_unreviewed_bank_account_transactions(self):
        """

        :return:
        :rtype:
        """
        stmt = select(BankTransaction).where(BankTransaction.reviewed == False).order_by(BankTransaction.date)
        transactions_df = pd.read_sql(stmt, self.__db_engine)

        return transactions_df

    def mark_bank_account_transaction_reviewed(self, account_number, amount, date, comment):
        """
        Changes the 'reviewed' field on an existing bank transaction to True

        :param account_number: Number of the account with the transaction
        :type account_number: str
        :param amount: Amount of the transaction
        :type amount: float
        :param date: Date of the transaction
        :type date: datetime
        :param comment: Comment on the transaction
        :type comment: str
        """
        with Session(self.__db_engine) as session:
            stmt = select(BankTransaction).filter_by(account_number=account_number, amount=amount,
                                                     date=date, comment=comment)
            transaction = session.execute(stmt).scalar_one()
            transaction.reviewed = True

            session.commit()

    def get_bank_account_summary(self, account_number):
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

    # ------------------- Envelope ---------------------------------------

    def add_envelope(self, envelope_name, description):
        """
        Add a bank account to the database. The new bank account is held by an existing bank.

        :param envelope_name: Unique name of the envelope
        :type envelope_name: str
        :param description: Description for the envelope
        :type description: str
        """
        with Session(self.__db_engine) as session:
            # bank = session.query(Bank).get(institution_number)
            envelope = Envelope(name=envelope_name, description=description)
            session.add(envelope)
            session.commit()
        return envelope

    def get_all_envelopes(self):
        """
        Gets a list of all the Envelope objects in the database
        :return: List of all Envelope objects
        :rtype: list
        """
        envelope_details = []
        with Session(self.__db_engine) as session:
            for envelope in session.execute(select(Envelope)).scalars().all():
                details = (envelope.name, envelope.description)
                envelope_details.append(details)
        return envelope_details

    def get_envelope_summary(self, envelope_name):
        """
        Gets summary information for an envelope object
        :param envelope_name:
        :type envelope_name:
        :return:
        :rtype:
        """
        with Session(self.__db_engine) as session:
            stmt = (
                select(func.count(), func.sum(EnvelopeTransaction.amount),
                       func.min(EnvelopeTransaction.date), func.max(EnvelopeTransaction.date))
                .select_from(EnvelopeTransaction)
                .where(EnvelopeTransaction.envelope == envelope_name)
            )
            result = session.execute(stmt).all()[0]
        return result

    def get_all_envelope_transactions(self, env_name):
        """
        Returns all the transactions in the given envelope.
        :param env_name: Name of the envelope
        :type env_name: str
        :return: List of tuples (transaction_id, date, amount, comment)
        :rtype: list
        """
        trans_list = []
        with Session(self.__db_engine) as session:
            stmt = (
                select(EnvelopeTransaction)
                    .where(EnvelopeTransaction.envelope == env_name)
                    .order_by(EnvelopeTransaction.date)
            )
            for transaction in session.execute(stmt).scalars().all():
                trans_list.append((transaction.id, transaction.date, transaction.amount, transaction.comment))
        return trans_list

    def add_envelope_transaction(self, envelope_name, amount, date, comment):
        """
        Adds a new envelope transaction.

        :param envelope_name: Name of the envelope
        :type envelope_name: str
        :param amount: Amount of the transaction
        :type amount: float
        :param date: Date of the transaction
        :type date: datetime.datetime
        :param comment: Comment about the transaction
        :type comment: str
        """
        with Session(self.__db_engine) as session:
            stmt = insert(EnvelopeTransaction).values(envelope=envelope_name, amount=amount, date=date, comment=comment)

            session.execute(stmt)
            session.commit()

    def delete_envelope_transaction(self, transaction_id):
        """

        :param transaction_id:
        :type transaction_id:
        """
        print("Transaction ID: {}".format(transaction_id))
        with Session(self.__db_engine) as session:
            stmt = delete(EnvelopeTransaction).where(EnvelopeTransaction.id == transaction_id)

            session.execute(stmt)
            session.commit()

    # ------------------- Macro ---------------------------------------

    def add_macro(self, macro_name, macro_description):
        """
        Creates a new macro
        :param macro_name: Name of the macro
        :type macro_name: str
        :param macro_description: Macro description
        :type macro_description: str
        """
        with Session(self.__db_engine) as session:
            stmt = insert(Macro).values(name=macro_name, description=macro_description)

            session.execute(stmt)
            session.commit()

    def get_all_macros(self):
        """
        Gets a list of all the macro objects in the database
        :return: List of all macro objects
        :rtype: list
        """
        macro_details = []
        with Session(self.__db_engine) as session:
            for macro in session.execute(select(Macro)).scalars().all():
                details = (macro.name, macro.description)
                macro_details.append(details)
        return macro_details

    def add_macro_transaction(self, macro_name, envelope_name, amount):
        """
        Adds a macro transaction
        :param macro_name: Name of the macro that the transaction belongs to
        :type macro_name: str
        :param envelope_name: Name of the envelope the amount will be added to when the macro is run
        :type envelope_name: str
        :param amount: Amount to add to the envelope when the macro is run
        :type amount: float
        """
        with Session(self.__db_engine) as session:
            stmt = insert(MacroTransaction).values(macro=macro_name, envelope=envelope_name, amount=amount)

            session.execute(stmt)
            session.commit()

    def get_all_macro_transactions(self, macro_name):
        """
        Gets a list of all stored transactions for a particular macro.

        :param macro_name: Name of the macro to get all the transactions for
        :type macro_name: str
        :return: List of transactions (envelope_name, amount) for the macro
        :rtype: list
        """
        macro_details = []
        with Session(self.__db_engine) as session:
            for transaction in session.execute(
                    select(MacroTransaction).where(MacroTransaction.macro == macro_name)
            ).scalars().all():
                details = (transaction.envelope, transaction.amount)
                macro_details.append(details)
        return macro_details

