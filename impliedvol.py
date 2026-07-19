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

	expected = expected_move(S, iv, days)
	ranges = move_range(S, iv, days, n_sigma)

if __name__ == "__main__":
    main()