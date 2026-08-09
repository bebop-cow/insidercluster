def surprise(actual, consenses):
	 return actual - consenses
	
def bucker(surprise):
	if surprise > 0:
		return "hotter"
	elif surprise < 0:
		return "cooler"
	else:
		return "inline"