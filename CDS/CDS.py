import datetime
import QuantLib as ql
from SWAP_CURVE import GET_QUOTE, SWAP_CURVE

# Today's Date
todaysDate = datetime.date(2020, 10, 8)
curve = SWAP_CURVE(todaysDate, GET_QUOTE(todaysDate))
curve_handle = ql.YieldTermStructureHandle(curve)

todaysDate = ql.Date(todaysDate.day, todaysDate.month, todaysDate.year)

calendar = ql.UnitedStates()

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
                                 0, # >>> contract cannot start before accrual
                                 calendar,
                                 ql.Quarterly,
                                 ql.ModifiedFollowing,
                                 ql.DateGeneration.TwentiethIMM,
                                 ql.Actual360(),
                                 recovery_rate,
                                 curve_handle)
                for s, tenor in zip(quoted_spreads, tenors)]

hazard_curve = ql.PiecewiseFlatHazardRate(todaysDate,
                                          cdsHelpers,
                                          ql.Actual360())


#print(hazard_curve.survivalProbability(todaysDate + ql.Period("1Y")), 0.9704)


# ### Reprice instruments

notional = 10000000.0
probability = ql.DefaultProbabilityTermStructureHandle(hazard_curve)

# We'll create a cds for every maturity:

maturity = ql.Date(26, 11, 2025)
spread = 21.755

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
                           ql.Actual360(),
                           True,
                           True,
                           todaysDate)

engine = ql.MidPointCdsEngine(probability, recovery_rate, curve_handle)
cds.setPricingEngine(engine)

print(cds.fairSpread())
print(cds.NPV())

#print(cds.runningSpread())
print(cds.fairUpfront())
