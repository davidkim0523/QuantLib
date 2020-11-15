import datetime
import QuantLib as ql
from SWAP_CURVE import GET_QUOTE, SWAP_CURVE

class IRS():
    def __init__(self, date, effective_date, maturity_date, irs_rate, notional, position, spread=0.0):
        
        # Initial Setup 1 : Date & Curve
        self.date = date
        self.curve = self.CURVE(self.date)
        
        # Initial Setup 2 : Instrument Info
        self.effective_date = ql.Date(effective_date.day, effective_date.month, effective_date.year)
        self.maturity_date = ql.Date(maturity_date.day, maturity_date.month, maturity_date.year)
        self.calendar = ql.UnitedStates()
        self.convention = ql.ModifiedFollowing
        self.day_counter = ql.Actual360()
        self.fixed_tenor = ql.Period(1, ql.Years)
        self.float_tenor = ql.Period(3, ql.Months)
        self.irs_rate = irs_rate
        self.notional = notional   
        self.spread = spread
        self.position = position
        
        # Pricing Results
        self.npv = self.PRICING(self.curve)
        self.delta = self.DELTA()
        self.theta = self.THETA()
        
    def CURVE(self, date):
        return SWAP_CURVE(date, GET_QUOTE(date))
    
    def PRICING(self, curve):
        # Yield Term-structure
        curve_handle = ql.YieldTermStructureHandle(curve)
        
        # USD 3M LIBOR
        float_index = ql.USDLibor(ql.Period(3, ql.Months), curve_handle)
        
        # Fixed Schedule
        fixedSchedule = ql.Schedule(self.effective_date,
                                    self.maturity_date,
                                    self.fixed_tenor,
                                    self.calendar,
                                    self.convention,
                                    self.convention,
                                    ql.DateGeneration.Backward,
                                    False)
        
        # Floating Schedule
        floatingSchedule = ql.Schedule(self.effective_date,
                                       self.maturity_date,
                                       self.float_tenor,
                                       self.calendar,
                                       self.convention,
                                       self.convention,
                                       ql.DateGeneration.Backward,
                                       False)        
        
        # Interes Rate Swap
        irs = ql.VanillaSwap(self.position,
                             self.notional,
                             fixedSchedule,
                             self.irs_rate,
                             self.day_counter,
                             floatingSchedule,
                             float_index,
                             self.spread,
                             self.day_counter)

        # Pricing Engine
        swapEngine = ql.DiscountingSwapEngine(curve_handle)  
        irs.setPricingEngine(swapEngine)
        
        npv = irs.NPV()
        
        return npv
        
    
    def DELTA(self):
        curve_handle = ql.YieldTermStructureHandle(self.curve)
        
        # 1bp
        basis_point = 0.0001
        
        # FRA price when 1bp up
        up_curve = ql.ZeroSpreadedTermStructure(curve_handle, ql.QuoteHandle(ql.SimpleQuote(basis_point)))
        up_irs = self.PRICING(up_curve)
        
        # FRA price when 1bp down
        down_curve = ql.ZeroSpreadedTermStructure(curve_handle, ql.QuoteHandle(ql.SimpleQuote(-basis_point)))
        down_irs = self.PRICING(down_curve)
        
        # DV01
        dv01 = (up_irs - down_irs) / 2
        
        return dv01
    
    def THETA(self):
        price_t0 = self.PRICING(self.CURVE(self.date))
        price_t1 = self.PRICING(self.CURVE(self.date + datetime.timedelta(days=1)))
        
        return price_t1 - price_t0

if __name__ == "__main__":

    # Today's Date
    todays_date = datetime.date(2020, 10, 9)
    
    # IRS Instrument Setup
    effective_date = datetime.date(2020, 10, 19)
    maturity_date = datetime.date(2022, 10, 19)
    position = ql.VanillaSwap.Payer
    irs_rate = 0.00218
    notional = 10000000
        
    # Build IRS object
    irs = IRS(todays_date,
              effective_date,
              maturity_date,
              irs_rate,
              notional,
              position)
    
    print("Price = {}".format(round(irs.npv, 4)))
    print("Delta = {}".format(round(irs.delta, 4)))
    print("Theta = {}".format(round(irs.theta, 4)))