import pandas as pd

EVENTS = [
    # date        actual  expected   (index levels; surprise in comment)
    ("2026-08-10", 334.95, 334.54),
    ("2026-07-14", 333.95, 334.70),   # -0.224pp cool
    ("2026-06-10", 335.12, 335.11),   # +0.003pp hot
    ("2026-04-10", 330.21, 330.41),   # -0.061pp cool
    ("2026-03-11", 326.79, 326.79),   #  0.000pp inline
    ("2026-02-13", 325.25, 325.41),   # -0.049pp cool
    ("2025-12-18", 324.12, 325.13),   # -0.311pp cool  (biggest)
    ("2025-10-24", 324.80, 325.01),   # -0.065pp cool
    ("2025-09-11", 323.98, 323.89),   # +0.028pp hot
    ("2025-08-12", 323.05, 323.20),   # -0.047pp cool
    ("2025-07-15", 322.56, 322.50),   # +0.019pp hot
    ("2025-05-13", 320.795, 320.88),  # -0.027pp cool
    ("2025-04-10", 319.799, 320.17),  # -0.116pp cool
    ("2025-03-12", 319.082, 319.22),  # -0.043pp cool
    ("2025-02-12", 317.67, 317.46),   # +0.067pp hot
    ("2025-01-15", 315.61, 315.61),   #  0.000pp inline
    ("2024-12-11", 315.49, 315.34),   # +0.048pp hot
    ("2024-11-13", 315.664, 315.59),  # +0.023pp hot
    ("2024-10-10", 315.30, 314.86),   # +0.140pp hot
    ("2024-09-11", 314.80, 314.98),   # -0.057pp cool
    ("2024-08-14", 314.54, 314.77),   # -0.073pp cool
    ("2024-07-11", 314.18, 314.63),   # -0.143pp cool
    ("2024-06-12", 314.07, 314.37),   # -0.096pp cool
    ("2024-05-15", 313.55, 313.76),   # -0.067pp cool
    ("2024-04-10", 312.33, 312.098),  # +0.075pp hot
    ("2024-03-12", 310.326, 310.30),  # +0.008pp hot
    ("2024-02-13", 308.417, 307.986), # +0.141pp hot
    ("2024-01-11", 306.746, 306.61),  # +0.044pp hot
    ("2023-12-12", 307.051, 306.90),  # +0.049pp hot
    ("2023-11-14", 307.671, 307.857), # -0.060pp cool
    ("2023-10-12", 307.789, 307.386), # +0.131pp hot
    ("2023-09-13", 307.026, 306.976), # +0.016pp hot
    ("2023-08-10", 305.691, 305.84),  # -0.049pp cool
    ("2023-07-12", 305.109, 305.219), # -0.036pp cool
    ("2023-06-13", 304.127, 304.063), # +0.021pp hot
    ("2023-05-10", 303.363, 303.532), # -0.056pp cool
]

def nearest_cpi(earnings_date, cpi_dates):
	best_cpi = None
	best_gap = None
	for cpi in cpi_dates:
		gap = (pd.Timestamp(cpi) - pd.Timestamp(earnings_date)).days
		if best_gap is None or abs(gap) < abs(best_gap):
			best_cpi = cpi
			best_gap = gap
	return best_cpi, best_gap

def classify_timing(gap):
	if gap < -3:
		return "CPI week before"
	elif gap > 3:
		return "CPI week after"
	else:
		return "same week"

def main():
	EARNINGS = {
    "AMD": ["2026-08-04", "2026-05-05", "2026-02-03", "2025-11-04"],
    "NVO": ["2026-08-04", "2026-05-05", "2026-02-03", "2025-11-05"],
}

	for ticker in EARNINGS:
		print(f"\n{ticker}")
		for ed in EARNINGS[ticker]:
			CPI_DATES = [e[0] for e in EVENTS]
			cpi, gap = nearest_cpi(ed,CPI_DATES)
			timing = classify_timing(gap)
			print(f"  earnings {ed}  nearest CPI {cpi}  gap {gap:+d}d  → {timing}")

if __name__ == '__main__':
	main()