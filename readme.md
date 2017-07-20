# Rent Vs Buy Calculator

This is my trial implementation of what is being done in this [web-page](https://www.nytimes.com/interactive/2014/upshot/buy-rent-calculator.html?abt=0002&abg=0)

You can invoke it with the following inputs and it will suggest the rent-value

``` sh
$ calculate.py
usage: calculate.py [-h] [--home_val HOME_VAL] [--how_long HOW_LONG]
                    [--mort_per MORT_PER] [--down_pay DOWN_PAY]
                    [--mort_term MORT_TERM] [--price_appr PRICE_APPR]
                    [--rent_appr RENT_APPR] [--inflation INFLATION]
                    [--inv_rate INV_RATE] [--prop_tax PROP_TAX]
                    [--joint JOINT] [--marg_rate MARG_RATE]
                    [--buy_loss BUY_LOSS] [--sell_loss SELL_LOSS]
                    [--maint MAINT] [--own_ins OWN_INS]
                    [--month_comm MONTH_COMM] [--rent_ins RENT_INS]
                    [--nopretty] [-l LOG_LEVEL]
$
```

Example invocation (Defaults are assumed if sth is not given):

```
$ calcluate.py
Inputs
{'rent_ins': 0.5, 'inv_rate': 8.0, 'home_val': 750000, 'joint': 'yes',
'sell_loss': 6.0, 'month_comm': 250, 'maint': 1.0, 'own_ins': 0.46,
'mort_per': 4.0, 'down_pay': 10, 'prop_tax': 0.8, 'mort_term': 30,
'inflation': 3.0, 'price_appr': 4.0, 'buy_loss': 1.5, 'rent_appr': 4.5,
'marg_rate': 25.0, 'how_long': 30}
Start renting if rent value is less than:
2,452.31
$
```

You can fill in any value though. Eg:

```
$ for i in $(seq 100000 100000 1000000 ); do \
        rent=$(./calculate.py --home_val $i -l 0); \
        echo "Breakeven Rent for $i is $rent" ; done
Breakeven Rent for 100000 is 563.37
Breakeven Rent for 200000 is 914.05
Breakeven Rent for 300000 is 1194.63
Breakeven Rent for 400000 is 1474.11
Breakeven Rent for 500000 is 1753.60
Breakeven Rent for 600000 is 2033.08
Breakeven Rent for 700000 is 2312.57
Breakeven Rent for 800000 is 2592.05
Breakeven Rent for 900000 is 2871.54
Breakeven Rent for 1000000 is 3151.03
$
```

# How are the calculations done

This is my implementation after a best effort (read, unreliable) understanding
of what the web-page does.

We get all inputs. We take the buyer-case first. Buyer spends some initial
values (buying costs, down-payment) and spends over the period (mortgage costs,
maintenance costs). These costs are inflation adjusted to their
amounts. These are then considered invested from that point till end of period.
These expenses are the oppurtunity_ cost for the buyer. At the end of period,
buyer is assumed to sell the house. After discounting all
sale-losses(capital gains, sale-payments), we discount this cost from the
oppurtunity_ cost. This is the net oppurtunity_ cost the buyer incurs by
buying the house.

We then take a rental-guess, and assuming this rental guess, do the same
oppurtunity_ cost calculation for the renter. The renter's expenses are his
rents and other payments. We then try to match the renter's oppurtunity_ cost
to the seller's oppurtunity_ cost. If the renter's cost exceeds, we decrese
rent, if its lesser, we increase rent, thus honing in to the break even value.


