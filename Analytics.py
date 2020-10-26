import numpy as np
import pandas as pd
from itertools import groupby, chain
from xbbg import blp

class Core_Analytics():
    def __init__(self):
        self.annual = 252
        
    # Annualized Arithmetic Average Return
    def average(self, returns):
        return returns.mean() * self.annual
    
    # Annualized Geometric Average Return
    def cagr(self, returns):
        return (1 + returns).prod() ** (self.annual / len(returns)) - 1
        
    # Annualized Standard Deviation
    def stdev(self, returns):
        return returns.std() * np.sqrt(self.annual)
        
    # Annualized Downside Deviation
    def downdev(self, returns, target=0.0):
        returns = returns.copy()
        returns.loc[returns > target] = 0
        summation = (returns ** 2).sum()
        return np.sqrt(self.annual * summation / (len(returns) - 1))
    
    # Annualzied Upside Deviation
    def updev(self, returns, target=0.0):
        returns = returns.copy()
        returns.loc[returns < target] = 0
        summation = (returns ** 2).sum()
        return np.sqrt(self.annual * summation / (len(returns) - 1))
    
    # Annualized Covariance
    def covar(self, returns, benchmark):
        return returns.cov(benchmark) * self.annual
    
    # Correlation
    def correl(self, returns, benchmark):
        return returns.corr(benchmark)
    
    def print_result(self, returns, benchmark, target=0.0):
        average = self.average(returns)
        cagr = self.cagr(returns)
        stdev = self.stdev(returns)
        downdev = self.downdev(returns, target)
        updev = self.updev(returns, target)
        covar = self.covar(returns, benchmark)
        correl = self.correl(returns, benchmark)
        
        result = {"Arithmetic Return": average,
                  "Compound Return": cagr,
                  "Volatility": stdev,
                  "Downside Deviation": downdev,
                  "Upside Deviation": updev,
                  "Covariance": covar,
                  "Correlation": correl}
     
        return result
        
    
class Tail_Analytics():
    def __init__(self):
        self.annual = 252
        
    def skewness(self, returns):
        return returns.skew()
    
    def kurtosis(self, returns):
        return returns.kurtosis()
    
    def coskewness(self, returns, benchmark):
        r_mean = returns.mean()
        b_mean = benchmark.mean()
        r_stdev = returns.std()
        b_stdev = benchmark.std()
        T = len(returns)        
        summation = ((returns - r_mean) * ((benchmark - b_mean) ** 2) / (r_stdev * (b_stdev ** 2))).sum()
        return (T / ((T - 1) * (T - 2))) * summation
    
    def cokurtosis(self, returns, benchmark):
        r_mean = returns.mean()
        b_mean = benchmark.mean()
        r_stdev = returns.std()
        b_stdev = benchmark.std()
        T = len(returns)
        summation = ((returns - r_mean) * ((benchmark - b_mean) ** 3) / (r_stdev * (b_stdev ** 3))).sum()
        return ((T * (T + 1)) / ((T - 1) * (T - 2) * (T - 3))) * summation - (3 * (T - 1) ** 2) / ((T - 2) * (T - 3))
    
    def drawdown(self, returns):
        cumulative = (1 + returns).cumprod()
        highwatermark = cumulative.cummax()
        drawdown = (cumulative / highwatermark) - 1
        return drawdown
        
    def maximum_drawdown(self, returns):
        return np.min(self.drawdown(returns))
    
    def drawdown_duration(self, returns):
        drawdown = self.drawdown(returns)
        ddur = list(chain.from_iterable((np.arange(len(list(j))) + 1).tolist() if i==1 else [0] * len(list(j)) for i, j in groupby(drawdown != 0)))
        ddur = pd.DataFrame(ddur, columns=['Drawdown Duration'])
        ddur.index = returns.index
        return ddur
    
    def maximum_drawdown_duration(self, returns):
        return np.max(self.drawdown_duration(returns))
    
    def pain_index(self, returns, days=252):
        return -(self.drawdown(returns)[-days:]).sum() / days
    
    def VaR(self, returns, percentile=99):
        return returns.quantile(1 - percentile / 100)
    
    def CVaR(self, returns, percentile=99):
        return returns[returns < self.VaR(returns, percentile)].mean()
    
    def print_result(self, returns, benchmark, percentile=99, days=252):
        skew = self.skewness(returns)
        kurt = self.kurtosis(returns)
        coskew = self.coskewness(returns, benchmark)
        cokurt = self.cokurtosis(returns, benchmark)
        mdd = self.maximum_drawdown(returns)
        mddur = self.maximum_drawdown_duration(returns)
        painidx = self.pain_index(returns, days)
        var = self.VaR(returns, percentile)
        cvar = self.CVaR(returns, percentile)
        
        result = {"Skewness" : skew,
                  "Kurtosis" : kurt,
                  "Co-Skewness" : coskew,
                  "Co-Kurtosis" : cokurt,
                  "Maximum Drawdown" : mdd,
                  "Maximum Drawdown Duration" : mddur,
                  "Pain Index" : painidx,
                  "99% VaR" : var,
                  "99% CVaR" : cvar}
        
        return result

