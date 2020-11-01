import datetime
import QuantExt as qe
from FX_CURVE import GET_QUOTE, USDIRS_CURVE, KRWCCS_CURVE

class CCS():
    def __init__(self, todays_date, effective_date, maturity_date, ccs_rate, fx_spot, ccy1_notional, ccy2_notional, position):
        # Initial Setup 1 - Date / Curves / Spot
        self.date = todays_date
        
        self.usd_curve = self.USD_CURVE(self.date)
        self.krw_curve = self.KRW_CURVE(self.date)
        
        self.spot_handle = qe.QuoteHandle(qe.SimpleQuote(fx_spot))
        
        # Initial Setup 2 - Instrument Info
        self.effective_date = qe.Date(effective_date.day, effective_date.month, effective_date.year)
        self.maturity_date = qe.Date(maturity_date.day, maturity_date.month, maturity_date.year)
        self.position = position
        self.ccs_rate = ccs_rate
        self.krw = qe.KRWCurrency()
        self.krw_notional = ccy1_notional
        self.usd = qe.USDCurrency()
        self.usd_notional = ccy2_notional
        
        self.length = 2
        self.spread = 0.0
        self.convention = qe.ModifiedFollowing
        self.calendar = qe.JointCalendar(qe.SouthKorea(), qe.UnitedStates())
        self.tenor = qe.Period(6, qe.Months)
        
        self.fixed_day_count = qe.Actual365Fixed()
        self.float_day_count = qe.Actual360()
        
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
        float_index = qe.USDLibor(qe.Period(6, qe.Months), usd_curve)
        
        fixed_schedule = qe.Schedule(self.effective_date,
                                     self.maturity_date,
                                     self.tenor,
                                     self.calendar,
                                     self.convention,
                                     self.convention,
                                     qe.DateGeneration.Backward,
                                     False)
        
        float_schedule = qe.Schedule(self.effective_date,
                                     self.maturity_date,
                                     self.tenor,
                                     self.calendar,
                                     self.convention,
                                     self.convention,
                                     qe.DateGeneration.Backward,
                                     False)
        
        ccs = qe.CrossCcyFixFloatSwap(self.position,
                                      self.krw_notional,
                                      self.krw,
                                      fixed_schedule,
                                      self.ccs_rate,
                                      self.fixed_day_count,
                                      self.convention,
                                      self.length,
                                      self.calendar,
                                      self.usd_notional,
                                      self.usd,
                                      float_schedule,
                                      float_index,
                                      self.spread,
                                      self.convention,
                                      self.length,
                                      self.calendar)

        engine = qe.CrossCcySwapEngine(self.krw,
                                       krw_curve,
                                       self.usd,
                                       usd_curve,
                                       fx_spot)
        
        ccs.setPricingEngine(engine)
        
        npv = ccs.NPV()
        
        return npv
        
    def FX_DELTA(self, fx_spot):
        up_fx = fx_spot * 1.0001
        up_fx_handle = qe.QuoteHandle(qe.SimpleQuote(up_fx))
        up_fxf = self.PRICING(self.usd_curve, self.krw_curve, up_fx_handle)
        
        down_fx = fx_spot * 0.9999
        down_fx_handle = qe.QuoteHandle(qe.SimpleQuote(down_fx))
        down_fxf = self.PRICING(self.usd_curve, self.krw_curve, down_fx_handle)
        
        fx_delta = (up_fxf - down_fxf) / 2
        print("FX Delta = {}".format(fx_delta))
        return fx_delta
    
    def USD_CURVE_DELTA(self):
        curve_handle = self.usd_curve
        
        # 1bp
        basis_point = 0.0001
        
        # FRA price when 1bp up
        up_curve = qe.ZeroSpreadedTermStructure(curve_handle, qe.QuoteHandle(qe.SimpleQuote(basis_point)))
        up_curve_handle = qe.YieldTermStructureHandle(up_curve)
        up_fxf = self.PRICING(up_curve_handle, self.krw_curve, self.spot_handle)
        
        # FRA price when 1bp down
        down_curve = qe.ZeroSpreadedTermStructure(curve_handle, qe.QuoteHandle(qe.SimpleQuote(-basis_point)))
        down_curve_handle = qe.YieldTermStructureHandle(down_curve)
        down_fxf = self.PRICING(down_curve_handle, self.krw_curve, self.spot_handle)

        # DV01
        dv01 = (up_fxf - down_fxf) / 2
        print("USD Curve Delta = {}".format(dv01))
        return dv01
    
    def KRW_CURVE_DELTA(self):
        curve_handle = self.krw_curve
        
        # 1bp
        basis_point = 0.0001
        
        # FRA price when 1bp up
        up_curve = qe.ZeroSpreadedTermStructure(curve_handle, qe.QuoteHandle(qe.SimpleQuote(basis_point)))
        up_curve_handle = qe.YieldTermStructureHandle(up_curve)
        up_fxf = self.PRICING(self.usd_curve, up_curve_handle, self.spot_handle)
        
        # FRA price when 1bp down
        down_curve = qe.ZeroSpreadedTermStructure(curve_handle, qe.QuoteHandle(qe.SimpleQuote(-basis_point)))
        down_curve_handle = qe.YieldTermStructureHandle(down_curve)
        down_fxf = self.PRICING(self.usd_curve, down_curve_handle, self.spot_handle)

        # DV01
        dv01 = (up_fxf - down_fxf) / 2
        print("KRW Curve Delta = {}".format(dv01))
        return dv01
    
    def THETA(self):
        price_t0 = self.PRICING(self.usd_curve, self.krw_curve, self.spot_handle)
        
        usd_curve_t1 = self.USD_CURVE(self.date + datetime.timedelta(days=1))
        krw_curve_t1 = self.KRW_CURVE(self.date + datetime.timedelta(days=1))
        
        price_t1 = self.PRICING(usd_curve_t1, krw_curve_t1, self.spot_handle)
        
        theta = price_t1 - price_t0
        print("1-day Theta = {}".format(theta))
        
        return theta
    
if __name__ == "__main__":
    
    todays_date = datetime.date(2020, 10, 20)
    
    # market
    effective_date = datetime.date(2020, 11, 26)
    maturity_date = datetime.date(2022, 11, 26)
    fx_spot = 1133.85
    
    position = qe.VanillaSwap.Payer
    
    ccs_rate = 0.0009746
    
    krw_notional = 7044000000
    usd_notional = krw_notional / fx_spot
    
    ccs = CCS(todays_date,
              effective_date,
              maturity_date,
              ccs_rate,
              fx_spot,
              krw_notional,
              usd_notional,
              position)