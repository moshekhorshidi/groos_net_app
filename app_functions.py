import streamlit as st
import pandas as pd

@st.cache_data 
def convert_df(df):
   return df.to_csv(header=True,mode='w',encoding='Windows-1255',index=False)

@st.cache_data 
def convert_df_utf(df):
   return df.to_csv(header=True,mode='w',encoding='UTF-8',index=False)

@st.cache_data 
def load_csv_data(file):
    data = pd.read_csv(file, encoding="ISO-8859-8")
    data['Row_Number'] = range(1, len(data) + 1)
    data['Row_Number'] = data['Row_Number'].astype(int)
    data.set_index('Row_Number')
    data.index.name = 'Row_Number'

    return data

@st.cache_data 
def load_excel_data(file):
    data = pd.read_excel(file)
    data['Row_Number'] = range(1, len(data) + 1)
    data['Row_Number'] = data['Row_Number'].astype(int)
    data.set_index('Row_Number')
    data.index.name = 'File_Row_Number'

    return data