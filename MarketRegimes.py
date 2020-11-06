import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()
import xlwings as xw

wb = xw.Book(r'C:\Users\HanaDT\Documents\quantdaddy\Market Regimes.xlsx')
sht = wb.sheets('Summary')
df = sht.range('H1:M589').options(pd.DataFrame).value
wb.close()

my_pal = {'Growth' : 'yellowgreen',
          'Inflation' : 'brown',
          'Volatility' : 'darkorange',
          'Funding Liquidity' : 'rebeccapurple',
          'Market Liquidity' : 'lightseagreen'}

plt.figure(figsize=(10, 8))
sns.boxplot(data=df, palette=my_pal)