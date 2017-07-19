#!/usr/bin/python

from __future__ import print_function

import os
import readline
import atexit
import math
from datetime import date
import numpy
import locale

def fl_fmt(f):
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        return locale.format("%.2f",f,grouping=True)
    except:
        return "%.2f"%f



def rlinput(prompt, prefill=''):
    '''
        Use readline and get user input
    '''
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return raw_input(prompt)
    finally:
        readline.set_startup_hook()

historyPath = os.path.expanduser("~/.rent_buy_calc_history")

def save_history(historyPath=historyPath):
    import readline
    readline.write_history_file(historyPath)

if os.path.exists(historyPath):
    readline.read_history_file(historyPath)

atexit.register(save_history)

def validate_value(low, high, given, mem_type, default):
    '''
        low/high: range
        given: user input as string
        memtype: 0: float, 1: int, 2/anything-else: string
        default: if range-check fails supply back this value. Note: string has no range check. Returned as-is.
    '''
    if mem_type == 1:
        val = int(given)
    elif mem_type == 0:
        val = float(given)
    else:
        return given
    if val < low and val > high:
        print("You should enter a value between %d and %d. You gave %s",low,high,given)
        return default
    else:
        return val

def ask_inputs():
    inputs = [
                [ "home_val",    "Home Value:"                            , "750000" , 100000 , 1000000 ,  1  ] ,
                [ "how_long",    "How long do you plan to hold the home:" , "30"     ,      2 ,     100 ,  1  ] ,
                [ "mort_per",    "Morgage percent:"                       , "3.67"   ,    1.0 ,    25.0 ,  0  ] ,
                [ "down_pay",    "Down Payment %:"                        , "10"     ,      1 ,     100 ,  1  ] ,
                [ "mort_term",   "Mortgage Term:"                         , "30"     ,      2 ,      40 ,  1  ] ,
                [ "price_appr",  "Price Appreciation %:"                  , "4.0"    ,    1.0 ,    25.0 ,  0  ] ,
                [ "rent_appr",   "Rent Appreciation%:"                    , "5.0"    ,    1.0 ,    25.0 ,  0  ] ,
                [ "inflation",   "Inflation %:"                           , "3.0"    ,    1.0 ,    25.0 ,  0  ] ,
                [ "inv_rate",    "Investment Rate%:"                      , "8.0"    ,    1.0 ,    25.0 ,  0  ] ,
                [ "prop_tax",    "Property Tax%:"                         , "0.8"    ,    0.1 ,    10.0 ,  0  ] ,
                [ "joint",       "Joint:"                                 , "yes"    ,   "yes",    "no" ,  2  ] ,
                [ "marg_rate",   "Marginal Rate%:"                        , "25"     ,      0 ,    25.0 ,  0  ] ,
                [ "buy_loss",    "Buying loss%:"                          , "1.5"    ,      0 ,    25.0 ,  0  ] ,
                [ "sell_loss",   "Selling loss%:"                         , "6"      ,      0 ,    25.0 ,  0  ] ,
                [ "maint",       "Maintenance:"                           , "1"      ,    0.1 ,    10.0 ,  0  ] ,
                [ "own_ins",     "Owner Insurance:"                       , "0.46"   ,    0.1 ,    10.0 ,  0  ] ,
                [ "month_comm",  "Monthly Common:"                        , "500"    ,      0 ,    5000 ,  1  ] ,
                [ "rent_dep",    "Rental Deposit:"                        , "0.27"   ,      0 ,     0.5 ,  0  ] ,
                [ "rent_ins",    "Renter Insurane:"                       , "0.5"    ,    0.1 ,    10.0 ,  0  ] ,
            ]
    given_inputs = {}
    for i in inputs:
        mem_name = i[0]
        mem_str = i[1]
        def_val = i[2]
        low = i[3]
        high = i[4]
        mem_type = i[5]
        given=rlinput(mem_str, def_val)
        value  = validate_value(low, high, given, mem_type, def_val)
        given_inputs[mem_name] = value
    return given_inputs

def compound_interest(p,n,r):
    '''
        Returns p * (1 + rate)^r
    '''
    rr = r/100.0
    return p * math.pow((1+rr), n)

def add_years(d, years):
    """
    Source: https://stackoverflow.com/a/15743908/2587153

    Add goddamn years to a date, taking care of Feb-29!
    """
    try:
        return d.replace(year = d.year + years)
    except ValueError:
        return d + (date(d.year + years, 1, 1) - date(d.year, 1, 1))

def extrapolate_values(initial, years, rate):
    '''
        Given an initial value, and years and rate_of_increase, return
            years lenth list of (date, value)s at end of each year.
    '''
    val_i = initial
    date_i = date.today()
    rr = rate/100.0
    result = []
    for i in range(years):
        val_i = val_i * ( 1 + rr)
        date_i = add_years(date_i,1)
        result.append((date_i,val_i))
    return result

def extrapolate_values_on_a_base(base, base_inc_rate, years, rate_on_base):
    '''
        Return list of (date, value) for n next years. (Result in years len long)
        That is, at end of each year, we have a value derived such that its is rate_on_base, where base is increasing at base_inc_rate.
    '''
    base_i = base
    date_i = date.today()
    rr = base_inc_rate/100.0
    vr = rate_on_base/100.0
    result = []
    for i in range(years):
        date_i = add_years(date_i,1)
        base_i = base_i * (1 + rr)
        value_i = base_i * vr
        result.append((date_i, value_i))
    return result

