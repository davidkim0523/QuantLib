import QuantLib as ql
from CDS_CURVE import *

class CDS():
    def __init__(self):
        pass
    
    def DISCOUNT_CURVE(self):
        pass
    
    def CDS_CURVE(self):
        pass
    
    def PRICING(self):
        pass
    
    def IR_DELTA(self):
        pass
    
    def CREDIT_DELTA(self):
        pass
    
    def THETA(self):
        pass


calendar = ql.UnitedStates()

# Today's Date
todaysDate = ql.Date(1, 12, 2020)
ql.Settings.instance().setEvaluationDate = todaysDate



# ### Reprice instruments

notional = 10000000.0
probability = ql.DefaultProbabilityTermStructureHandle(hazard_curve)

# We'll create a cds for every maturity:

maturity = ql.Date(21, 11, 2025)
spread = 21.4918

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
                           True)

engine = ql.MidPointCdsEngine(probability, recovery_rate, discountCurve)
cds.setPricingEngine(engine)

print(cds.fairSpread())
print(cds.NPV())

#print(cds.runningSpread())
print(cds.fairUpfront())

print(cds.conventionalSpread(0.4, discountCurve, ql.Actual360()))
print(cds.couponLegNPV())
print(cds.defaultLegNPV())

