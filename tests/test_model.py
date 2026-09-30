"""The model's maths, checked against a textbook value, against itself, and by simulation."""

import math

import numpy as np
import pytest

from paper import model


def test_the_call_price_matches_the_textbook_example():
    # S = K = 100, r = 5%, sigma = 20%, one year: the standard worked example, 10.4506.
    assert model.black_scholes_call(100, 100, 0.05, 0.2, 1.0) == pytest.approx(10.4506, abs=5e-5)


@pytest.mark.parametrize(
    ("s", "k", "r", "sigma", "t"),
    [(100, 90, 0.03, 0.25, 0.5), (80, 100, 0.01, 0.4, 2.0), (120, 100, 0.05, 0.1, 0.25)],
)
def test_calls_and_puts_obey_parity(s, k, r, sigma, t):
    call = model.black_scholes_call(s, k, r, sigma, t)
    put = model.black_scholes_put(s, k, r, sigma, t)
    assert call - put == pytest.approx(s - k * math.exp(-r * t), abs=1e-10)


def test_at_maturity_an_option_is_worth_its_payoff():
    assert model.black_scholes_call(110, 100, 0.05, 0.2, 0.0) == 10
    assert model.black_scholes_put(110, 100, 0.05, 0.2, 0.0) == 0


def test_simulation_agrees_with_the_formula():
    price, error = model.monte_carlo_call(100, 100, 0.05, 0.2, 1.0, paths=200_000)
    assert abs(price - model.black_scholes_call(100, 100, 0.05, 0.2, 1.0)) < 3 * error


def test_the_log_price_drifts_at_mu_minus_half_sigma_squared():
    """Itô's lemma: d(log S) = (mu - sigma^2 / 2) dt + sigma dW, so over a year the log return
    averages mu - sigma^2 / 2, not mu, and its variance is sigma^2."""
    mu, sigma, paths = 0.08, 0.3, 100_000
    _, prices = model.price_paths(100, mu, sigma, horizon=1.0, steps=50, paths=paths)
    log_returns = np.log(prices[:, -1] / 100)
    assert abs(log_returns.mean() - (mu - sigma**2 / 2)) < 4 * sigma / math.sqrt(paths)
    assert log_returns.var() == pytest.approx(sigma**2, rel=0.02)


def test_the_same_seed_draws_the_same_paths():
    first = model.price_paths(100, 0.08, 0.2, 1.0, steps=10, paths=5)[1]
    second = model.price_paths(100, 0.08, 0.2, 1.0, steps=10, paths=5)[1]
    assert np.array_equal(first, second)
