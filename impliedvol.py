import math
import yfinance as yf

def expected_move(S, iv, days):
	T = days/365
	move = S * iv * math.sqrt(T)
	return move

def move_range(S, iv, days, n_sigma):
	onesigma = expected_move(S, iv, days)
	scaled_move = onesigma * n_sigma
	lowerprice = S - scaled_move
	upperprice = S + scaled_move

	return lowerprice, upperprice

#strike picker mode
def sigma_distance(S, iv, days, strike):
	onesigma = expected_move(S, iv, days)
	nosigma = (strike - S) / onesigma
	return nosigma

def prob_above(S, iv, days, strike):
	z = sigma_distance(S, iv, days, strike)
	cdf = 0.5 * (1 + math.erf(z / math.sqrt(2)))   # P(finish below strike)
	return 1 - cdf            

#Live IV
def get_atm_iv(ticker, expiry_index=0):
    tk = yf.Ticker(ticker)
    expiry = tk.options[expiry_index]
    chain = tk.option_chain(expiry)
    calls = chain.calls
    spot = tk.history(period="1d")["Close"].iloc[-1]
    nearest = (calls["strike"] - spot).abs().idxmin()   # index of closest strike
    return calls.loc[nearest, "impliedVolatility"]          # that row's IV

def get_spot(ticker):
	tk = yf.Ticker(ticker)
	last_close = tk.history(period="1d")["Close"].iloc[-1]
	return last_close

def main():
	ticker = input("Ticker: ").strip().upper()
	S = get_spot(ticker)          # (or pull live — we can do that next)
    days = int(input("Days to expiry: "))
    strike = float(input("Strike: "))
    iv = get_atm_iv(ticker, 0)          # real ATM IV, nearest expiry
    print(f"{ticker} live ATM IV: {iv:.4f}")

    low1, high1 = move_range(S, iv, days, 1)
    low2, high2 = move_range(S, iv, days, 2)
    print(f"1σ (68%): {low1:.2f} to {high1:.2f}")
    print(f"2σ (95%): {low2:.2f} to {high2:.2f}")

    strike = 402.5
    z = sigma_distance(S, iv, days, strike)
    p = prob_above(S, iv, days, strike)
    print(f"strike {strike}: {z:+.2f}σ, {p*100:.1f}% above")

if __name__ == "__main__":
    main()
