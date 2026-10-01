

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

print(discount_to_pv([110, 121, 133.1, 146.41, 161.05], 0.10))