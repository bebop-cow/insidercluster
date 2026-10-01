

def project_fcf(fcf0, growth, years=5):
	projectfcf = []
	for yr in range(1, years+1):
		year_n = fcf0 * (1 + growth)**yr
		projectfcf.append(year_n)
	return projectfcf

print(project_fcf(100, 0.10, 5))