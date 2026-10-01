

def project_fcf(fcf0, growth, years=5):
	projectfcf = []
	for yr in range(1, years+1):
		year_n = fcf0 * (1 + growth)**yr
		projectfcf.append(year_n)
	return projectfcf

def discount_to_pv(cashflows, discount_rate):
	pvs = []
	for i, cf in enumerate(cashflows):
		year = i + 1                              # index 0 = year 1
		pv = cf / (1 + discount_rate)**year
		pvs.append(pv)
	return pvs

def terminal_value(last_fcf, terminal_growth, discount_rate):
	tv = last_fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
	if terminal_growth >= discount_rate:
		return None
	return tv

def intrinsic_value(fcf0, growth, discount_rate, terminal_growth, shares, years=5):
	cfs = project_fcf(fcf0, growth, years)
	pvs = discount_to_pv(cfs, discount_rate)
	tv = terminal_value(cfs[-1], terminal_growth, discount_rate)
	tv_pv = tv / (1 + discount_rate)**years
	total = sum(pvs) + tv_pv
	return total / shares

print(intrinsic_value(100, 0.10, 0.10, 0.025, 50))