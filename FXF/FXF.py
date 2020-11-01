<<<<<<< HEAD
import datetime
import QuantExt as qe
from FX_CURVE import GET_QUOTE, USDIRS_CURVE, KRWCCS_CURVE

class FXF():
    def __init__(self, todays_date, maturity_date, fx_spot, ccy1, ccy1_notional, ccy2, ccy2_notional, day_count):
        
        # Initial Setup 1 - Date / Curves / Spot
        self.date = todays_date
        
        self.usd_curve = self.USD_CURVE(self.date)
        self.krw_curve = self.KRW_CURVE(self.date)
        
        self.spot_handle = qe.QuoteHandle(qe.SimpleQuote(fx_spot))
        
        # Initial Setup 2 - Instrument Info
        self.maturity_date = qe.Date(maturity_date.day, maturity_date.month, maturity_date.year)
=======
import QuantExt as qe
from SWAP_CURVE import GET_QUOTE, SWAP_CURVE

class FXF():
    def __init__(self, todays_date, maturity_date, fx_spot, ccy1, ccy1_notional, ccy2, ccy2_notional, day_count):
        self.date = todays_date
        self.maturity_date = maturity_date
        
        self.curve = self.CURVE(self.date)
        
        self.spot_handle = qe.QuoteHandle(qe.SimpleQuote(fx_spot))
>>>>>>> f47134ae5e5667ba85dd8d2bf1ce707a2b13370e
        self.ccy1 = ccy1
        self.ccy1_notional = ccy1_notional
        self.ccy2 = ccy2
        self.ccy2_notional = ccy2_notional
        
        self.day_count = day_count
        self.payCcy1 = False
        
<<<<<<< HEAD
        
        # Pricing Results
        self.npv = self.PRICING(self.usd_curve, self.krw_curve, self.spot_handle)
        self.fx_delta = self.FX_DELTA(fx_spot)
        self.usd_curve_delta = self.USD_CURVE_DELTA()
        self.krw_curve_delta = self.KRW_CURVE_DELTA()
        self.theta = self.THETA()
        
        
    def USD_CURVE(self, date):
        curve_handle = qe.YieldTermStructureHandle(USDIRS_CURVE(date, GET_QUOTE(date, 'USD')))
        return curve_handle
    
    def KRW_CURVE(self, date):
        curve_handle = qe.YieldTermStructureHandle(KRWCCS_CURVE(date, GET_QUOTE(date, 'KRW')))
        return curve_handle
        
    def PRICING(self, usd_curve, krw_curve, fx_spot):        
=======
    def CURVE(self, date):
        curve_handle = qe.YieldTermStructureHandle(SWAP_CURVE(date, GET_QUOTE(date)))
        
        return curve_handle
        
    def PRICING(self):
        curve_handle = self.CURVE(self.date)
        
>>>>>>> f47134ae5e5667ba85dd8d2bf1ce707a2b13370e
        fxf = qe.FxForward(self.ccy1_notional,
                           self.ccy1,
                           self.ccy2_notional,
                           self.ccy2,
                           self.maturity_date,
                           self.payCcy1)

        # To-do : Dual Curve Import
        engine = qe.DiscountingFxForwardEngine(self.ccy1,
<<<<<<< HEAD
                                               krw_curve,
                                               self.ccy2,
                                               usd_curve,
                                               fx_spot)
=======
                                               curve_handle,
                                               self.ccy2,
                                               curve_handle,
                                               self.spot_handle)
>>>>>>> f47134ae5e5667ba85dd8d2bf1ce707a2b13370e
        
        fxf.setPricingEngine(engine)
        
        npv = fxf.NPV()
        
        return npv

