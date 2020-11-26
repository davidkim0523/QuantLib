import QuantLib as ql

calendar = ql.UnitedStates()

# Today's Date
todaysDate = ql.Date(20, 11, 2020)
ql.Settings.instance().setEvaluationDate = todaysDate

# Swap Curve
dep_tenors = [1, 2, 3, 6, 12]
dep_quotes = [0.1455, 0.1761, 0.2126, 0.2555, 0.3386]
isdaRateHelpers = [ql.DepositRateHelper(ql.QuoteHandle(ql.SimpleQuote(dep_quotes[i] / 100)), 
                                        ql.Period(dep_tenors[i], ql.Months),
                                        2,
                                        calendar,
                                        ql.ModifiedFollowing,
                                        False,
                                        ql.Actual360())
                   for i in range(len(dep_tenors))]

swap_tenors = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]
swap_quotes = [0.2495,
               0.2988,
               0.3650,
               0.4500,
               0.5410,
               0.6305,
               0.7110,
               0.7858,
               0.8543,
               0.9680,
               1.0890,
               1.1933,
               1.2438,
               1.2602]

isda_ibor = ql.IborIndex('IsdaIbor',
                         ql.Period(3, ql.Months),
                         2,
                         ql.USDCurrency(),
                         calendar,
                         ql.ModifiedFollowing,
                         False,
                         ql.Actual360())

isdaRateHelpers = isdaRateHelpers + [ql.SwapRateHelper(ql.QuoteHandle(ql.SimpleQuote(swap_quotes[i] / 100)),
                                                       ql.Period(swap_tenors[i], ql.Years),
                                                       calendar,
                                                       ql.Semiannual,
                                                       ql.ModifiedFollowing,
                                                       ql.Thirty360(),
                                                       isda_ibor)
                                    for i in range(len(swap_tenors))]

discountCurve = ql.RelinkableYieldTermStructureHandle()
discountCurve.linkTo(ql.PiecewiseLinearZero(0,
                                            calendar,
                                            isdaRateHelpers,
                                            ql.Actual360()))

# Recovery Rate
recovery_rate = 0.4

# Market Quotes
quoted_spreads = [7.97,
                  8.29,
                  9.61,
                  11.23,
                  15.5,
                  21.751,
                  29.64,
                  41.66]

tenors = [ql.Period(6, ql.Months),
          ql.Period(1, ql.Years),
          ql.Period(2, ql.Years),
          ql.Period(3, ql.Years),
          ql.Period(4, ql.Years),
          ql.Period(5, ql.Years),
          ql.Period(7, ql.Years),
          ql.Period(10, ql.Years)]

maturities = [calendar.adjust(todaysDate + x, ql.Following) for x in tenors]

cdsHelpers = [ql.SpreadCdsHelper(ql.QuoteHandle(ql.SimpleQuote(s / 10000)),
                                 tenor,
                                 2,
                                 calendar,
                                 ql.Quarterly,
                                 ql.ModifiedFollowing,
                                 ql.DateGeneration.TwentiethIMM,
                                 ql.Actual360(),
                                 recovery_rate,
                                 discountCurve)
                for s, tenor in zip(quoted_spreads, tenors)]

hazard_curve = ql.PiecewiseFlatHazardRate(todaysDate,
                                          cdsHelpers,
                                          ql.Actual360())


#print(hazard_curve.survivalProbability(todaysDate + ql.Period("1Y")), 0.9704)


# ### Reprice instruments

notional = 10000000.0
probability = ql.DefaultProbabilityTermStructureHandle(hazard_curve)

# We'll create a cds for every maturity:

maturity = ql.Date(21, 11, 2025)
spread = 21.751

schedule = ql.Schedule(todaysDate,
                       maturity,
                       ql.Period(ql.Quarterly),
                       calendar,
                       ql.ModifiedFollowing,
                       ql.ModifiedFollowing,
                       ql.DateGeneration.TwentiethIMM,
                       False)

cds = ql.CreditDefaultSwap(ql.Protection.Buyer,
                           notional,
                           spread / 10000,
                           schedule,
                           ql.ModifiedFollowing,
                           ql.Actual360())

engine = ql.MidPointCdsEngine(probability, recovery_rate, discountCurve)
cds.setPricingEngine(engine)

print(cds.fairSpread())
print(cds.NPV())

#print(cds.runningSpread())
print(cds.fairUpfront())
