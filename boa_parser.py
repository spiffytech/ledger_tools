#!/usr/bin/env python

# Author: Brian Cottingham
# 2010-07-08
# Parses the Bank of America "downloadable text" files and spits out Ledger-formated data

import time
from optparse import OptionParser
import os
import re
import yaml

# Find the file with human-readable translations for BoA statement descriptions
boa_translations_filename = "boa_translate.yaml"
boa_translations_locs = (
    os.path.join(os.path.dirname(__file__), boa_translations_filename),
    os.path.join(os.path.expanduser("~"), "." + boa_translations_filename),
    os.path.join(os.path.normpath("/etc/"), boa_translations_filename)
)
for loc in boa_translations_locs:
    if os.path.exists(loc):
        boa_translations = loc
        break
else: 
    print "Can't find Bank of America description translation file. \nPlease put it in one of these locations:\n"
    for loc in boa_translations_locs:
        print loc
    exit(1)


def print_equity(boa_statement):
    """Prints a transaction that initializes the account balance. Used when creating a new ledger file."""
    for line in open(boa_statement):
        if line.startswith("Beginning balance as of"):
            init_balance = line.split()[-1]
            
            init_date = line.split()[-2]
            time_tuple = time.strptime(init_date, "%m/%d/%Y")
            init_date = time.strftime("%Y/%m/%d", time_tuple)

    print '''
%(date)s * Opening balance
    Assets:Bank:Checking  $%(balance)s
    Equity:Opening Balance
''' % {"date": init_date, "balance": init_balance}


def print_ledger(stmt_file, init, account_name):
    """Parses the BoA statement file and prints all transactions in a Ledger-friendly format."""

    # Regex to match/parse transactions in the BoA statement file
    regex = re.compile(r'''(?P<date>\d{2}/\d{2}/\d{4})  # Date of the transaction
                                \s{2,}
                                (?P<payee>.*)  # Transaction description(payee)
                                \s{2,}
                                (?P<amount>-*[0-9,.]+)  # Transaction value
                                \s{2,}
                                [0-9,.]+$  # Running account balance
        ''', re.VERBOSE)

    desc_patterns = list(yaml.load_all(open(boa_translations)))

    for line in open(stmt_file):
        line = line.strip()
        rematch = re.match(regex, line)
        if rematch:
            trans_date, payee, amount = rematch.groups()
            amount = amount.replace(",", "")

            # Convert date to Ledger-happy format
            time_tuple = time.strptime(trans_date, "%m/%d/%Y")
            trans_date = time.strftime("%Y/%m/%d", time_tuple)

            credit = "something"  # Dummy category to use when we don't know the real category
            debit = account_name
            amount = str(float(amount)*-1)

            # Parse the BoA descriptions for payee/category
            for pattern in desc_patterns:
                if re.search(pattern["pattern"], payee):
                    try:
                        credit = pattern["category"]
                    except KeyError:
                        pass
                    payee = pattern["payee"]

            status = "*" if init is True else ""  # If scrit is passed "-i", all transactions are cleared

            transaction = '''
%(date)s %(status)s %(payee)s
    %(credit)-35s  $%(amount)s
    %(debit)s
''' % {"payee": payee, 
        "amount": amount, 
        "date": trans_date, 
        "debit": debit, 
        "credit": credit, 
        "status": status
    }

            print transaction


def main():
    usage = "usage: %prog [options] [FILE]\nFormats your Bank of America 'plain text' statement file into a Ledger-friendly format."
    oparser = OptionParser(usage=usage)
    oparser.add_option("-i", "--init", 
        action="store_true", 
        dest="init", 
        help="Initialize a ledger from scratch. Prints an Equity->Checking transfer at the top, and clears all transactions.", 
        default=False
    )

    oparser.add_option("--account",
        action="store",
        dest="account_name",
        help="Name of the bank account this statement is for",
        default="Assets:Bank:Checking"
    )

    (options, args) = oparser.parse_args()
    if len(args) == 0:
        oparser.error("Statement filename is required")
    else:
        boa_statement = args[0]

    if options.init:
        print_equity(boa_statement)
    print_equity
    print_ledger(stmt_file=boa_statement, init=options.init, account_name=options.account_name)
    


if __name__ == "__main__":
    main()

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
