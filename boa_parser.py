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


def print_ledger(boa_statement, init=False):
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

    for line in open(boa_statement):
        line = line.strip()
        rematch = re.match(regex, line)
        if rematch:
            trans_date, payee, amount = rematch.groups()
            amount = amount.replace(",", "")

            # Convert date to Ledger-happy format
            time_tuple = time.strptime(trans_date, "%m/%d/%Y")
            trans_date = time.strftime("%Y/%m/%d", time_tuple)

            credit = "something"  # Dummy category to use when we don't know the real category
            debit = "Assets:Bank:Checking"  # Assume all transactions are for a checking account
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
    oparser = OptionParser()
    oparser.add_option("-f", "--file", 
        action="store", 
        dest="boa_statement", 
        help="Bank of America statement file, 'Printable Text Format'")

    oparser.add_option("-i", "--init", 
        action="store_true", 
        dest="init", 
        help="Initialize a ledger from scratch. Prints an Equity->Checking transfer at the top, and clears all transactions.", 
        default=False)

    (options, args) = oparser.parse_args()
    if options.boa_statement is None:
        oparser.error("Statement filename is required")

    if options.init:
        print_equity(options.boa_statement)
    print_equity
    print_ledger(options.boa_statement, options.init)
    


if __name__ == "__main__":
    main()
