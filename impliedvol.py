import math


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

def main():

	S = 503
	iv = 1.17
	days = 2

	low1, high1 = move_range(S, iv, days, 1)
	low2, high2 = move_range(S, iv, days, 2)
	print(f"stock {S}, IV {iv}, {days} days")
	print(f"1σ (68%): {low1:.2f} to {high1:.2f}")
	print(f"2σ (95%): {low2:.2f} to {high2:.2f}")

if __name__ == "__main__":
    main()