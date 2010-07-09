#!/usr/bin/env python

# Author: Brian Cottingham
# 2010-07-08
# Parses the Bank of America "downloadable text" files and spits out Ledger-formated data

from optparse import OptionParser
import re

def print_equity(boa_statement):
    for line in open(boa_statement):
        if line.startswith("Beginning balance as of"):
            init_balance = line.split()[-1]
            init_date = line.split()[-2]
            init_balance = "$" + init_balance

    print '''
%(date)s * Opening balance
    Assets:Bank:Checking  %(balance)s
    Equity:Opening Balance
''' % {"date": init_date, "balance": init_balance}


def print_ledger(boa_statement, init=False):
    regex = re.compile(r'''(?P<date>\d{2}/\d{2}/\d{4})
                                \s{2,}
                                (?P<payee>.*)
                                \s{2,}
                                (?P<amount>-*[0-9,.]+)
                                \s{2,}
                                [0-9,.]+$
        ''', re.VERBOSE)

    for line in open(boa_statement):
        line = line.strip()
        rematch = re.match(regex, line)
        if rematch:
            trans_date, payee, amount = rematch.groups()

            credit = "something" if amount.startswith("-") else "Assets:Bank:Checking"
            debit = "Assets:Bank:Checking" if amount.startswith("-") else "something"
            amount = str(float(amount)*-1) if amount.startswith("-") else amount

            status = "*" if init is True else ""

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
