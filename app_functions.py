import streamlit as st
import pandas as pd
import re
from dateutil import parser
from io import BytesIO


# download the files functions

@st.cache_data 
def convert_df(df):
   return df.to_csv(header=True,mode='w',encoding='Windows-1255',index=False)

@st.cache_data 
def convert_df_utf(df):
   return df.to_csv(header=True, index=False, encoding='utf-8').encode('utf-8')

# dataframe functions for upload and load the data

@st.cache_data
def load_data(file):
    # Determine file type based on the file extension
    filename = file.name
    data = None

    try:
        if filename.endswith('.csv'):
            # Try reading CSV with multiple encodings
            encodings_to_try = ["ISO-8859-8", "utf-8", "ISO-8859-1", "latin1"]
            for encoding in encodings_to_try:
                try:
                    data = pd.read_csv(file, encoding=encoding)
                    if not data.empty:
                        break
                except (UnicodeDecodeError, pd.errors.EmptyDataError):
                    continue
        elif filename.endswith(('.xls', '.xlsx')):
            # Read Excel files
            data = pd.read_excel(file)
        elif filename.endswith('.txt'):
            # Assume text files are structured as CSV
            encodings_to_try = ["utf-8", "ISO-8859-1", "latin1"]
            for encoding in encodings_to_try:
                try:
                    data = pd.read_csv(file, encoding=encoding, delimiter="\t")
                    if not data.empty:
                        break
                except (UnicodeDecodeError, pd.errors.EmptyDataError):
                    continue
        else:
            st.error("Unsupported file format. Please upload a CSV, Excel, or text file.")
            return None

        if data is None or data.empty:
            st.error("Failed to read the file content. It might be empty, removed from the application or improperly formatted.")
            return None

        if '#' not in data.columns:
            data['Index'] = range(1, len(data) + 1)
            data.set_index('Index', inplace=True)

    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
        return None

    return data

# function for data types 

def clean_and_convert_to_float(column):
    # Basic replacements and trim whitespace
    column_cleaned = (
        column.astype(str)
        .str.replace(r'[^\w\s.-]', '', regex=True)  # Remove special characters except "." and "-"
        .str.replace(r'\s+', '', regex=True)  # Remove all whitespace
        .str.replace(',', '', regex=False)  # Remove thousands separators
        .str.replace('(', '', regex=False)  # Convert opening parentheses 
        .str.replace(')', '', regex=False)  # Remove closing parentheses
        .str.replace('€', '', regex=False)  # Remove euro 
        .str.replace('$', '', regex=False)  # Remove dollar 
        .str.replace('£', '', regex=False)  # Remove pound 
        .str.replace('₪', '', regex=False)  # Remove shekel  
        .str.replace("'", '', regex=False)  # Remove pound 
        .str.replace(r'\((.*?)\)', r'-\1', regex=True)  # Convert accountent negitive number parentheses to negative sign number 
    )
    # Convert exponent expressions to standard floats
    column_cleaned = column_cleaned.apply(lambda x: re.sub(r'(\d+)\s*[xX]\s*10\s*[eE]\s*(\d+)', r'\1e\2', x))

    # Convert cleaned column to numeric, handling non-convertible values
    numeric_column = pd.to_numeric(column_cleaned, errors='coerce')
    return numeric_column.fillna(0)


def clean_and_convert_to_int(column):

    float_column = clean_and_convert_to_float(column)
    int_column = float_column.round().astype('Int64')  # Using 'Int64' to handle NaNs gracefully
    return int_column.fillna(0)

def clean_and_convert_to_date(column, date_formats=None):

    def parse_date(x):
        try:
            return parser.parse(x) if date_formats is None else pd.to_datetime(x, format=date_formats, errors='coerce')
        except (ValueError, TypeError):
            return pd.NaT
    
    date_column = column.astype(str).apply(parse_date)
    return date_column.fillna(pd.NaT)

def clean_and_convert_to_string(column):

    string_column = column.astype(str).str.strip()  # Remove leading and trailing whitespaces
    return string_column

def clean_and_convert_to_json(column):

    def parse_json(x):
        try:
            return pd.json.loads(x)
        except (ValueError, TypeError):
            return {}
    
    json_column = column.apply(parse_json)
    return json_column

def clean_and_convert_to_boolean(column):

    boolean_column = column.apply(lambda x: str(x).lower().strip() in ['true', '1', 'yes'])
    return boolean_column.astype(bool)


def export_to_excel(samples_dict):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for category, data in samples_dict.items():
                    data.to_excel(writer, sheet_name=category, index=False)
            return output.getvalue()
