import QuantExt as qe
from SWAP_CURVE import GET_QUOTE, SWAP_CURVE

class FXF():
    def __init__(self, todays_date, maturity_date, fx_spot, ccy1, ccy1_notional, ccy2, ccy2_notional, day_count):
        self.date = todays_date
        self.maturity_date = maturity_date
        
        self.curve = self.CURVE(self.date)
        
        self.spot_handle = qe.QuoteHandle(qe.SimpleQuote(fx_spot))
        self.ccy1 = ccy1
        self.ccy1_notional = ccy1_notional
        self.ccy2 = ccy2
        self.ccy2_notional = ccy2_notional
        
        self.day_count = day_count
        self.payCcy1 = False
        
    def CURVE(self, date):
        curve_handle = qe.YieldTermStructureHandle(SWAP_CURVE(date, GET_QUOTE(date)))
        
        return curve_handle
        
    def PRICING(self):
        curve_handle = self.CURVE(self.date)
        
        fxf = qe.FxForward(self.ccy1_notional,
                           self.ccy1,
                           self.ccy2_notional,
                           self.ccy2,
                           self.maturity_date,
                           self.payCcy1)

        # To-do : Dual Curve Import
        engine = qe.DiscountingFxForwardEngine(self.ccy1,
                                               curve_handle,
                                               self.ccy2,
                                               curve_handle,
                                               self.spot_handle)
        
        fxf.setPricingEngine(engine)
        
        npv = fxf.NPV()
        
        return npv

    def FX_DELTA(self):
        pass
    
    def CURVE_DELTA(self):
        pass
    
    def THETA(self):
        pass

if __name__ == "__main__":
    # market
    fx_spot = 1133.85
    eur_interest_rate = -0.00544
    krw_interest_rate = 0.00598
    forward_rate = 1150.0
    day_count = qe.ActualActual()
    
    # discount curves
    eur_curve = qe.FlatForward(todays_date,
                               eur_interest_rate,
                               day_count)
    krw_curve = qe.FlatForward(todays_date,
                               krw_interest_rate,
                               day_count)
    eur_curve_handle = qle.RelinkableYieldTermStructureHandle()
    krw_curve_handle = qle.RelinkableYieldTermStructureHandle()
    eur_curve_handle.linkTo(eur_curve)
    krw_curve_handle.linkTo(krw_curve)
    
    
    # FX Forward Instrument
    krw = qe.KRWCurrency()
    usd = qe.USDCurrency()
    maturity_date = qe.Date(11, 9, 2020)
    
    payCcy1 = False
    krw_notional = 7044000000
    usd_notional = krw_notional / forward_rate
    
    fxf = FXF()