def update_invest_history(investment_history, needed_val, inv_rate, tax_rate):
    '''
        We have investment history in the form of list of
            (date, investment), with 0 values in case none was invested/available in the year.
        needed_val is what we need
    '''
    residual = 1
    step = 0.05
    guess = 0.05
    epsilon = 0.0001
    limit = 10000
    while abs(residual) > epsilon and limit > 0:
        limit -= 1
        residual = 0.0
        for i, ta in enumerate(transactions):
            residual += ta[1] / pow(guess, years[i])
        if abs(residual) > epsilon:
            if residual > 0:
                guess += step
            else:
                guess -= step
                step /= 2.0
    if limit <= 0:
        raise Exception("Couldn't guess")
    return guess-1


inp = ask_inputs()
print("got inputs\n%s"%inp)

#Find value of home at end of period
value_at_end = compound_interest(inp['home_val'], inp['how_long'], inp['price_appr'])
print("Home value at end of %d years is %s"%(inp['how_long'], fl_fmt(value_at_end)))

sale_loss = value_at_end * (inp['sell_loss']/100.0)
print("Sale-loss:%s"%(fl_fmt(sale_loss)))
value_at_end -= sale_loss

gains = value_at_end - inp['home_val']
if inp['how_long'] > 3:
    if inp['joint'] == "yes":
        deduct = 500000
    else:
        deduct = 250000
    gains -= deduct
    if gains:
        gains_loss = gains / inp['marg_rate']
        print("Cap-Gains Loss:%s"%(fl_fmt(gains_loss)))
        value_at_end -= gains_loss

property_taxes = extrapolate_values_on_a_base(inp['home_val'],inp['price_appr'],inp['how_long'],inp['prop_tax'])
maintenances   = extrapolate_values_on_a_base(inp['home_val'],inp['price_appr'],inp['how_long'],inp['maint'])
owner_insur    = extrapolate_values_on_a_base(inp['home_val'],inp['price_appr'],inp['how_long'],inp['own_ins'])
monthly_initial = inp['month_comm'] * 12
monthly_common_expenses = extrapolate_values(monthly_initial, inp['how_long'], inp['inflation'])

monthly_mortgage_rate = inp['mort_per'] / 1200.0
no_mortgage_months    = inp['mort_term'] * 12
downpay_value         = inp['home_val'] * (inp['down_pay']/100.0)
mortgage_value        = (inp['home_val'] - downpay_value) * -1
mortgate_pmt          = numpy.pmt(monthly_mortgage_rate, no_mortgage_months, mortgage_value)
print("Mortgage value is %s"%fl_fmt(mortgate_pmt))

tax_exception  = 9300
if inp['joint'] == "yes":
    tax_exception = 12600

buyer_year_expense = []
for i in range(inp['how_long']):
    exp = maintenances[i][1]
    exp += monthly_common_expenses[i][1]
    exp += owner_insur[i][1]
    mort_plus_prop = property_taxes[i][1] + mortgate_pmt * 12
    exp += mort_plus_prop
    if mort_plus_prop > tax_exception:
        tax_save = (mort_plus_prop - tax_exception) * (inp['marg_rate']/100.0)
        exp -= tax_save
    buyer_year_expense.append(exp)


print("every situation:")
for i in range(inp['how_long']):
    print("year %d,  property_taxes: %s maintenances: %s monthly_common_expenses: %s  net_yearly: %s"%(
                i,fl_fmt(property_taxes[i][1]),fl_fmt(maintenances[i][1]),fl_fmt(monthly_common_expenses[i][1]),fl_fmt(buyer_year_expense[i])))
print("Final value end of %d years is %s"%(inp['how_long'], fl_fmt(value_at_end)))

buy_loss = inp['home_val'] * (inp['buy_loss']/100.0)
initial_buy_expense = downpay_value + buy_loss
print("Initial Buy Expense %s"%fl_fmt(initial_buy_expense))

# Rental ase.
rent_guess = inp['home_val']/250.0
rental_values = extrapolate_values(rent_guess,inp['how_long'],inp['rent_appr'])
renter_insur =  extrapolate_values_on_a_base(rent_guess, inp['rent_appr'],inp['how_long'],inp['rent_ins'])

#first year
first_year_exp = rental_value[0][1] + renter_insur[0][1]
first_year_invest = initial_buy_expense - first_year_exp
investment_history = []
investment_history.append(rental_values[0][0], first_year_invest)
available_kitty = 0
for i in range(1,inp['how_long']):
    available_kitty *= (1 + inp['inv_rate']/100.0)
    # what is the expense for this eyar
    renter_exp_for_this_year = rental_values[i][1] + renter_insur[i][1]
    buyer_exp_for_this_year = buyer_year_expense[i][1]
    if buyer_exp_for_this_year > renter_exp_for_this_year:
        #great. Just subtract that and put that as investment.
        inv_val = buyer_exp_for_this_year - renter_exp_for_this_year
        investment_history.append(rental_values[i][0], inv_val)
    else:
        needed_val = renter_exp_for_this_year - buyer_exp_for_this_year
        #grr. we need to break our kitty to fund our expense.
        lost_value = update_invest_history(investment_history, this year, needed_val)
        available_kitty -= lost_value
available_kitty *= (1 + inp['inv_rate']/100.0)

print("available_kitty is %s"%(fl_fmt(available_kitty)))
