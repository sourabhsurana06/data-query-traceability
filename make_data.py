import duckdb, pandas as pd, numpy as np
rng = np.random.default_rng(42)

categories = ["Apparel", "Footwear", "Accessories", "Home", "Beauty"]
regions = ["North", "South", "East", "West"]
weeks = list(range(1, 9))

rows = []
for w in weeks:
    for c in categories:
        for r in regions:
            base = {"Apparel":50000,"Footwear":35000,"Accessories":20000,"Home":28000,"Beauty":18000}[c]
            reg_mult = {"North":1.1,"South":1.0,"East":0.85,"West":0.95}[r]
            units = base * reg_mult * rng.normal(1.0, 0.04) / 100
            asp = {"Apparel":1200,"Footwear":2200,"Accessories":600,"Home":1800,"Beauty":900}[c]
            if w == 8 and c == "Footwear" and r == "West":
                asp = asp * 0.45          # planted anomaly: collapsed markdown
            if w == 8:
                units = units * 1.06       # mild seasonal lift that masks it
            revenue = units * asp
            rows.append([w, c, r, round(units), round(asp, 2), round(revenue, 2)])

df = pd.DataFrame(rows, columns=["week","category","region","units","asp","revenue"])
con = duckdb.connect("retail.db")
con.execute("DROP TABLE IF EXISTS sales")
con.execute("CREATE TABLE sales AS SELECT * FROM df")
print(con.execute("SELECT week, ROUND(SUM(revenue)) AS rev FROM sales GROUP BY week ORDER BY week").df().to_string(index=False))
con.close()
print("Done. retail.db created.")