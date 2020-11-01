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
                                       self.krw_curve,
                                       self.usd,
                                       self.usd_curve,
                                       fx_spot)
        
        ccs.setPricingEngine(engine)
        
        npv = ccs.NPV()
        
        return npv
        
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