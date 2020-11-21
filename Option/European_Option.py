import QuantLib as ql

valuationDate = ql.Date(20, 11, 2020)
ql.Settings.instance().evaluationDate = valuationDate

calendar = ql.SouthKorea()
dayCount = ql.ActualActual()

# Simple Quote Objects
underlying_qt = ql.SimpleQuote(270.48)      # Underlying Price
dividend_qt = ql.SimpleQuote(0.0)           # Dividend Yield
riskfreerate_qt = ql.SimpleQuote(0.01)      # Risk-free Rate
volatility_qt = ql.SimpleQuote(0.13)        # Volatility

# Quote Handle Objects
u_qhd = ql.QuoteHandle(underlying_qt)
q_qhd = ql.QuoteHandle(dividend_qt)
r_qhd = ql.QuoteHandle(riskfreerate_qt)
v_qhd = ql.QuoteHandle(volatility_qt)

# Term-Structure Objects
r_ts = ql.FlatForward(valuationDate, r_qhd, dayCount)
d_ts = ql.FlatForward(valuationDate, q_qhd, dayCount)
v_ts = ql.BlackConstantVol(valuationDate, calendar, v_qhd, dayCount)

# Term-Structure Handle Objects
r_thd = ql.YieldTermStructureHandle(r_ts)
d_thd = ql.YieldTermStructureHandle(d_ts)
v_thd = ql.BlackVolTermStructureHandle(v_ts)

# Process & Engine
process = ql.BlackScholesMertonProcess(u_qhd, d_thd, r_thd, v_thd)
engine = ql.AnalyticEuropeanEngine(process)

# Option Objects
option_type = ql.Option.Call
strikePrice = 272
expiryDate = ql.Date(12, 12, 2019)
exercise = ql.EuropeanExercise(expiryDate)
payoff = ql.PlainVanillaPayoff(option_type, strikePrice)
option = ql.VanillaOption(payoff, exercise)

# Pricing
option.setPricingEngine(engine)

# Price & Greeks Results
print('Option Premium = ', round(option.NPV(), 2))          # option premium
print('Option Delta = ', round(option.delta(), 4))          # delta
print('Option Gamma = ', round(option.gamma(), 4))          # gamma
print('Option Theta = ', round(option.thetaPerDay(), 4))    # theta
print('Option Vega = ', round(option.vega() / 100, 4))      # vega
print('Option Rho = ', round(option.rho() / 100, 4))        # rho
print('\n')

# Automatic Re-Pricing
underlying_qt.setValue(275)
print('Option Premium = ', round(option.NPV(), 2))          # option premium
print('Option Delta = ', round(option.delta(), 4))          # delta
print('Option Gamma = ', round(option.gamma(), 4))          # gamma
print('Option Theta = ', round(option.thetaPerDay(), 4))    # theta
print('Option Vega = ', round(option.vega() / 100, 4))      # vega
print('Option Rho = ', round(option.rho() / 100, 4))        # rho
print('\n')

# Implied Volatility
underlying_qt.setValue(270.48)
mkt_price = 8.21
implied_volatility = option.impliedVolatility(mkt_price, process)
volatility_qt.setValue(implied_volatility)
print('Option Premium = ', round(option.NPV(), 2))          # option premium
print('Option Delta = ', round(option.delta(), 4))          # delta
print('Option Gamma = ', round(option.gamma(), 4))          # gamma
print('Option Theta = ', round(option.thetaPerDay(), 4))    # theta
print('Option Vega = ', round(option.vega() / 100, 4))      # vega
print('Option Rho = ', round(option.rho() / 100, 4))        # rho
print('\n')