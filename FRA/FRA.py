import datetime
import QuantLib as ql
from SWAP_CURVE import GET_QUOTE, SWAP_CURVE

class FRA():
    def __init__(self, date, curve, effective_date, maturity_date, fra_type, fra_rate, notional):
        
        # Initial Setup
        self.date = ql.Date(date.day, date.month, date.year)
        ql.Settings.instance().evaluationDate = self.date
        self.curve = ql.YieldTermStructureHandle(curve)
        self.effective_date = ql.Date(effective_date.day, effective_date.month, effective_date.year)
        self.maturity_date = ql.Date(maturity_date.day, maturity_date.month, maturity_date.year)
        self.fra_type = fra_type
        self.fra_rate = fra_rate
        self.notional = notional
        self.libor = ql.USDLibor(ql.Period(3, ql.Months), self.curve)

        # Pricing Results
        self.npv = self.pricing(self.curve)
        self.dv01 = self.dv01(self.curve)
        
    def pricing(self, curve):
        
        # Pricing FRA
        fra = ql.ForwardRateAgreement(self.effective_date,
                                      self.maturity_date,
                                      self.fra_type,
                                      self.fra_rate,
                                      self.notional,
                                      self.libor,
                                      curve)
        
        npv = fra.NPV()
        
        return npv
    
    def dv01(self, curve):
        
        # 1bp
        basis_point = 0.0001
        
        # FRA price when 1bp up
        up_curve = ql.ZeroSpreadedTermStructure(curve, ql.QuoteHandle(ql.SimpleQuote(basis_point)))
        up_curve_handle = ql.YieldTermStructureHandle(up_curve)
        up_fra = self.pricing(up_curve_handle)
        
        # FRA price when 1bp down
        down_curve = ql.ZeroSpreadedTermStructure(curve, ql.QuoteHandle(ql.SimpleQuote(-basis_point)))
        down_curve_handle = ql.YieldTermStructureHandle(down_curve)
        down_fra = self.pricing(down_curve_handle)
        
        # DV01
        dv01 = (up_fra - down_fra) / 2
        
        return dv01



if __name__ == "__main__":

    # Today's Date
    todays_date = datetime.date(2020, 10, 9)
    
    # Build Curve
    curve = SWAP_CURVE(todays_date, GET_QUOTE(todays_date))
    
    # FRA Instrument Setup
    effective_date = datetime.date(2020, 10, 19)
    maturity_date = datetime.date(2020, 12, 15)
    fra_type = ql.Position.Long
    fra_rate = 0.0022
    notional = 10000000
    
    # Build FRA object
    fra = FRA(todays_date,
              curve,
              effective_date,
              maturity_date,
              fra_type,
              fra_rate,
              notional)
    
    print(fra.npv)
    print(fra.dv01)