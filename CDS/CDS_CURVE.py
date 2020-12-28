import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

import QuantLib as ql
import xlwings as xw

# Get IRS Quote from Excel File
def GET_IRS_QUOTE(today):
    
    # Import Data from Excel
    xw.App(visible=False)
    wb = xw.Book(r'./Data.xlsb')
    sht = wb.sheets('USDIRS')
    curve = sht.range('A1:D20').options(pd.DataFrame).value
    wb.close()
    
    # Pre-process DataFrame
    curve['DaysToMaturity'] = np.nan
    curve['Maturity'] = pd.to_datetime(curve['Maturity']).dt.date
    
    for tenor in curve.index:
        curve.loc[tenor, 'DaysToMaturity'] = (curve.loc[tenor, 'Maturity'] - today).days
    
    return curve

# Get CDS Quote from Excel File
def GET_CDS_QUOTE(today):
    
    # Import Data from Excel
    xw.App(visible=False)
    wb = xw.Book(r'./Data.xlsb')
    sht = wb.sheets('ROKCDS')
    curve = sht.range('A1:C9').options(pd.DataFrame).value
    wb.close()
    
    # Pre-process DataFrame
    curve['DaysToMaturity'] = np.nan
    curve['Maturity'] = pd.to_datetime(curve['Maturity']).dt.date
    
    for tenor in curve.index:
        curve.loc[tenor, 'DaysToMaturity'] = (curve.loc[tenor, 'Maturity'] - today).days
    
    return curve

# Construct IRS Curve
def SWAP_CURVE(today, quote):
    
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

# Construct CDS Curve
def CDS_CURVE(today, cds_quote, discount_curve):
    # Set Evaluation Date
    todays_date = ql.Date(today.day, today.month, today.year)
    ql.Settings.instance().evaluationDate = todays_date
    
    # Tenors
    tenors = [ql.Period(6, ql.Months),
              ql.Period(1, ql.Years),
              ql.Period(2, ql.Years),
              ql.Period(3, ql.Years),
              ql.Period(4, ql.Years),
              ql.Period(5, ql.Years),
              ql.Period(7, ql.Years),
              ql.Period(10, ql.Years)]
    
    # Market Conventions
    settlement_days = 2
    calendar = ql.UnitedStates()
    recovery_rate = 0.4
    frequency = ql.Quarterly
    convention = ql.ModifiedFollowing
    date_generation = ql.DateGeneration.CDS
    day_count = ql.Actual360()
    
    cdsHelpers = [ql.SpreadCdsHelper(ql.QuoteHandle(ql.SimpleQuote(spread / 10000)),
                                     tenor,
                                     settlement_days,
                                     calendar,
                                     frequency,
                                     convention,
                                     date_generation,
                                     day_count,
                                     recovery_rate,
                                     ql.YieldTermStructureHandle(discount_curve))
                  for spread, tenor in zip(cds_quote['Market.Mid'], tenors)]
    
    hazard_curve = ql.PiecewiseFlatHazardRate(todays_date,
                                              cdsHelpers,
                                              day_count)
    
    
    return hazard_curve

def DEFAULT_PROB(date, curve):
    date = ql.Date(date.day, date.month, date.year)
    
    default_prob = curve.defaultProbability(date)
    
    return default_prob
    
def SURVIVAL_PROB(date, curve):
    date = ql.Date(date.day, date.month, date.year)
    
    survival_prob = curve.survivalProbability(date)
    
    return survival_prob

if __name__ == "__main__":
    
    # Today's Date
    todays_date = datetime.date(2020, 12, 11)

    # Get Quote & Build Swap Curve
    irs_quote = GET_IRS_QUOTE(todays_date)
    cds_quote = GET_CDS_QUOTE(todays_date)
    discount_curve = SWAP_CURVE(todays_date, irs_quote)  
    hazard_curve = CDS_CURVE(todays_date, cds_quote, discount_curve)
    
    # Calculate Default Probability & Survival Probability
    cds_quote['default prob'] = np.nan
    cds_quote['survival prob'] = np.nan
    
    for tenor, date in zip(cds_quote.index, cds_quote['Maturity']):
        cds_quote.loc[tenor, 'default prob'] = DEFAULT_PROB(date, hazard_curve)
        cds_quote.loc[tenor, 'survival prob'] = SURVIVAL_PROB(date, hazard_curve)
        
    # Print the Result
    print(cds_quote[['default prob', 'survival prob']])
    
    # Plot the Result
    plt.figure(figsize=(16, 8))
    plt.plot(cds_quote['default prob'], 'b.-', label='Default Probability')
    plt.title('Default Probability', loc='center')
    plt.legend()
    plt.xlabel('Maturity')
    plt.ylabel('%')
    
    plt.figure(figsize=(16, 8))
    plt.plot(cds_quote['survival prob'], 'g.-', label='Survival Probability')
    plt.title('Survival Probability', loc='center')
    plt.legend()
    plt.xlabel('Maturity')
    plt.ylabel('%')