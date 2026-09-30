"""The model: prices that follow geometric Brownian motion, and the Black–Scholes price of a call.

Only NumPy and the standard library, so the same code runs in readers' browsers (Pyodide).
"""

from __future__ import annotations

import math

import numpy as np

SEED = 20260930  # every random draw in the paper starts here, so every figure comes out the same


def price_paths(
    s0: float,
    mu: float,
    sigma: float,
    horizon: float,
    steps: int,
    paths: int,
    seed: int = SEED,
) -> tuple[np.ndarray, np.ndarray]:
    """Prices S_t = S_0 exp((mu - sigma^2/2) t + sigma W_t) on an even grid of `steps` steps.

    Returns the times, shape (steps + 1,), and the prices, shape (paths, steps + 1). Each step
    uses the exact solution, so the paths carry no discretisation error.
    """
    rng = np.random.default_rng(seed)
    dt = horizon / steps
    shocks = rng.standard_normal((paths, steps))
    increments = (mu - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * shocks
    log_prices = np.concatenate([np.zeros((paths, 1)), np.cumsum(increments, axis=1)], axis=1)
    return np.linspace(0.0, horizon, steps + 1), s0 * np.exp(log_prices)


def normal_cdf(x: float) -> float:
    """The standard normal distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black_scholes_call(s: float, k: float, r: float, sigma: float, t: float) -> float:
    """The Black–Scholes price of a European call: spot s, strike k, rate r, maturity t."""
    if t <= 0.0:
        return max(s - k, 0.0)
    d1 = (math.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    return s * normal_cdf(d1) - k * math.exp(-r * t) * normal_cdf(d2)


def black_scholes_put(s: float, k: float, r: float, sigma: float, t: float) -> float:
    """The Black–Scholes price of a European put."""
    if t <= 0.0:
        return max(k - s, 0.0)
    d1 = (math.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    return k * math.exp(-r * t) * normal_cdf(-d2) - s * normal_cdf(-d1)


def monte_carlo_call(
    s: float, k: float, r: float, sigma: float, t: float, paths: int, seed: int = SEED
) -> tuple[float, float]:
    """The call's price by simulation under the risk-neutral measure: the mean discounted payoff,
    and its standard error."""
    rng = np.random.default_rng(seed)
    s_t = s * np.exp((r - 0.5 * sigma**2) * t + sigma * math.sqrt(t) * rng.standard_normal(paths))
    payoffs = math.exp(-r * t) * np.maximum(s_t - k, 0.0)
    return float(payoffs.mean()), float(payoffs.std(ddof=1) / math.sqrt(paths))
