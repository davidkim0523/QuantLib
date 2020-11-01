import datetime
import QuantLib as ql
from SWAP_CURVE import GET_QUOTE, SWAP_CURVE

class FRA():
    def __init__(self, date, curve, effective_date, maturity_date, position, fra_rate, notional):
        
        # Initial Setup 1 : Date & Curve
        self.date = ql.Date(date.day, date.month, date.year)
        ql.Settings.instance().evaluationDate = self.date
        self.curve_handle = ql.YieldTermStructureHandle(curve)
        
        # Initial Setup 2 : Instruments Info
        self.effective_date = ql.Date(effective_date.day, effective_date.month, effective_date.year)
        self.maturity_date = ql.Date(maturity_date.day, maturity_date.month, maturity_date.year)
        if position == 'Long':
            self.position = ql.Position.Long
        else:
            self.position = ql.Position.Short
        self.fra_rate = fra_rate
        self.notional = notional
        self.libor = ql.USDLibor(ql.Period(3, ql.Months), self.curve_handle)

        # Pricing Results
        self.npv = self.PRICING(self.curve)
        self.dv01 = self.DV01()
        self.theta = self.THETA()
    
    def PRICING(self):
        # Pricing FRA
        fra = ql.ForwardRateAgreement(self.effective_date,
                                      self.maturity_date,
                                      self.position,
                                      self.fra_rate,
                                      self.notional,
                                      self.libor,
                                      self.curve_handle)
        
        npv = fra.NPV()
        
        return npv
    
    def DV01(self):
        # 1bp
        basis_point = 0.0001
        
        # FRA price when 1bp up
        up_curve = ql.ZeroSpreadedTermStructure(self.curve_handle, ql.QuoteHandle(ql.SimpleQuote(basis_point)))
        up_curve_handle = ql.YieldTermStructureHandle(up_curve)
        self.curve_handle = up_curve_handle
        up_fra = self.PRICING()

        # FRA price when 1bp down
        down_curve = ql.ZeroSpreadedTermStructure(self.curve_handle, ql.QuoteHandle(ql.SimpleQuote(-basis_point)))
        down_curve_handle = ql.YieldTermStructureHandle(down_curve)
        self.curve_handle = down_curve_handle
        down_fra = self.PRICING()
        
        original_curve = ql.ZeroSpreadedTermStructure(self.curve_handle, ql.QuoteHandle(ql.SimpleQuote(basis_point)))
        original_curve_handle = ql.YieldTermStructureHandle(original_curve)
        self.curve_handle = original_curve_handle
        
        # DV01
        dv01 = (up_fra - down_fra) / 2
        
        return dv01
    
    def THETA(self):
        price_t0 = self.PRICING()
        print(price_t0)
        
        ql.Settings.instance().evaluationDate = self.date + ql.Period(1, ql.Days)
        price_t1 = self.PRICING()
        print(price_t1)
        
        ql.Settings.instance().evaluationDate = self.date
        
        return price_t1 - price_t0
    
        
if __name__ == "__main__":

    # Today's Date
    todays_date = datetime.date(2020, 10, 9)
    curve = SWAP_CURVE(todays_date, GET_QUOTE(todays_date))
    
    # FRA Instrument Setup
    effective_date = datetime.date(2020, 10, 19)
    maturity_date = datetime.date(2020, 12, 15)
    position = 'Long'
    fra_rate = 0.0022
    notional = 10000000
    
    # Build FRA object
    fra = FRA(todays_date,
              effective_date,
              maturity_date,
              position,
              fra_rate,
              notional)
    
    print("Price = {}".format(round(fra.npv, 4)))
    print("DV01 = {}".format(round(fra.dv01, 4)))
    print("Theta = {}".format(round(fra.theta, 4)))
    