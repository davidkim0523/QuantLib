import QuantLib as ql
import xlwings as xw
import pandas as pd
import datetime

# Get Quote from Bloomberg
def GET_QUOTE(ticker):
    xw.App(visible=False)
    wb = xw.Book(r'Z:\PL\SWAP_CURVE.xlsb')
    
    if ticker == 'USDIRS':
        sht = wb.sheets(ticker)
        curve = sht.range('A1:E25').options(pd.DataFrame).value
        
    elif ticker == 'KRWIRS':
        sht = wb.sheets(ticker)
        curve = sht.range('A1:D15').options(pd.DataFrame).value
        
    elif ticker == 'KRWCCS':
        sht = wb.sheets(ticker)
        curve = sht.range('A1:D15').options(pd.DataFrame).value
    
    wb.close()
    return curve 

# Construct IRS Curve
def CURVE(today, ticker, quote):

    depo = quote[quote['InstType'] == 'CASH']
    futures = quote[quote['InstType'] == 'FUTURE']
    swap = quote[quote['InstType'] == 'SWAP']

    todays_date = ql.Date(today.day, today.month, today.year)
    ql.Settings.instance().evaluationDate = todays_date
    
    if ticker == 'USDIRS':
        calendar = ql.UnitedStates()
        dayCounter = ql.Actual360()
        adjustment = ql.ModifiedFollowing
        settlementDays = 2
        frequency = ql.Semiannual

    elif ticker == 'KRWIRS':
        calendar = ql.SouthKorea()
        dayCounter = ql.Actual365Fixed()
        adjustment = ql.ModifiedFollowing
        settlementDays = 2
        frequency = ql.Quarterly
        
    # Build Rate Helpers
    # 1. Deposit Rate Helper
    depositHelpers = [ql.DepositRateHelper(ql.QuoteHandle(ql.SimpleQuote(rate / 100)),
                                           ql.Period(int(day), ql.Days),
                                           settlementDays,
                                           calendar,
                                           adjustment,
                                           False,
                                           dayCounter)
                      for day, rate in zip(depo['DaysToMaturity'], depo['Market.Mid'])]
    
    # 2. Fra Rate Helper
    futuresHelpers = []
    for i, price in enumerate(futures['Market.Mid']):
        iborStartDate = ql.Date(futures['Maturity'][i].day,
                                futures['Maturity'][i].month,
                                futures['Maturity'][i].year)
        
        futuresHelper = ql.FuturesRateHelper(ql.QuoteHandle(ql.SimpleQuote(price)),
                                             iborStartDate,
                                             3,
                                             calendar,
                                             adjustment,
                                             False,
                                             dayCounter)
        
        futuresHelpers.append(futuresHelper)
    
    # 3. Swap Rate Helper
    swapHelpers = [ql.SwapRateHelper(ql.QuoteHandle(ql.SimpleQuote(rate / 100)),
                                     ql.Period(int(day), ql.Days),
                                     calendar,
                                     frequency,
                                     adjustment,
                                     dayCounter,
                                     ql.Euribor3M())
                   for day, rate in zip(swap['DaysToMaturity'], swap['Market.Mid'])]
    
    # Curve Construction
    helpers = depositHelpers + futuresHelpers + swapHelpers
    depoFuturesSwapCurve = ql.PiecewiseLinearZero(todays_date, helpers, dayCounter)
        
    return depoFuturesSwapCurve


# Pricing Swap Contract
def IRS(ticker, notional, effective_date, maturity_date, position, fixed_rate, curve, spread=0):
        
    # term structure handles
    discountTermStructure = ql.RelinkableYieldTermStructureHandle()
    forecastTermStructure = ql.RelinkableYieldTermStructureHandle()
    
    discountTermStructure.linkTo(curve)
    forecastTermStructure.linkTo(curve)     
    
    effective_date = ql.Date(effective_date.day, effective_date.month, effective_date.year)
    maturity_date = ql.Date(maturity_date.day, maturity_date.month, maturity_date.year)

    if position == 'Pay':
        position = ql.VanillaSwap.Payer
    elif position == 'Rcv':
        position = ql.VanillaSwap.Receiver

    if ticker == 'USDIRS':
        calendar = ql.UnitedStates()
        
        # Fixed Leg
        fixedLegAdjustment = ql.ModifiedFollowing
        fixedLegDayCounter = ql.Thirty360()
        fixedLegTenor = ql.Period(3,ql.Months)
        
        # Floating Leg
        usd_libor = ql.USDLibor(ql.Period(3, ql.Months), forecastTermStructure)
#        usd_libor.addFixing(ql.Date(16, 3, 2020), 0.088938)
        floatingLegAdjustment = ql.ModifiedFollowing
        floatingLegDayCounter = ql.Actual360()
        floatingLegTenor = ql.Period(3,ql.Months)
        
      
    elif ticker == 'KRWIRS':
        calendar = ql.SouthKorea()
        
        # Fixed Leg
        fixedLegAdjustment = ql.ModifiedFollowing
        fixedLegDayCounter = ql.Actual365Fixed()
        fixedLegTenor = ql.Period(3,ql.Months)
        
        # Floating Leg
        index = ql.USDLibor(ql.Period(3, ql.Months), forecastTermStructure)
        floatingLegAdjustment = ql.ModifiedFollowing
        floatingLegDayCounter = ql.Actual365Fixed()
        floatingLegTenor = ql.Period(3,ql.Months)
        
        
    # Fixed Schedule
    fixedSchedule = ql.Schedule(effective_date,
                                maturity_date,
                                fixedLegTenor,
                                calendar,
                                fixedLegAdjustment,
                                fixedLegAdjustment,
                                ql.DateGeneration.Forward,
                                False)
    
    # Floating Schedule
    floatingSchedule = ql.Schedule(effective_date,
                                   maturity_date,
                                   floatingLegTenor,
                                   calendar,
                                   floatingLegAdjustment,
                                   floatingLegAdjustment,
                                   ql.DateGeneration.Forward,
                                   False)
    
    # Plain Vanilla Swap
    if ticker == "USDIRS":
        index = usd_libor
    
    irs = ql.VanillaSwap(position,
                         notional,
                         fixedSchedule,
                         fixed_rate,
                         fixedLegDayCounter,
                         floatingSchedule,
                         index,
                         spread,
                         floatingLegDayCounter)

    # Pricing Engine
    swapEngine = ql.DiscountingSwapEngine(discountTermStructure)  
    irs.setPricingEngine(swapEngine)
    
    return irs

def PRICER(curve, product):
    # term structure handles
    discountTermStructure = ql.RelinkableYieldTermStructureHandle()
    discountTermStructure.linkTo(curve)
    
    swapEngine = ql.DiscountingSwapEngine(discountTermStructure)
    product.setPricingEngine(swapEngine)
    
    return product

if __name__ == "__main__":
    todays_date = datetime.date.today()
    ticker = 'USDIRS'
    position = 'Pay'
    notional = 10000000
    effective_date = datetime.date(2020, 9, 25)
    maturity_date = datetime.date(2025, 9, 25)
    fixed_rate = 0.32795 / 100
    
    quote = GET_QUOTE(ticker)
    curve = CURVE(todays_date, ticker, quote)  
    irs = IRS(ticker, notional, effective_date, maturity_date, position, fixed_rate, curve)
    irs_pricer = PRICER(curve, irs)
    
    print(irs_pricer.NPV())