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


#Payoff overlay


def main():

	strike = 402.5
    z = sigma_distance(S, iv, days, strike)
    p = prob_above(S, iv, days, strike)
    print(f"strike {strike}: {z:+.2f}σ away, {p*100:.1f}% chance above")

if __name__ == "__main__":

    main()