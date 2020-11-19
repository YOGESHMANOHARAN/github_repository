import pandas as pd

def read_and_resample(filename):
    df = pd.read_excel(filename)
    return df.resample('1H').mean()

