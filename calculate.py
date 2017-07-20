#!/usr/bin/python

from __future__ import print_function

import os
import atexit
import math
from datetime import date
import numpy
import locale
import argparse
import sys

pretty = True

def fl_fmt(f):
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        return locale.format("%.2f",f,grouping=pretty)
    except:
        return "%.2f"%f

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

inputs = [
            [ "home_val",    "Home Value:"                            , "750000" , 100000 , 1000000 ,  1  ] ,
            [ "how_long",    "How long do you plan to hold the home:" , "30"     ,      2 ,     100 ,  1  ] ,
            [ "mort_per",    "Morgage percent:"                       , "4.0"    ,    1.0 ,    25.0 ,  0  ] ,
            [ "down_pay",    "Down Payment %:"                        , "10"     ,      1 ,     100 ,  1  ] ,
            [ "mort_term",   "Mortgage Term:"                         , "30"     ,      2 ,      40 ,  1  ] ,
            [ "price_appr",  "Price Appreciation %:"                  , "4.0"    ,    1.0 ,    25.0 ,  0  ] ,
            [ "rent_appr",   "Rent Appreciation%:"                    , "4.5"    ,    1.0 ,    25.0 ,  0  ] ,
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
            [ "rent_ins",    "Renter Insurane:"                       , "0.5"    ,    0.1 ,    10.0 ,  0  ] ,
        ]

def parse_command_line_inputs():

    parser = argparse.ArgumentParser()
    for i in inputs:
        parser.add_argument("--" + i[0], dest=i[0], help=i[1], default=i[2])
    parser.add_argument("--nopretty", action="store_true")

    parsed_args = parser.parse_args()
    failed = False
    given_inputs = {}
    for i in inputs:
        if not hasattr(parsed_args,i[0]):
            print("Supply input: %s"%i[0])
            failed = True
        else:
            given = getattr(parsed_args,i[0])
            def_val = i[2]
            low = i[3]
            high = i[4]
            mem_type = i[5]
            value  = validate_value(low, high, given, mem_type, def_val)
            given_inputs[i[0]] = value

    if failed:
        sys.exit(1)

    global pretty
    if parsed_args.nopretty:
        pretty = False;

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

def principal_remaining_after(p, n, r, rem_years):
    rr = r / 1200.0
    nn = n*12
    rem_mths = rem_years * 12
    paid_mths = nn - rem_mths
    paid_prin = 0.0
    for i in range(1,paid_mths+1):
        pp = numpy.ppmt(rr, i, nn, p)
        paid_prin += pp
    return (p*-1) - paid_prin


def get_a_renter_oppurtunity_cost(rent_guess, how_long, rent_appr, rent_ins):
    rental_values = extrapolate_values(rent_guess*12,how_long,rent_appr)
    renter_insur =  extrapolate_values_on_a_base(rent_guess*12, rent_appr,how_long,rent_ins)

    renter_oppurtunity_cost = 0.0
    renter_year_expense = []
    for i in range(inp['how_long']):
        renter_exp_for_this_year = rental_values[i][1] + renter_insur[i][1]
        renter_year_expense.append(renter_exp_for_this_year)
        years_left = inp['how_long'] - i
        renter_oppurtunity_cost += compound_interest(renter_exp_for_this_year, years_left, inp['inv_rate'])

    # print("Renter situation:")
    # for i in range(inp['how_long']):
        # print("year %d,  rent: %s rent_insur: %s net_yearly: %s"%(
                    # i,fl_fmt(rental_values[i][1]),fl_fmt(renter_insur[i][1]), fl_fmt(renter_year_expense[i])))

    # print("oppurtunity_cost_for_renter at guess_rent:%s is: %s"%(fl_fmt(rent_guess),fl_fmt(renter_oppurtunity_cost)))

    return renter_oppurtunity_cost



inp = parse_command_line_inputs()
print("got inputs\n%s"%inp)

#Find value of home at end of period
value_at_end = compound_interest(inp['home_val'], inp['how_long'], inp['price_appr'])
#print("Home value at end of %d years is %s"%(inp['how_long'], fl_fmt(value_at_end)))

sale_loss = value_at_end * (inp['sell_loss']/100.0)
#print("Sale-loss:%s"%(fl_fmt(sale_loss)))
value_at_end -= sale_loss

