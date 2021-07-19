#!/usr/bin/python

from __future__ import print_function

import os
import math
import numpy_financial as npf
import locale
import argparse
import sys

pretty = True
set_verbose_level = 1

def log_print(verbose_level, format_str, tuple_of_args=()):
    if set_verbose_level >= verbose_level:
        print(format_str%tuple_of_args)

class Fl_fmt:
    locale_set = 0
    locale_avail = 0

    def __init__(self,f):
        if not Fl_fmt.locale_set:
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.utf8')
                Fl_fmt.locale_avail = 1
            except:
                pass
            Fl_fmt.locale_set = 1
        self.f = f

    def __str__(self):
        if Fl_fmt.locale_avail:
            return locale.format("%.2f",self.f,grouping=pretty)
        else:
            return "%.2f"%self.f

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
            [ "home_val",    "Home Value"                            , "300000" , 100000 , 1000000 ,  1  ] ,
            [ "how_long",    "How long do you plan to hold the home" , "20"     ,      2 ,     100 ,  1  ] ,
            [ "mort_per",    "Mortgage percent"                      , "3"    ,    1.0 ,    25.0 ,  0  ] ,
            [ "down_pay",    "Down Payment %"                        , "0"     ,      1 ,     100 ,  1  ] ,
            [ "mort_ins",    "Mortgage insurance %"                  , "0.5"     ,      0.3 ,    1.2 ,  0  ] ,
            [ "mort_term",   "Mortgage Term"                         , "30"     ,      2 ,      40 ,  1  ] ,
            [ "price_appr",  "Price Appreciation %"                  , "6.0"    ,    1.0 ,    25.0 ,  0  ] ,
            [ "rent_appr",   "Rent Appreciation%"                    , "4.5"    ,    1.0 ,    25.0 ,  0  ] ,
            [ "inflation",   "Inflation %"                           , "4.2"    ,    1.0 ,    25.0 ,  0  ] ,
            [ "inv_rate",    "Investment Rate%"                      , "12.0"    ,    1.0 ,    25.0 ,  0  ] ,
            [ "prop_tax",    "Property Tax%"                         , "1.1"    ,    0.1 ,    10.0 ,  0  ] ,
            [ "joint",       "Joint"                                 , "yes"    ,   "yes",    "no" ,  2  ] ,
            [ "marg_rate",   "Marginal Rate%"                        , "22"     ,      0 ,    25.0 ,  0  ] ,
            [ "buy_loss",    "Buying loss%"                          , "1.5"    ,      0 ,    25.0 ,  0  ] ,
            [ "sell_loss",   "Selling loss%"                         , "6"      ,      0 ,    25.0 ,  0  ] ,
            [ "maint",       "Maintenance"                           , ".5"      ,    0.1 ,    10.0 ,  0  ] ,
            [ "own_ins",     "Owner Insurance"                       , "0.46"   ,    0.1 ,    10.0 ,  0  ] ,
            [ "month_comm",  "Monthly Common"                        , "250"    ,      0 ,    5000 ,  1  ] ,
            [ "rent_ins",    "Renter Insurance"                      , "0.5"    ,    0.1 ,    10.0 ,  0  ] ,
        ]

def parse_command_line_inputs():

    parser = argparse.ArgumentParser()
    for i in inputs:
        option = "--" + i[0]
        parser.add_argument(option, dest=i[0], help=i[1], default=i[2])
    parser.add_argument("--nopretty", action="store_true")
    parser.add_argument("-l", "--log_level", type=int)

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
    global set_verbose_level
    if parsed_args.log_level != None:
        set_verbose_level = parsed_args.log_level
        if set_verbose_level == 0:
            pretty = False

    return given_inputs


def compound_interest(p,n,r):
    '''
        Returns p * (1 + rate)^r
    '''
    rr = r/100.0
    return p * math.pow((1+rr), n)

def extrapolate_values(initial, years, rate):
    '''
        Given an initial value, and years and rate_of_increase, return
            years lenth list of values at end of each year.
    '''
    val_i = initial
    rr = rate/100.0
    result = []
    for i in range(years):
        val_i = val_i * ( 1 + rr)
        result.append(val_i)
    return result

def extrapolate_values_on_a_base(base, base_inc_rate, years, rate_on_base):
    '''
        Return list of values for n next years. (Result in years len long)
        That is, at end of each year, we have a value derived such that its is rate_on_base, where base is increasing at base_inc_rate.
    '''
    base_i = base
    rr = base_inc_rate/100.0
    vr = rate_on_base/100.0
    result = []
    for i in range(years):
        base_i = base_i * (1 + rr)
        value_i = base_i * vr
        result.append(value_i)
    return result

def principal_remaining_after(p, n, r, rem_years):
    rr = r / 1200.0
    nn = n*12
    rem_mths = rem_years * 12
    paid_mths = nn - rem_mths
    paid_prin = 0.0
    for i in range(1,paid_mths+1):
        pp = npf.ppmt(rr, i, nn, p)
        paid_prin += pp
    return (p*-1) - paid_prin


