import datetime
import QuantLib as ql
from SWAP_CURVE import GET_QUOTE, SWAP_CURVE

class FRA():
    def __init__(self, effective_date, maturity_date, position, fra_rate, notional):
        
        # Initial Setup 1 : Date & Curve
#        self.date = ql.Date(date.day, date.month, date.year)
#        ql.Settings.instance().evaluationDate = self.date
#        self.curve = ql.YieldTermStructureHandle(curve)
        
        # Initial Setup 2 : Instruments Info
        self.effective_date = ql.Date(effective_date.day, effective_date.month, effective_date.year)
        self.maturity_date = ql.Date(maturity_date.day, maturity_date.month, maturity_date.year)
        self.position = position
        self.fra_rate = fra_rate
        self.notional = notional
#        self.libor = ql.USDLibor(ql.Period(3, ql.Months), self.curve)

        # Pricing Results
#        self.npv = self.pricing(self.curve)
#        self.dv01 = self.dv01(self.curve)
#        self.theta = self.theta(self.curve)
        
    def pricing(self, date, curve):
        curve_handle = ql.YieldTermStructureHandle(curve)
        ql.Settings.instance().evaluationDate = date      
        libor = ql.USDLibor(ql.Period(3, ql.Months), curve_handle)
        # Pricing FRA
        fra = ql.ForwardRateAgreement(self.effective_date,
                                      self.maturity_date,
                                      self.position,
                                      self.fra_rate,
                                      self.notional,
                                      libor,
                                      curve_handle)
        
        npv = fra.NPV()
        
        return npv
    
    def dv01(self, date, curve):
        curve = ql.YieldTermStructureHandle(curve)
        
        # 1bp
        basis_point = 0.0001
        
        # FRA price when 1bp up
        up_curve = ql.ZeroSpreadedTermStructure(curve, ql.QuoteHandle(ql.SimpleQuote(basis_point)))
        #up_curve_handle = ql.YieldTermStructureHandle(up_curve)
        up_fra = self.pricing(date, up_curve)
        print(up_fra)
        # FRA price when 1bp down
        down_curve = ql.ZeroSpreadedTermStructure(curve, ql.QuoteHandle(ql.SimpleQuote(-basis_point)))
        #down_curve_handle = ql.YieldTermStructureHandle(down_curve)
        down_fra = self.pricing(date, down_curve)
        print(down_fra)
        # DV01
        dv01 = (up_fra - down_fra) / 2
        
        return dv01

    def theta(self, date, curve):
        
        price_t0 = self.pricing(date, curve)
        print(price_t0)
        
        price_t1 = self.pricing(date + 1, curve)
        print(price_t1)
        
        return price_t1 - price_t0
        
        
if __name__ == "__main__":

    # Today's Date
    todays_date = datetime.date(2020, 10, 9)
    
    # Build Curve
    curve = SWAP_CURVE(todays_date, GET_QUOTE(todays_date))
    
    todays_date = ql.Date(todays_date.day, todays_date.month, todays_date.year)
    
    # FRA Instrument Setup
    effective_date = datetime.date(2020, 10, 19)
    maturity_date = datetime.date(2020, 12, 15)
    fra_type = ql.Position.Long
    fra_rate = 0.0022
    notional = 10000000
    
    # Build FRA object
    fra = FRA(effective_date,
              maturity_date,
              fra_type,
              fra_rate,
              notional)
    
    print("Price = {}".format(round(fra.pricing(todays_date, curve), 4)))
    print("DV01 = {}".format(round(fra.dv01(todays_date, curve), 4)))
    print("Theta = {}".format(round(fra.theta(todays_date, curve), 4)))