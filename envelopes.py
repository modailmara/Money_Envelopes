"""
Main entry point for the program. Command line interface to view and manage envelopes.
"""
import datetime
import locale
from pathlib import Path

from ParseData import ParseData

IMPORT_DIR = Path('.') / 'import'


class TextInterface:
    """
    Interactive text interface for performing basic functions of MoneyEnvelopes.

    The task here is to manage text input and output. Other tasks are passed off as soon as the input is gathered.
    """

    def __init__(self):
        # Uses the standard database and input directories and files
        self._parse_data = ParseData()

        # set the locale to local
        locale.setlocale(locale.LC_ALL, '')

        # latest retrieved total balances
        self.total_bank_balance = 0
        self.total_envelope_balance = 0

    def main(self):
        """
        Main menu for interaction.
        """
        while True:
            self.print_account_summary()
            self.print_envelope_summary()
            print('\n---')
            print('Options:')
            print('  1 - Import a transactions file (maybe create a Bank Account?)')
            print('  2 - Create an Envelope')
            print('  3 - Process unreviewed transactions')

            print('\n  98 - Clear all the data in the database.')
            print()

            option = input('Enter an option number (q to quit): ')
            option = option.strip()

            if option == '1':
                account_number = self.choose_account_number()
                if account_number is not None:
                    filename = self.choose_import_file()
                    if filename is not None:
                        self._parse_data.import_transactions_file(account_number, filename)
            elif option == '2':
                # create a new envelope
                self.create_new_envelope()
            elif option == '3':
                self.process_bank_transactions()
            elif option == '98':
                self._parse_data.reset_database()
            elif option.lower() in ['q', 'quit']:
                print('Quitting MoneyEnvelopes')
                break
            else:
                print('Please enter 1-3 or q. You entered "{}"'.format(option))

    def process_bank_transactions(self):
        """
        Shows bank transactions that have not been reviewed. Allows the user to copy to an envelope or mark as reviewed.
        """
        envelope_names = [envelope[0] for envelope in self._parse_data.get_envelopes_summary_list()]
        commands = {'m': 'Return to (m)ain menu',
                    'e <number> <name>': 'Assign transaction <number> to (E)nvelope <name>',
                    'r <number>': 'Mark transaction <number> as (r)eviewed'}
        command_str = '\n'.join(['{}: {}'.format(cmd, desc) for cmd, desc in commands.items()])
        option = ''
        while option != 'm':
            # show the list of oldest unreviewed transactions
            old_trans = self._parse_data.get_oldest_unreviewed_bank_transactions(10)
            print("Transactions: ")
            for num, (account_name, account_number, amount, date, comment) in enumerate(old_trans):
                print('  {} - {} {} {} {}'.format(num, account_name, date.strftime('%d-%b-%Y'),
                                                  locale.currency(amount, grouping=True), comment))
            print('Envelopes: {}'.format(envelope_names))

            option = input('\n{}\n> '.format(command_str))
            option = option.strip()

            option_words = [word.strip() for word in option.split(' ')]
            if option_words[0] == 'e' and len(option_words) == 3:
                # assign a transaction to an envelope
                if self.is_convertible_to_int(option_words[1]) and int(option_words[1]) < len(old_trans) \
                        and option_words[2] in envelope_names:
                    _, account_number, amount, date, comment = old_trans[int(option_words[1])]
                    self._parse_data.assign_transaction_to_envelope(account_number, amount, date, comment,
                                                                    option_words[2])
            elif option_words[0] == 'r' and len(option_words) == 2:
                # mark a transaction as reviewed without assigning it to an envelope
                if self.is_convertible_to_int(option_words[1]) and int(option_words[1]) < len(old_trans):
                    _, account_number, amount, date, comment = old_trans[int(option_words[1])]
                    self._parse_data.mark_reviewed(account_number, amount, date, comment)

    def create_new_envelope(self):
        """
        Prompt for information and create a new envelope
        """
        print("Creating a new Envelope...")
        invalid_names = [envelope[0] for envelope in self._parse_data.get_envelopes_summary_list()] + ['']
        name = ''
        while name in invalid_names:
            print("Enter a unique, non-empty envelope name. Envelope names: {}".format(invalid_names))
            name = input("Name: ")
            name = name.strip()
        print("(Optional) Description for '{}':".format(name))
        description = input()

        self._parse_data.create_new_envelope(name, description)

    def choose_account_number(self):
        """
        Choose a bank account. Gives option to create a new bank account.

        :return: Account number if one selected or None if not selected
        :rtype: str
        """
        while True:
            print('\n---')
            print('Choose a bank account:')
            account_names = []  # list of account_number
            for account_number, account_name, bank_id in self._parse_data.get_accounts_list():
                num = len(account_names)
                account_names.append(account_number)
                print(f'  {num} - {account_name} ({account_number})')
            print('\n {} - Create new bank account\n'.format(len(account_names)))

            option = input('Enter an option number (m to return to the main menu): ')
            if self.is_convertible_to_int(option) and int(option.strip()) in range(len(account_names)):
                # chose an existing account
                account_num = account_names[int(option)]
                return account_num
            elif self.is_convertible_to_int(option) and int(option.strip()) == len(account_names):
                self.create_bank_account()
            elif option.lower() in ['m', 'main']:
                return None
            else:
                print('Please enter a number 0 to {}, or m. You entered "{}"'.format(len(account_names) - 1, option))

    def create_bank_account(self):
        """
        Gather bank account information and create new bank account
        """
        print('\n---')
        print('Create a bank account:')
        institution_number = input("  Bank institution number: ")
        bank_name = input("  Bank name: ")
        transit_number = input("  Bank transit number: ")
        account_number = input("  Account number: ")
        account_name = input("  Account name: ")

        self._parse_data.create_new_account(institution_number, bank_name, transit_number, account_number, account_name)

    def choose_import_file(self):
        """

        :return: filepath to the transactions file in the import directory
        :rtype: pathlib.Path
        """
        print('\n---')
        print("Choose one of the files in the '{}' directory:".format(IMPORT_DIR.name))

        filenames = [filename for filename in IMPORT_DIR.iterdir() if filename.is_file()]

        for num, filename in enumerate(filenames):
            print('{} - {}'.format(num, filename))
        option = input('Enter an option number (m to return to the main menu): ')

        if self.is_convertible_to_int(option) and int(option.strip()) in range(len(filenames)):
            return IMPORT_DIR / filenames[int(option.strip())]
        elif option.strip() in ['m', 'main']:
            return None

    # ---------------------- Support functions --------------------------------

    @staticmethod
    def is_convertible_to_int(int_string):
        """

        :param int_string: String we might want to convert to an int
        :type int_string: str
        :return: True if the stripped string is an int
        :rtype: bool
        """
        try:
            int(int_string.strip())
            return True
        except ValueError:
            return False

    def print_envelope_summary(self):
        """
        Prints a summary of the current state of the envelopes

        Format example:
          Envelope              Balance    #trans.      Earliest         Latest
          ----------------------------------------------------------------------
          Payroll            $37,543.05         5    01-Jan-2021    02-Apr-2023
          Insurance          $37,543.05     3,000    15-Nov-2016    25-Feb-2018
          Health Insurance   $37,543.05    10,000    15-Nov-2016    25-Feb-2018
          ----------------------------------------------------------------------
          Total:            $112,629.15    13,005    15-Nov-2016    02-Apr-2023
        """
        print()
        # column widths
        column_padding = 4
        envelope_str = "Envelope"
        envelope_width = len('health insurance') + column_padding
        balance_str = "balance"
        balance_width = len('$112,629.15') + column_padding
        num_trans_str = "#trans."
        num_trans_width = len("10,000") + column_padding
        earliest_str = "Earliest"
        earliest_width = len('dd-mmm-YYYY') + column_padding
        latest_str = "Latest"
        latest_width = earliest_width

        # print the headings
        heading_str = f"{envelope_str:^{envelope_width}}"
        heading_str += f"{balance_str:>{balance_width}}"
        heading_str += f"{num_trans_str:>{num_trans_width}}"
        heading_str += f"{earliest_str:>{earliest_width}}"
        heading_str += f"{latest_str:>{latest_width}}"
        print(heading_str)
        print('-' * (envelope_width + balance_width + num_trans_width + earliest_width + latest_width))

        # print the summary lab test info
        total_balance = 0
        num_trans_total = 0
        earliest_date = None
        latest_date = None
        for envelope_name, balance, num_transactions, earliest, latest in self._parse_data.get_envelopes_summary_list():
            info_str = f"{envelope_name:<{envelope_width}}"

            balance = 0 if balance is None else balance
            total_balance += balance
            balance_str = locale.currency(balance, grouping=True)
            info_str += f"{balance_str:>{balance_width}}"

            num_transactions = 0 if num_transactions is None else num_transactions
            num_trans_total += num_transactions
            info_str += f"{num_transactions:>{num_trans_width}}"

            if earliest is None:
                earliest_str = '-'
            elif earliest_date is None:  # earliest is not None
                earliest_date = earliest
                earliest_str = earliest.strftime('%d-%b-%Y')
            else:  # neither are None
                earliest_str = earliest.strftime('%d-%b-%Y')
                earliest_date = min(earliest_date, earliest)
            info_str += f"{earliest_str:>{earliest_width}}"

            if latest is None:
                latest_str = '-'
            elif latest_date is None:
                latest_date = latest
                latest_str = latest.strftime('%d-%b-%Y')
            else:
                latest_date = max(latest_date, latest)
                latest_str = latest.strftime('%d-%b-%Y')
            info_str += f"{latest_str:>{latest_width}}"

            print(info_str)

        print('-' * (envelope_width + balance_width + num_trans_width + earliest_width + latest_width))
        total_str = 'Total'
        total_str = f"{total_str:^{envelope_width}}"
        total_balance_str = locale.currency(total_balance, grouping=True)
        total_str += f"{total_balance_str:>{balance_width}}"
        total_str += f"{num_trans_total:>{num_trans_width}}"
        if earliest_date is None:
            earliest_str = '-'
        else:
            earliest_str = earliest_date.strftime('%d-%b-%Y')
        total_str += f"{earliest_str:>{earliest_width}}"
        if latest_date is None:
            latest_str = '-'
        else:
            latest_str = latest_date.strftime('%d-%b-%Y')
        total_str += f"{latest_str:>{latest_width}}"
        print(total_str)
        self.total_envelope_balance = total_balance
        print("\nLeftover:  {}".format(locale.currency(self.total_bank_balance - self.total_envelope_balance,
                                                       grouping=True)))

    def print_account_summary(self):
        """
        Prints a summary of the current state of the database.

        Format example:
          Account          Balance    #trans.      Earliest         Latest
          -----------------------------------------------------------------
          Operating     $37,543.05         5    01-Jan-2021    02-Apr-2023
          Business      $37,543.05     3,000    15-Nov-2016    25-Feb-2018
          Visa          $37,543.05    10,000    15-Nov-2016    25-Feb-2018
          -----------------------------------------------------------------
          Total:       $112,629.15    13,005    15-Nov-2016    02-Apr-2023
        """
        print()
        # column widths
        column_padding = 4
        account_str = "Account"
        account_width = len('operating') + column_padding
        balance_str = "balance"
        balance_width = len('$112,629.15') + column_padding
        num_trans_str = "#trans."
        num_trans_width = len("100,000") + column_padding
        earliest_str = "Earliest"
        earliest_width = len('dd-mmm-YYYY') + column_padding
        latest_str = "Latest"
        latest_width = earliest_width

        # print the headings
        heading_str = f"{account_str:^{account_width}}"
        heading_str += f"{balance_str:>{balance_width}}"
        heading_str += f"{num_trans_str:>{num_trans_width}}"
        heading_str += f"{earliest_str:>{earliest_width}}"
        heading_str += f"{latest_str:>{latest_width}}"
        print(heading_str)
        print('-' * (account_width + balance_width + num_trans_width + earliest_width + latest_width))

        # print the summary lab test info
        total_balance = 0
        num_trans_total = 0
        earliest_date = datetime.datetime.now()
        latest_date = datetime.datetime(2000, 1, 1)
        for account_name, balance, num_transactions, earliest, latest in self._parse_data.get_accounts_summary_list():
            info_str = f"{account_name:<{account_width}}"

            balance = 0 if balance is None else balance
            total_balance += balance
            balance_str = locale.currency(balance, grouping=True)
            info_str += f"{balance_str:>{balance_width}}"

            num_transactions = 0 if num_transactions is None else num_transactions
            num_trans_total += num_transactions
            info_str += f"{num_transactions:>{num_trans_width}}"

            if earliest is None:
                earliest_str = '-'
            elif earliest_date is None:  # earliest is not None
                earliest_date = earliest
                earliest_str = earliest.strftime('%d-%b-%Y')
            else:  # neither are None
                earliest_str = earliest.strftime('%d-%b-%Y')
                earliest_date = min(earliest_date, earliest)
            info_str += f"{earliest_str:>{earliest_width}}"

            if latest is None:
                latest_str = '-'
            elif latest_date is None:
                latest_date = latest
                latest_str = latest.strftime('%d-%b-%Y')
            else:
                latest_date = max(latest_date, latest)
                latest_str = latest.strftime('%d-%b-%Y')
            #
            # if type(earliest) == datetime.datetime:
            #     earliest_date = min(earliest_date, earliest)
            #     earliest_str = earliest.strftime('%d-%b-%Y')
            # else:
            #     earliest_str = '-'
            # info_str += f"{earliest_str:>{earliest_width}}"
            #
            # if type(latest) == datetime.datetime:
            #     latest_date = max(latest_date, latest)
            #     latest_str = latest.strftime('%d-%b-%Y')
            # else:
            #     latest_str = '-'
            info_str += f"{latest_str:>{latest_width}}"
            print(info_str)

        print('-' * (account_width + balance_width + num_trans_width + earliest_width + latest_width))
        total_str = 'Total'
        total_str = f"{total_str:^{account_width}}"
        total_balance_str = locale.currency(total_balance, grouping=True)
        total_str += f"{total_balance_str:>{balance_width}}"
        total_str += f"{num_trans_total:>{num_trans_width}}"
        earliest_str = earliest_date.strftime('%d-%b-%Y')
        total_str += f"{earliest_str:>{earliest_width}}"
        latest_str = latest_date.strftime('%d-%b-%Y')
        total_str += f"{latest_str:>{latest_width}}"
        print(total_str)

        self.total_bank_balance = total_balance


if __name__ == "__main__":
    interface = TextInterface()
    interface.main()