<<<<<<< HEAD
    def FX_DELTA(self, fx_spot):
        up_fx = fx_spot * 1.0001
        up_fx_handle = qe.QuoteHandle(qe.SimpleQuote(up_fx))
        up_fxf = self.PRICING(self.usd_curve, self.krw_curve, up_fx_handle)
        
        down_fx = fx_spot * 0.9999
        down_fx_handle = qe.QuoteHandle(qe.SimpleQuote(down_fx))
        down_fxf = self.PRICING(self.usd_curve, self.krw_curve, down_fx_handle)
        
        fx_delta = (up_fxf - down_fxf) / 2
        
        return fx_delta
    
    def USD_CURVE_DELTA(self):
        curve_handle = self.usd_curve
        
        # 1bp
        basis_point = 0.0001
        
        # FRA price when 1bp up
        up_curve = qe.ZeroSpreadedTermStructure(curve_handle, qe.QuoteHandle(qe.SimpleQuote(basis_point)))
        up_curve_handle = qe.YieldTermStructureHandle(up_curve)
        up_fxf = self.PRICING(up_curve_handle, self.krw_curve, self.spot_handle)
        print(up_fxf)
        
        # FRA price when 1bp down
        down_curve = qe.ZeroSpreadedTermStructure(curve_handle, qe.QuoteHandle(qe.SimpleQuote(-basis_point)))
        down_curve_handle = qe.YieldTermStructureHandle(down_curve)
        down_fxf = self.PRICING(down_curve_handle, self.krw_curve, self.spot_handle)
        print(down_fxf)

        # DV01
        dv01 = (up_fxf - down_fxf) / 2
        return dv01
    
    def KRW_CURVE_DELTA(self):
        curve_handle = self.krw_curve
        
        # 1bp
        basis_point = 0.0001
        
        # FRA price when 1bp up
        up_curve = qe.ZeroSpreadedTermStructure(curve_handle, qe.QuoteHandle(qe.SimpleQuote(basis_point)))
        up_curve_handle = qe.YieldTermStructureHandle(up_curve)
        up_fxf = self.PRICING(self.usd_curve, up_curve_handle, self.spot_handle)
        print(up_fxf)
        
        # FRA price when 1bp down
        down_curve = qe.ZeroSpreadedTermStructure(curve_handle, qe.QuoteHandle(qe.SimpleQuote(-basis_point)))
        down_curve_handle = qe.YieldTermStructureHandle(down_curve)
        down_fxf = self.PRICING(self.usd_curve, down_curve_handle, self.spot_handle)
        print(down_fxf)

        # DV01
        dv01 = (up_fxf - down_fxf) / 2
        return dv01
    
    def THETA(self):
        price_t0 = self.PRICING(self.usd_curve, self.krw_curve, self.spot_handle)
        print(price_t0)
        usd_curve_t1 = self.USD_CURVE(self.date + datetime.timedelta(days=1))
        krw_curve_t1 = self.KRW_CURVE(self.date + datetime.timedelta(days=1))
        price_t1 = self.PRICING(usd_curve_t1, krw_curve_t1, self.spot_handle)
        print(price_t1)
        return price_t1 - price_t0

if __name__ == "__main__":
    
    todays_date = datetime.date(2020, 10, 20)
    
    # market
    maturity_date = datetime.date(2020, 12, 26)
    fx_spot = 1133.85
    ccy1 = 'KRW'
    ccy2 = 'USD'
    
    fx_forward = 1150.0
=======
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
    
>>>>>>> f47134ae5e5667ba85dd8d2bf1ce707a2b13370e
    
    # FX Forward Instrument
    krw = qe.KRWCurrency()
    usd = qe.USDCurrency()
<<<<<<< HEAD
    krw_notional = 7044000000
    usd_notional = krw_notional / fx_forward
    day_count = qe.ActualActual()
    
    fxf = FXF(todays_date,
              maturity_date,
              fx_spot,
              krw,
              krw_notional,
              usd,
              usd_notional,
              day_count)
=======
    maturity_date = qe.Date(11, 9, 2020)
    
    payCcy1 = False
    krw_notional = 7044000000
    usd_notional = krw_notional / forward_rate
    
    fxf = FXF()
>>>>>>> f47134ae5e5667ba85dd8d2bf1ce707a2b13370e