class Performance_Analytics(Core_Analytics, Tail_Analytics):
    def __init__(self):
        self.annual = 252
        
    def sharpe_ratio(self, returns, benchmark):
        """
        When the benchmark used for the calculation of excess return is not a risk-free asset,
        this is often called Information Ratio.
        """
        return self.average(returns - benchmark) / self.stdev(returns - benchmark)
    
    def adjusted_sharpe_ratio(self, returns, benchmark):
        """
        The adjusted Sharpe Ratio was proposed as an alternative to the standard Sharpe Ratio
        when related performance is not normally distributed.
        The measure is derived from a Taylor series expansion of an exponential utility function.
        """
        skewness = (returns - benchmark).skew()
        kurtosis = (returns - benchmark).kurtosis()
        sharpe_ratio = self.sharpe_ratio(returns, benchmark)
        return sharpe_ratio * (1 + skewness * sharpe_ratio / 6 - kurtosis * (sharpe_ratio ** 2) / 24)
    
    def sortino_ratio(self, returns, benchmark, target=0.0):
        return self.average(returns - benchmark) / self.downdev(returns, target)
    
    def calmar_ratio(self, returns, benchmark):
        return -self.average(returns - benchmark) / self.maximum_drawdown(returns - benchmark)
    
    def pain_ratio(self, returns, benchmark):
        return self.average(returns - benchmark) / self.pain_index(returns - benchmark)
    
    def reward_to_VaR_ratio(self, returns, benchmark):
        return -self.average(returns - benchmark) / self.VaR(returns - benchmark)
    
    def reward_to_CVaR_ratio(self, returns, benchmark):
        return -self.average(returns - benchmark) / self.CVaR(returns - benchmark)
    
    def hit_ratio(self, returns):
        return len(returns[returns > 0]) / (len(returns[returns > 0]) + len(returns[returns < 0]))
    
    def gain_to_pain_ratio(self, returns):
        return - returns[returns > 0].sum() / returns[returns < 0].sum()
    
    def print_result(self, returns, benchmark, target=0.0):
        sr = self.sharpe_ratio(returns, benchmark)
        asr = self.adjusted_sharpe_ratio(returns, benchmark)
        sortino = self.sortino_ratio(returns, benchmark, target)
        calmar = self.calmar_ratio(returns, benchmark)
        painratio = self.pain_ratio(returns, benchmark)
        varratio = self.reward_to_VaR_ratio(returns, benchmark)
        cvarratio = self.reward_to_CVaR_ratio(returns, benchmark)
        hitratio = self.hit_ratio(returns)
        gpratio = self.gain_to_pain_ratio(returns)
        
        result = {"Sharpe Ratio" : sr,
                  "Adjusted Sharpe Ratio" : asr,
                  "Sortino Ratio" : sortino,
                  "Calmar Ratio" : calmar,
                  "Pain Ratio" : painratio,
                  "Reward-to-VaR Ratio" : varratio,
                  "Reward-to-CVaR Ratio" : cvarratio,
                  "Hit Ratio" : hitratio,
                  "Gain-to-Pain Ratio" : gpratio}
    
        return result
    
if __name__ == "__main__":
    # Import Data from Bloomberg API
    Tickers = ['SPX Index', 'VIX Index', 'H15T3M Index']
    Start = '19900102'
    
    End =  pd.Timestamp.today().strftime("%Y%m%d")
    flds = ["PX_LAST"]
    
    df = blp.bdh(tickers=Tickers,
                 flds=flds,
                 start_date=Start,
                 end_date=End)
    
    df.columns = ['SPX Index', 'VIX Index', '3M T-Bill']
    
    df['SPX Ret'] = df['SPX Index'].pct_change()
    df['VIX Ret'] = df['VIX Index'].pct_change()
    df['Null Ret'] = 0.0
    df = df.dropna()
    
    spx_ret = df['SPX Ret']
    vix_ret = df['VIX Ret']
    rf_ret = (df['3M T-Bill'] / 100) / 252
    null_ret = df['Null Ret']
    
    
    # 1. Core Analytics
    core = Core_Analytics()
    average = core.average(spx_ret)
    cagr = core.cagr(spx_ret)
    stdev = core.stdev(spx_ret)
    downdev = core.downdev(spx_ret)
    updev = core.updev(spx_ret)
    covar = core.covar(spx_ret, vix_ret)
    correl = core.correl(spx_ret, vix_ret)
    
    core_result = core.print_result(spx_ret, rf_ret)
    
    # 2. Tail-Risk Analytics
    tail = Tail_Analytics()
    skew = tail.skewness(spx_ret)
    kurt = tail.kurtosis(vix_ret)
    coskew = tail.coskewness(spx_ret, rf_ret)
    cokurt = tail.cokurtosis(spx_ret, rf_ret)
    dd = tail.drawdown(spx_ret)
    mdd = tail.maximum_drawdown(spx_ret)
    ddur = tail.drawdown_duration(spx_ret)
    maxddur = tail.maximum_drawdown_duration(spx_ret)
    painidx = tail.pain_index(spx_ret)
    var = tail.VaR(spx_ret)
    cvar = tail.CVaR(spx_ret)
    
    tail_result = tail.print_result(spx_ret, spx_ret)
    
    # 3. Performance Evaluation Analytics
    perform = Performance_Analytics()
    sr = perform.sharpe_ratio(spx_ret, rf_ret)
    asr = perform.adjusted_sharpe_ratio(spx_ret, rf_ret)
    sortino = perform.sortino_ratio(spx_ret, rf_ret)
    calmar = perform.calmar_ratio(spx_ret, rf_ret)
    painratio = perform.pain_ratio(spx_ret, rf_ret)
    varratio = perform.reward_to_VaR_ratio(spx_ret, rf_ret)
    cvarratio = perform.reward_to_CVaR_ratio(spx_ret, rf_ret)
    hitratio = perform.hit_ratio(spx_ret)
    gpr = perform.gain_to_pain_ratio(spx_ret)
    
    perform_result = perform.print_result(spx_ret, null_ret)
    
    table = {**core_result, **tail_result, **perform_result}
    pd.DataFrame(table).T.to_clipboard()