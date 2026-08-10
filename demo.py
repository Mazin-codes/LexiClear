import pandas as pd

df = pd.read_excel("evaluation/results.xlsx")

print(df.head())
print(df.columns.tolist())