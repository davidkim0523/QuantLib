import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

import QuantLib as ql
import xlwings as xw

# Get Quote from Excel File
def GET_QUOTE(today, ticker):
    
    # Import Data from Excel
    xw.App(visible=False)   
    wb = xw.Book(r'./FX_CURVE.xlsx')
    
    if ticker == 'USD':
        sht = wb.sheets('USDIRS')
        curve = sht.range('A1:D25').options(pd.DataFrame).value
        
    elif ticker == 'KRW':
        sht = wb.sheets('KRWCCS')
        curve = sht.range('A1:D15').options(pd.DataFrame).value
    
    wb.close()
    
    # Pre-process DataFrame
    curve['DaysToMaturity'] = np.nan
    curve['Maturity'] = pd.to_datetime(curve['Maturity']).dt.date
    
    for tenor in curve.index:
        curve.loc[tenor, 'DaysToMaturity'] = (curve.loc[tenor, 'Maturity'] - today).days
    
    return curve

# Construct USD IRS Curve
def USDIRS_CURVE(today, quote):
    
    # Divide DataFrame into 3 Parts
    depo = quote[quote['InstType'] == 'CASH']
    futures = quote[quote['InstType'] == 'FUTURE']
    swap = quote[quote['InstType'] == 'SWAP']

    # Set Evaluation Date
    todays_date = ql.Date(today.day, today.month, today.year)
    ql.Settings.instance().evaluationDate = todays_date
    
    # Market Conventions
    calendar = ql.UnitedStates()
    dayCounter = ql.Actual360()
    convention = ql.ModifiedFollowing
    settlementDays = 2
    frequency = ql.Semiannual
        
    # Build Rate Helpers
    # 1. Deposit Rate Helper
    depositHelpers = [ql.DepositRateHelper(ql.QuoteHandle(ql.SimpleQuote(rate / 100)),
                                           ql.Period(int(day), ql.Days),
                                           settlementDays,
                                           calendar,
                                           convention,
                                           False,
                                           dayCounter)
                      for day, rate in zip(depo['DaysToMaturity'], depo['Market.Mid'])]
    
    # 2. Futures Rate Helper
    futuresHelpers = []
    for i, price in enumerate(futures['Market.Mid']):
        iborStartDate = ql.Date(futures['Maturity'][i].day,
                                futures['Maturity'][i].month,
                                futures['Maturity'][i].year)
        
        futuresHelper = ql.FuturesRateHelper(ql.QuoteHandle(ql.SimpleQuote(price)),
                                             iborStartDate,
                                             3,
                                             calendar,
                                             convention,
                                             False,
                                             dayCounter)
        futuresHelpers.append(futuresHelper)
    
    # 3. Swap Rate Helper
    swapHelpers = [ql.SwapRateHelper(ql.QuoteHandle(ql.SimpleQuote(rate / 100)),
                                     ql.Period(int(day), ql.Days),
                                     calendar,
                                     frequency,
                                     convention,
                                     dayCounter,
                                     ql.Euribor3M())
                   for day, rate in zip(swap['DaysToMaturity'], swap['Market.Mid'])]
    
    # Curve Construction
    helpers = depositHelpers + futuresHelpers + swapHelpers
    depoFuturesSwapCurve = ql.PiecewiseLinearZero(todays_date, helpers, dayCounter)
        
    return depoFuturesSwapCurve

def KRWCCS_CURVE(today, quote):
    
    # Divide DataFrame into 3 Parts
    depo = quote[quote['InstType'] == 'CASH']
    swap = quote[quote['InstType'] == 'SWAP']

    # Set Evaluation Date
    todays_date = ql.Date(today.day, today.month, today.year)
    ql.Settings.instance().evaluationDate = todays_date
    
    # Market Conventions
    calendar = ql.SouthKorea()
    dayCounter = ql.Actual365Fixed()
    convention = ql.ModifiedFollowing
    settlementDays = 2
    frequency = ql.Semiannual
        
    # Build Rate Helpers
    # 1. Deposit Rate Helper
    depositHelpers = [ql.DepositRateHelper(ql.QuoteHandle(ql.SimpleQuote(rate / 100)),
                                           ql.Period(int(day), ql.Days),
                                           settlementDays,
                                           calendar,
                                           convention,
                                           False,
                                           dayCounter)
                      for day, rate in zip(depo['DaysToMaturity'], depo['Market.Mid'])]
    
    # 2. Swap Rate Helper
    swapHelpers = [ql.SwapRateHelper(ql.QuoteHandle(ql.SimpleQuote(rate / 100)),
                                     ql.Period(int(day), ql.Days),
                                     calendar,
                                     frequency,
                                     convention,
                                     dayCounter,
                                     ql.Euribor3M())
                   for day, rate in zip(swap['DaysToMaturity'], swap['Market.Mid'])]
    
    # Curve Construction
    helpers = depositHelpers + swapHelpers
    depoFuturesSwapCurve = ql.PiecewiseLinearZero(todays_date, helpers, dayCounter)
        
    return depoFuturesSwapCurve

def DISCOUNT_FACTOR(date, curve):
    date = ql.Date(date.day, date.month, date.year)
    return curve.discount(date)

def ZERO_RATE(date, curve):
    date = ql.Date(date.day, date.month, date.year)
    day_counter = ql.Actual360()
    compounding = ql.Compounded
    freq = ql.Continuous
    zero_rate = curve.zeroRate(date,
                               day_counter,
                               compounding,
                               freq).rate()
    return zero_rate

def FORWARD_RATE(date, curve):
    date = ql.Date(date.day, date.month, date.year)
    day_counter = ql.Actual360()
    compounding = ql.Compounded
    freq = ql.Continuous
    forward_rate = curve.forwardRate(date,
                                     date,
                                     day_counter,
                                     compounding,
                                     freq,
                                     True).rate()
    return forward_rate


if __name__ == "__main__":
    
    # Today's Date
    todays_date = datetime.date(2020, 10, 9)

    # Get Quote & Build Swap Curve
    quote = GET_QUOTE(todays_date, 'KRW')
    curve = USDIRS_CURVE(todays_date, quote)  
    
    # Calculate Discount Factor / Zero Rate / Forward Rate
    quote['discount factor'] = np.nan
    quote['zero rate'] = np.nan
    quote['forward rate'] = np.nan
    
    for tenor, date in zip(quote.index, quote['Maturity']):
        quote.loc[tenor, 'discount factor'] = DISCOUNT_FACTOR(date, curve)
        quote.loc[tenor, 'zero rate'] = ZERO_RATE(date, curve) * 100
        quote.loc[tenor, 'forward rate'] = FORWARD_RATE(date, curve) * 100
        
    # Print the Result
    print(quote[['discount factor', 'zero rate', 'forward rate']])
    
    # Plot the Result
    plt.figure(figsize=(16, 8))
    plt.plot(quote['zero rate'], 'b.-', label='Zero Curve')
    plt.plot(quote['forward rate'], 'g.-', label='Forward Curve')
    plt.title('Zero & Forward Curve', loc='center')
    plt.legend()
    plt.xlabel('Maturity')
    plt.ylabel('Interest Rate')
    
    plt.figure(figsize=(16, 8))
    plt.plot(quote['discount factor'], 'r.-', label='Discount Curve')
    plt.title('Discount Curve', loc='center')
    plt.legend()
    plt.xlabel('Maturity')
    plt.ylabel('Discount Factor')