gains = value_at_end - inp['home_val']
if inp['how_long'] > 3:
    if inp['joint'] == "yes":
        deduct = 500000
    else:
        deduct = 250000
    gains -= deduct
    if gains > 0:
        gains_loss = gains / inp['marg_rate']
        #print("Cap-Gains Loss:%s"%(fl_fmt(gains_loss)))
        value_at_end -= gains_loss

monthly_mortgage_rate = inp['mort_per'] / 1200.0
no_mortgage_months    = inp['mort_term'] * 12
downpay_value         = inp['home_val'] * (inp['down_pay']/100.0)
mortgage_value        = (inp['home_val'] - downpay_value) * -1
mortgate_pmt          = numpy.pmt(monthly_mortgage_rate, no_mortgage_months, mortgage_value)
#print("Mortgage value is %s"%fl_fmt(mortgate_pmt))

if inp['how_long'] < inp['mort_term']:
    rem = inp['mort_term'] - inp['how_long']
    rem_prin = principal_remaining_after(mortgage_value, inp['mort_term'], inp['mort_per'], rem)
    #print("Remaining Principal to Pay:%s"%(fl_fmt(rem_prin)))
    value_at_end -= rem_prin


property_taxes = extrapolate_values_on_a_base(inp['home_val'],inp['price_appr'],inp['how_long'],inp['prop_tax'])
maintenances   = extrapolate_values_on_a_base(inp['home_val'],inp['price_appr'],inp['how_long'],inp['maint'])
owner_insur    = extrapolate_values_on_a_base(inp['home_val'],inp['price_appr'],inp['how_long'],inp['own_ins'])
monthly_initial = inp['month_comm'] * 12
monthly_common_expenses = extrapolate_values(monthly_initial, inp['how_long'], inp['inflation'])


tax_exception  = 9300
if inp['joint'] == "yes":
    tax_exception = 12600

buyer_year_expense = []
buyer_oppur_cost = 0.0
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
    years_left = inp['how_long'] - i
    buyer_oppur_cost += compound_interest(exp, years_left, inp['inv_rate'])


#print("Buyer situation:")
for i in range(inp['how_long']):
    if (i < inp['mort_term']):
        mort_val = mortgate_pmt * 12
    else:
        mort_val = 0.0
    #print("year %d,  property_taxes: %s maintenances: %s monthly_common_expenses: %s  mortgage: %s net_yearly: %s"%(
                #i,fl_fmt(property_taxes[i][1]),fl_fmt(maintenances[i][1]),fl_fmt(monthly_common_expenses[i][1]),fl_fmt(mort_val), fl_fmt(buyer_year_expense[i])))


buy_loss = inp['home_val'] * (inp['buy_loss']/100.0)
initial_buy_expense = downpay_value + buy_loss
print("Initial Buy Expense %s"%fl_fmt(initial_buy_expense))

buyer_oppur_cost += compound_interest(initial_buy_expense, inp['how_long'], inp['inv_rate'])
buyer_net_oppurtuinty = buyer_oppur_cost - value_at_end

print("oppurtunity_cost_for_buyer: %s"%fl_fmt(buyer_oppur_cost))
print("Final value end of %d years is %s"%(inp['how_long'], fl_fmt(value_at_end)))
print("Net for buyer:%s"%fl_fmt(buyer_net_oppurtuinty))


residual = 10000
rent_initial_guess = inp['home_val']/250.0
rent_guess = rent_initial_guess
epsilon = 1.0
limit = 10000
lower_bound = None
upper_bound = None
while abs(residual) > epsilon and limit > 0:
    limit -= 1
    renter_oppurtunity_cost = get_a_renter_oppurtunity_cost(rent_guess,inp['how_long'],inp['rent_appr'],inp['rent_ins'])
    residual = buyer_net_oppurtuinty - renter_oppurtunity_cost
    if abs(residual) > epsilon:
        #print("left:%d, Took a guess of %s, and rent_cost:%s , diff: %s"%(limit, fl_fmt(rent_guess), fl_fmt(renter_oppurtunity_cost), fl_fmt(residual)))
        if residual > 0:
            lower_bound = rent_guess
            if not upper_bound:
                rent_guess += 100
                continue
        else:
            upper_bound = rent_guess
            if not lower_bound:
                rent_guess -= 100
                continue
        rent_guess = (upper_bound + lower_bound)/2.0
if limit <= 0:
    raise Exception("Couldn't guess")

print ("Start renting if rent value is less than %s"%fl_fmt(rent_guess))
