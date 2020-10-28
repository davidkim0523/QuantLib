import datetime
import QuantLib as ql
from SWAP_CURVE import GET_QUOTE, SWAP_CURVE

class FRA():
    def __init__(self, todays_date, effective_date, maturity_date, position, fra_rate, notional):
        
        # Initial Setup 1 : Date & Curve
        self.date = todays_date
        self.curve = self.CURVE(self.date)
        
        # Initial Setup 2 : Instruments Info
        self.effective_date = ql.Date(effective_date.day, effective_date.month, effective_date.year)
        self.maturity_date = ql.Date(maturity_date.day, maturity_date.month, maturity_date.year)
        if position == 'Long':
            self.position = ql.Position.Long
        else:
            self.position = ql.Position.Short
        self.fra_rate = fra_rate
        self.notional = notional

        # Pricing Results
        self.npv = self.PRICING(self.curve)
        self.dv01 = self.DV01()
        self.theta = self.THETA()
        
    def CURVE(self, date):
        return SWAP_CURVE(date, GET_QUOTE(date))
    
    def HANDLER(self, curve):
        return ql.YieldTermStructureHandle(curve)

    def PRICING(self, curve):
        curve_handle = ql.YieldTermStructureHandle(curve)
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
    
    def DV01(self):
        curve_handle = self.HANDLER(self.curve)
        
        # 1bp
        basis_point = 0.0001
        
        # FRA price when 1bp up
        up_curve = ql.ZeroSpreadedTermStructure(curve_handle, ql.QuoteHandle(ql.SimpleQuote(basis_point)))
        #up_curve_handle = ql.YieldTermStructureHandle(up_curve)
        up_fra = self.PRICING(up_curve)

        # FRA price when 1bp down
        down_curve = ql.ZeroSpreadedTermStructure(curve_handle, ql.QuoteHandle(ql.SimpleQuote(-basis_point)))
        #down_curve_handle = ql.YieldTermStructureHandle(down_curve)
        down_fra = self.PRICING(down_curve)

        # DV01
        dv01 = (up_fra - down_fra) / 2
        
        return dv01
    
    def THETA(self):
        price_t0 = self.PRICING(self.CURVE(self.date))
        print(price_t0)
        
        price_t1 = self.PRICING(self.CURVE(self.date + datetime.timedelta(days=1)))
        print(price_t1)
        
        return price_t1 - price_t0
    
        
if __name__ == "__main__":

    # Today's Date
    todays_date = datetime.date(2020, 10, 9)
            
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
    