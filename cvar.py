import pandas as pd
import numpy as np
import datetime as dt
from pandas_datareader import data as pdr

def get_data(stocks, start, end):
    """
    Fetch adjusted close prices from Yahoo and return:
    - returns: DataFrame of pct_change()
    - meanReturns: Series of mean daily returns
    - covMatrix: DataFrame covariance matrix of returns
    """
    stockData = pdr.get_data_yahoo(stocks, start=start, end=end)
    stockData = stockData["Close"]
    returns = stockData.pct_change()
    meanReturns = returns.mean()
    covMatrix = returns.cov()
    return returns, meanReturns, covMatrix

def portfolio_performance(weights, meanReturns, covMatrix, time_horizon):
    """
    weights: array-like portfolio weights (sum to 1)
    meanReturns: Series of mean returns (typically daily)
    covMatrix: covariance matrix (matching meanReturns)
    time_horizon: multiplier to scale returns/std (e.g., 252 for annualization from daily)
    Returns: (expected_return, std_dev) scaled by time_horizon
    """
    expected_return = np.sum(meanReturns * weights) * time_horizon
    std = np.sqrt(np.dot(weights.T, np.dot(covMatrix, weights))) * np.sqrt(time_horizon)
    return expected_return, std

def _alpha_to_percent(alpha):
    """
    Accept alpha as either:
      - percentage (e.g. 5  => 5%)
      - proportion (e.g. 0.05 => 5%)
    Return alpha expressed as percent (0-100).
    """
    if alpha <= 0:
        raise ValueError("alpha must be > 0")
    if 0 < alpha <= 1:
        return alpha * 100.0
    if 1 < alpha < 100:
        return float(alpha)
    # alpha == 100 is degenerate; disallow
    raise ValueError("alpha must be in (0,1] or (1,100)")

def historical_var(returns, alpha=5):
    """
    Historical VaR (percentile-based).
    returns: pd.Series or pd.DataFrame of returns
    alpha: significance level as percent or proportion (default 5 -> 5%)
    For Series: returns the alpha-percentile (e.g. 5% percentile)
    For DataFrame: aggregates column-wise and returns Series
    """
    if isinstance(returns, pd.Series):
        a = _alpha_to_percent(alpha)
        # Use dropna to avoid NaNs affecting percentile
        return np.percentile(returns.dropna(), a)
    elif isinstance(returns, pd.DataFrame):
        return returns.aggregate(historical_var, alpha=alpha)
    else:
        raise TypeError("Expected returns to be dataframe or series")

def historical_cvar(returns, alpha=5):
    """
    Historical CVaR / Expected Shortfall.
    returns: pd.Series or pd.DataFrame of returns
    alpha: significance level as percent or proportion (default 5 -> 5%)
    For Series: compute VaR at alpha, then return the mean of returns <= VaR.
    For DataFrame: aggregates column-wise and returns Series
    """
    if isinstance(returns, pd.Series):
        # compute VaR first (corrected: do NOT call historical_cvar recursively)
        var = historical_var(returns, alpha=alpha)
        clean = returns.dropna()
        tail = clean[clean <= var]
        return tail.mean() if len(tail) > 0 else np.nan
    elif isinstance(returns, pd.DataFrame):
        return returns.aggregate(historical_cvar, alpha=alpha)
    else:
        raise TypeError("Expected returns to be dataframe or series")

if __name__ == "__main__":
    # Sample usage if running directy
    stockList = ['CBA', 'BHP', 'TLS', 'NAB', 'WBC', 'STO']
    stocks = [stock + '.AX' for stock in stockList]
    endDate = dt.datetime.now()
    startDate = endDate - dt.timedelta(days=800)

    returns, meanReturns, covMatrix = get_data(stocks, start=startDate, end=endDate)
    returns = returns.dropna()

    # deterministic random weights for reproducibility
    np.random.seed(42)
    weights = np.random.random(len(returns.columns))
    weights /= np.sum(weights)

    returns['portfolio'] = returns.dot(weights)

    var_5 = historical_var(returns['portfolio'], alpha=5)
    cvar_5 = historical_cvar(returns['portfolio'], alpha=5)

    print(f"Portfolio weights:\n{pd.Series(weights, index=returns.columns)}\n")
    print(f"VaR (5%): {var_5}")
    print(f"CVaR (5%): {cvar_5}")