def get_a_renter_oppurtunity_cost(rent_guess, how_long, rent_appr, rent_ins):
    rental_values = extrapolate_values(rent_guess*12,how_long,rent_appr)
    renter_insur =  extrapolate_values_on_a_base(rent_guess*12, rent_appr,how_long,rent_ins)

    renter_oppurtunity_cost = 0.0
    renter_year_expense = []
    for i in range(inp['how_long']):
        renter_exp_for_this_year = rental_values[i] + renter_insur[i]
        renter_year_expense.append(renter_exp_for_this_year)
        years_left = inp['how_long'] - i
        renter_oppurtunity_cost += compound_interest(renter_exp_for_this_year, years_left, inp['inv_rate'])

    log_print(5,"Renter situation:")
    if set_verbose_level >= 5:
        for i in range(inp['how_long']):
            log_print(5,"year %d,  rent: %s rent_insur: %s net_yearly: %s",
                    (i,Fl_fmt(rental_values[i]),Fl_fmt(renter_insur[i]), Fl_fmt(renter_year_expense[i])))

    log_print(5, "oppurtunity_cost_for_renter at guess_rent:%s is: %s",
                    (Fl_fmt(rent_guess),Fl_fmt(renter_oppurtunity_cost)))

    return renter_oppurtunity_cost


inp = parse_command_line_inputs()
log_print(1,"Inputs\n%s"%inp)

#Find value of home at end of period
value_at_end = compound_interest(inp['home_val'], inp['how_long'], inp['price_appr'])
log_print(3,"Home value at end of %d years is %s",(inp['how_long'], Fl_fmt(value_at_end)))

sale_loss = value_at_end * (inp['sell_loss']/100.0)
log_print(3,"Sale-loss:%s",(Fl_fmt(sale_loss)))
value_at_end -= sale_loss

gains = value_at_end - inp['home_val']
if inp['how_long'] > 3:
    if inp['joint'] == "yes":
        deduct = 500000
    else:
        deduct = 250000
    gains -= deduct
if gains > 0:
    gains_loss = gains * (inp['marg_rate']/100.0)
    log_print(3,"Cap-Gains Loss:%s",(Fl_fmt(gains_loss)))
    value_at_end -= gains_loss

if inp['down_pay'] < 20:
    inp['mort_per'] += inp['mort_ins']

monthly_mortgage_rate = inp['mort_per'] / 1200.0
no_mortgage_months    = inp['mort_term'] * 12
downpay_value         = inp['home_val'] * (inp['down_pay']/100.0)
mortgage_value        = (inp['home_val'] - downpay_value) * -1
mortgate_pmt          = npf.pmt(monthly_mortgage_rate, no_mortgage_months, mortgage_value)
log_print(3,"Mortgage value is %s",Fl_fmt(mortgate_pmt))

if inp['how_long'] < inp['mort_term']:
    rem = inp['mort_term'] - inp['how_long']
    rem_prin = principal_remaining_after(mortgage_value, inp['mort_term'], inp['mort_per'], rem)
    log_print(3,"Remaining Principal to Pay:%s",(Fl_fmt(rem_prin)))
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
    exp = maintenances[i]
    exp += monthly_common_expenses[i]
    exp += owner_insur[i]
    mort_plus_prop = property_taxes[i] + mortgate_pmt * 12
    exp += mort_plus_prop
    if mort_plus_prop > tax_exception:
        tax_save = (mort_plus_prop - tax_exception) * (inp['marg_rate']/100.0)
        exp -= tax_save
    buyer_year_expense.append(exp)
    years_left = inp['how_long'] - i
    buyer_oppur_cost += compound_interest(exp, years_left, inp['inv_rate'])


log_print(4,"Buyer situation:")
for i in range(inp['how_long']):
    if (i < inp['mort_term']):
        mort_val = mortgate_pmt * 12
    else:
        mort_val = 0.0
    log_print(4,"year %d,  property_taxes: %s maintenances: %s monthly_common_expenses: %s  mortgage: %s net_yearly: %s",
                    (i,Fl_fmt(property_taxes[i]),Fl_fmt(maintenances[i]),Fl_fmt(monthly_common_expenses[i]),Fl_fmt(mort_val), Fl_fmt(buyer_year_expense[i])))


buy_loss = inp['home_val'] * (inp['buy_loss']/100.0)
initial_buy_expense = downpay_value + buy_loss
log_print(2,"Initial Buy Expense %s",Fl_fmt(initial_buy_expense))

buyer_oppur_cost += compound_interest(initial_buy_expense, inp['how_long'], inp['inv_rate'])
buyer_net_oppurtuinty = buyer_oppur_cost - value_at_end

log_print(2,"oppurtunity_cost_for_buyer: %s",Fl_fmt(buyer_oppur_cost))
log_print(2,"Final value end of %d years is %s",(inp['how_long'], Fl_fmt(value_at_end)))
log_print(2,"Net for buyer:%s",Fl_fmt(buyer_net_oppurtuinty))


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
        log_print(4,"left:%d, Took a guess of %s, and rent_cost:%s , diff: %s",(limit, Fl_fmt(rent_guess), Fl_fmt(renter_oppurtunity_cost), Fl_fmt(residual)))
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

log_print (1,"Start renting if rent value is less than:")
print("%s"%Fl_fmt(rent_guess))
