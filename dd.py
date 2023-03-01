#import libraries
import tvDatafeed
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import numpy as np
import talib as ta
import matplotlib.pyplot as plt
import ccxt

exchange = ccxt.lbank2({
    'apiKey': '6',
    'secret': 'mysecret'
    'enableRateLimit': True,
})

# getting data from trading view
tv = TvDatafeed()
df = tv.get_hist(symbol='ATOMUSDT',exchange='binance',interval=Interval.in_1_hour,n_bars=5000)

#define alligator indicator
def alligator(df, jaw_length=13, teeth_length=8, lips_length=5):
    df['jaw'] = df['close'].rolling(window=jaw_length).mean().shift(jaw_length)
    df['teeth'] = df['close'].rolling(window=teeth_length).mean().shift(teeth_length)
    df['lips'] = df['close'].rolling(window=lips_length).mean().shift(lips_length)

    return df

jaw = alligator(df)['jaw'][-1]
lips = alligator(df)['lips'][-1]
teeth = alligator(df)['teeth'][-1]

df['SMA100'] = df['close'].rolling(window=100).mean()   #ezafe kardane sma200 be dataframe

# fractal high
df['wf_top_bool']=np.where(
df['high'] == df['high'].rolling(5, center=True).max() , True , False)

# fractal low
df['wf_bot_bool']=np.where(
df['low'] == df['low'].rolling(5, center=True).min() , True , False)

# alligator long
df['AG_long'] = np.where((df['close'] > df['jaw']) & (df['close'] > df['teeth']) & (df['close'] > df['lips']), True, False)

# alligator long
df['AG_short'] = np.where((df['close'] < df['jaw']) & (df['close'] < df['teeth']) & (df['close'] < df['lips']), True, False)

# taein meqdare fractal haye low(fl) va high(fh)
df['fh']= np.where(
df['high'] == df['high'].rolling(5, center=True).max() , df['high'] , None)
df['fh'] = df['fh'].ffill()
df['fl']=np.where(
df['low'] == df['low'].rolling(5, center=True).min() , df['low'] , None)
df['fl'] = df['fl'].ffill()

df['Buy'] = np.where((df.AG_long == True) & (df.close > df.fh) & (df.close > df.SMA100) , 1 , 0)
df['Sell'] = np.where((df.AG_short == True) & (df.close < df.fl) & (df.close < df.SMA100) , 1 , 0)

Multiplier = 3
df["TPl"]=np.where(df.Buy==1 , df.close+ (df.close-df.teeth)*Multiplier , 0)
df["TPs"]=np.where(df.Sell==1 , df.close+ (df.close-df.teeth)*Multiplier , 0)

long_entry , long_exit = [] , []
short_entry , short_exit = [] , []

for i in range (len(df)):
    if df.Buy.iloc[i]:            #jahaii ke signale buy sader shode
        long_entry.append(df.iloc[i].name)     # vared kardane zamani ke position buy baz bode be liste long entry
        for j in range (len(df)-i):         # yek loope jadid az jaii ke position baz shode be bad baraye check kardane tp ya sl
            if df.TPl.iloc[i]< df.close.iloc[i+j] or \
            df.teeth.iloc[i+j] > df.close.iloc[i+j]:    #agar qeymat zire sl baste shod, time baste shodan be long_exit ezafe mishe
                long_exit.append(df.iloc[i+j].name)
                break                                    #bad az residan be sl loop motevaqef mishe
    elif df.Sell.iloc[i]:                       #jahaii ke signale sell sader mishe ,  moshabehe signal buy
        short_entry.append(df.iloc[i].name)
        for j in range (len(df)-i):
            if df.TPs.iloc[i] > df.close.iloc[i+j] or \
            df.teeth.iloc[i+j]<df.close.iloc[i+j]:
                short_exit.append(df.iloc[i+j].name)
                break

