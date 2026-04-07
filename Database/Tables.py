"""
Definitions for all the database tables.

Assumptions:
  - only one user/owner/business
"""

from sqlalchemy import ForeignKey, String
from typing import Optional, List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from datetime import datetime


class Base(DeclarativeBase):
    pass


class Bank(Base):
    """
    Details of a bank branch that holds one of the accounts
    """
    __tablename__ = "bank"

    institution_number: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    transit_number: Mapped[str] = mapped_column(String(5))

    accounts: Mapped[Optional[List["BankAccount"]]] = relationship(back_populates="bank", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f'Bank: {self.name}: transit={self.transit_number}, institution={self.institution_number}'


class BankAccount(Base):
    """
    Describes a bank account.

    Assumes account numbers are unique even across institutions.
    """
    __tablename__ = "bank_account"

    account_number: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str]

    bank_id = mapped_column(ForeignKey("bank.institution_number", ondelete='CASCADE'))
    bank: Mapped["Bank"] = relationship(back_populates='accounts')


class BankTransaction(Base):
    """
    Money came or went from a bank account
    """
    __tablename__ = "bank_transaction"

    account_number: Mapped[int] = mapped_column(ForeignKey('bank_account.account_number'), primary_key=True)
    amount: Mapped[float] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(primary_key=True)
    comment: Mapped[str] = mapped_column(primary_key=True)

    reviewed: Mapped[bool]


class Envelope(Base):
    """
    Envelope to set aside money for expenses
    """
    __tablename__ = "envelope"

    name: Mapped[str] = mapped_column(primary_key=True)

    description: Mapped[Optional[str]]


class EnvelopeTransaction(Base):
    """
    Money moved in (set money aside) or out (paid a bill) of the envelope.
    Or maybe just moving money around.
    """
    __tablename__ = 'envelope_transaction'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    envelope: Mapped[str] = mapped_column(ForeignKey('envelope.name'))
    amount: Mapped[float]
    date: Mapped[datetime]

    comment: Mapped[Optional[str]]


class Macro(Base):
    """
    A macro is a group of payments to Envelopes. It's a convenience for a group of payments used often.
    """
    __tablename__ = "macro"

    name: Mapped[str] = mapped_column(primary_key=True)
    description: Mapped[str]


class MacroTransaction(Base):
    """
    Transaction operations that are part of a macro.
    """
    __tablename__ = 'macro_transaction'

    macro: Mapped[str] = mapped_column(ForeignKey('macro.name'), primary_key=True)
    envelope: Mapped[str] = mapped_column(ForeignKey('envelope.name'), primary_key=True)

    amount: Mapped[float]
