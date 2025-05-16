import app_functions as af
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import openpyxl
from datetime import datetime
import numpy as np

# Application version
APP_VERSION = "0.0.0"

# -- Set a page config and style -- 
st.set_page_config(page_title=f'Gross Net Analysis WebApp',
                   page_icon=':bar_chart:',
                   layout='wide')

st.title("Gross Net Analysis WebApp")

app_css_page_style = """
<style>
footer {visibility: hidden;}
</style>
"""
st.markdown(app_css_page_style, unsafe_allow_html=True)

# App navigation options
app_navigation_options = {"Home": 0, "Mapping Client Data": 1, 
                          "Monthly Costing": 2, "Annual Costing": 3}


# # App navigation options
# app_navigation_options = {"Home": 0, "Mapping Client Data": 1, 
#                           "Monthly Costing": 2, "Annual Costing": 3, 
#                           "Employee Calculation": 4}


with st.sidebar:
    st.markdown(f"**App Version (Testing): {APP_VERSION}**")
    app_navigation = option_menu(
        menu_title='App Navigation',
        options=list(app_navigation_options.keys()),
        icons=['bi bi-house', 'map', 'bi bi-calendar2-check', 
               'bar-chart-fill', 'percent'],
        menu_icon='three-dots-vertical'
    )
    

# Initialize session state once
def initialize_session_state():
    if 'monthly_mapping_done' not in st.session_state:
        st.session_state['monthly_mapping_done'] = False
    if 'annual_mapping_done' not in st.session_state:
        st.session_state['annual_mapping_done'] = False
    if 'employee_mapping_done' not in st.session_state:
        st.session_state['employee_mapping_done'] = False

    if 'monthly_df_mapped' not in st.session_state:
        st.session_state['monthly_df_mapped'] = None
    if 'annual_df_mapped' not in st.session_state:
        st.session_state['annual_df_mapped'] = None
    if 'employee_df_mapped' not in st.session_state:
        st.session_state['employee_df_mapped'] = None

    if 'monthly_uploaded' not in st.session_state:
        st.session_state['monthly_uploaded'] = None
    if 'annual_uploaded' not in st.session_state:
        st.session_state['annual_uploaded'] = None
    if 'employee_uploaded' not in st.session_state:
        st.session_state['employee_uploaded'] = None

    # Initialize date_formats if not present
    if 'date_formats' not in st.session_state:
        st.session_state['date_formats'] = {}
    
    # Initialize date formats for each type of date column if not already set
    date_columns = {
        "Payment Date": None,
        "Employee Start Date": None,
        "Employee End Date": None
    }
    
    for date_col in date_columns:
        if date_col not in st.session_state['date_formats']:
            st.session_state['date_formats'][date_col] = None

initialize_session_state()

# Define numeric columns that should always be converted to float
NUMERIC_COLUMNS = [
    "Total Payments",
    "Base Salary",
    "Hourly Rate",
    "Salary Cost",
    "Salary",
    "Income Tax Deduction",
    "National Insurance"
]

def convert_numeric_columns(df, columns_to_convert):
    """
    Convert specified columns to numeric values, handling various formats and errors.
    
    Args:
        df (pd.DataFrame): Input dataframe
        columns_to_convert (list): List of columns to convert to numeric
        
    Returns:
        pd.DataFrame: Dataframe with converted numeric columns
    """
    df_copy = df.copy()
    
    for col in columns_to_convert:
        if col in df_copy.columns:
            # Remove any currency symbols, commas, and spaces
            if df_copy[col].dtype == 'object':
                df_copy[col] = df_copy[col].astype(str).str.replace('₪', '', regex=False)
                df_copy[col] = df_copy[col].str.replace('$', '', regex=False)
                df_copy[col] = df_copy[col].str.replace(',', '', regex=False)
                df_copy[col] = df_copy[col].str.strip()
            
            # Convert to numeric, replacing errors with NaN
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
            
            # Notify if any values were converted to NaN
            nan_count = df_copy[col].isna().sum()
            if nan_count > 0:
                st.warning(f"{nan_count} values in {col} could not be converted to numbers and were set to NaN. Please check your data.")
    
    return df_copy

def home():
    
    st.title("Welcome to the Gross Net Analysis WebApp")
    
    st.markdown("""

            **Overview**

            Welcome to employee cost analysis! Our Gross Net Analysis WebApp is designed to empower financial analysts, human resource managers, and business owners with robust insights into employee compensation dynamics. By seamlessly integrating data mapping, monthly and annual costing analysis, and employee-specific calculations, our application provides an all-encompassing platform for comprehensive financial data exploration.

            **Features**

            - **Mapping Client Data:** Customize your data layout to ensure accurate analysis by mapping relevant columns for employee ID, payments, and department attributes. This feature helps tailor your datasets, making further analysis accurate and efficient.
            
            - **Monthly Costing Analysis:** Delve into detailed monthly breakdowns of employee costs. Assess key metrics such as salary costs, work hours, and department distributions to better understand financial trends and identify cost-saving opportunities.

            - **Annual Costing Analysis:** Discover deeper insights from annual data. View aggregate payments, departmental financial allocations, and employee distribution. Our cutting-edge visualization tools allow you to visualize patterns, align budgetary forecasts, and communicate findings effectively.

            - **Employee Calculations:** Perform detailed per-employee financial assessments, estimating pension provisions, compensation funds, and educational contributions. Tailored calculations provide clarity on social security obligations, making it easier to uphold fiscal responsibilities.

            **How to Use**

            1. **Data Upload:** 
            - Navigate to the sidebar and upload your data files in supported formats (.csv, .xls, .xlsx, .txt) using our intuitive file upload feature.

            2. **Mapping and Customization:**
            - Customize your data for precise analysis. Use our mapping tools to align your uploaded data with the required fields for successful integration and exploration.

            3. **Explore and Analyze:**
            - Utilize the navigation menu to explore different analytical perspectives—monthly, annual, or employee-specific. Gain valuable insights using our interactive charts, downloadable reports, and tailored KPIs.

            4. **Download and Report:**
            - Extract detailed reports and visual insights effortlessly. Use the download options to save analysis results for further offline processing and strategic planning.

            **Get Started Now**

            We invite you to explore the world of data-driven decision-making. Let our WebApp transform the way you perceive employee costs. Dive deeper, analyze effectively, and optimize effortlessly.

            **Feedback and Support**

            Your feedback is invaluable to us. As we continue to enhance the capabilities of our application, please feel free to reach out with suggestions or inquiries. Together, let's make financial analysis an enlightening experience.
            
            
            
            """)

def mapping_data(file_key, expected_columns, mapping_key, uploaded_key):
    uploaded_file = st.file_uploader(f"**Upload file for {file_key}**", type=["csv", "xls", "xlsx", "txt"], key=file_key)

    # Define date columns for each file type
    date_columns = {
        "monthly": ["Payment Date"],
        "annual": ["Employee Start Date", "Employee End Date"]
    }

    if uploaded_file or st.session_state.get(uploaded_key):
        if uploaded_file:
            st.session_state[uploaded_key] = uploaded_file
            df = af.load_data(uploaded_file)
        else:
            df = af.load_data(st.session_state[uploaded_key])

        if df is not None:
            st.subheader(f"Total records in uploaded file (Completeness check): {len(df)}")
            st.write(f"***Preview of Uploaded {file_key.capitalize()} Data***", df.head())

            if mapping_key not in st.session_state:
                st.session_state[mapping_key] = {col: None for col in expected_columns}

            # Show date format selection section before the mapping form
            if date_columns.get(file_key):
                st.subheader("Date Format Settings")
                date_format_cols = st.columns(len(date_columns[file_key]))
                
                for idx, date_col in enumerate(date_columns[file_key]):
                    with date_format_cols[idx]:
                        st.markdown(f"**{date_col} Format**")
                        current_format = st.session_state['date_formats'].get(date_col, "Select format")
                        date_format = st.selectbox(
                            "Select your file date format:",
                            options=[
                                "Select format",
                                "YYYY-MM-DD",
                                "DD-MM-YYYY",
                                "MM-DD-YYYY",
                                "DD/MM/YYYY",
                                "MM/DD/YYYY",
                                "YYYY/MM/DD",
                                "YYYY.MM.DD",
                                "DD.MM.YYYY",
                                "MM.DD.YYYY"
                            ],
                            index=0 if current_format == "Select format" else [None, "YYYY-MM-DD", "DD-MM-YYYY", "MM-DD-YYYY", "DD/MM/YYYY", "MM/DD/YYYY", "YYYY/MM/DD"].index(current_format),
                            key=f"date_format_standalone_{file_key}_{date_col}"
                        )
                        st.session_state['date_formats'][date_col] = date_format
                        
                        # Show example of selected format
                        if date_format != "Select format":
                            st.markdown("**Example:**")
                            example_date = datetime.now().strftime(
                                date_format.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
                            )
                            st.code(example_date)

            with st.form(key=f'{file_key}_mapping_form'):
                st.write(f"Map Your {file_key.capitalize()} Data Columns:")

                # Add a placeholder to column options
                columns_with_placeholder = ['Not Selected'] + list(df.columns)

                # Track if all required selections are made
                all_selections_valid = True
                date_formats_selected = True

                for expected_column in expected_columns:
                    current_mapping = st.session_state[mapping_key].get(expected_column, "Select column from list")
                    
                    # Create single column for selection since date format is now outside
                    selected_column = st.selectbox(
                        f"Select relevant column for '{expected_column}':",
                        options=columns_with_placeholder,
                        index=columns_with_placeholder.index(current_mapping) if current_mapping in columns_with_placeholder else 0,
                        key=f"select_{file_key}_{expected_column}"
                    )

                    # Check if date format is selected for date columns
                    if expected_column in date_columns.get(file_key, []):
                        if st.session_state['date_formats'].get(expected_column) == "Select format":
                            date_formats_selected = False

                    # Check if the current selection is valid
                    if selected_column == "Select column from list":
                        all_selections_valid = False

                    # Only update session state if a valid column is selected
                    if selected_column != "Select column from list":
                        st.session_state[mapping_key][expected_column] = selected_column

                submitted = st.form_submit_button(f"Submit {file_key.capitalize()} Mapping")

                # Show warning if date formats are not selected
                if not date_formats_selected:
                    st.warning("Please select date formats for all date columns before submitting.")

            if submitted:
                # Check both column mappings and date formats before proceeding
                if all_selections_valid and date_formats_selected:
                    column_mapping = {val: key for key, val in st.session_state[mapping_key].items()}
                    
                    # Convert date columns using selected formats
                    for expected_column, original_column in column_mapping.items():
                        if expected_column in date_columns.get(file_key, []):
                            if st.session_state['date_formats'][expected_column] == "Select format":
                                st.error(f"Please select a date format for {expected_column}")
                                return
                            format_str = st.session_state['date_formats'][expected_column].replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
                            try:
                                df[original_column] = pd.to_datetime(df[original_column], format=format_str)
                            except Exception as e:
                                st.error(f"Error converting dates in column {original_column}: {str(e)}")
                                return

                    # First rename the columns
                    df_mapped = df.rename(columns=column_mapping)
                    
                    # Then convert numeric columns
                    numeric_cols_present = [col for col in NUMERIC_COLUMNS if col in df_mapped.columns]
                    if numeric_cols_present:
                        df_mapped = convert_numeric_columns(df_mapped, numeric_cols_present)
                    
                    # Extract year and month components from date columns
                    df_mapped = af.extract_date_components(df_mapped, date_columns.get(file_key, []))
                    
                    st.session_state[f'{file_key}_df_mapped'] = df_mapped

                    if set(expected_columns).issubset(df_mapped.columns):
                        st.success(f"{file_key.capitalize()} Column mapping successful!")
                        st.session_state[f'{file_key}_mapping_done'] = True
                        
                        # Show preview of mapped data with date components
                        st.subheader("Preview of Mapped Data")
                        preview_columns = list(expected_columns)
                        for date_col in date_columns.get(file_key, []):
                            preview_columns.extend([
                                f"{date_col}_Year",
                                f"{date_col}_Month",
                                f"{date_col}_Month_Name"
                            ])
                        st.dataframe(df_mapped[preview_columns].head())
                        
                    
                    else:
                        st.error(f"Mapping failed. Ensure all required columns are correctly mapped.")
                        st.session_state[f'{file_key}_mapping_done'] = False
                else:
                    if not all_selections_valid:
                        st.error("Please complete all column mappings before submitting.")
                    if not date_formats_selected:
                        st.error("Please select date formats for all date columns before submitting.")
        else:
            st.info(f"Check the file again or load data again for {file_key} to continue using the application.")
    else:
        st.info(f"Please upload a valid {file_key} file to proceed with mapping.")

def get_days_in_month(date):
    # Get the last day of the month
    if date.month == 12:
        last_day = pd.Timestamp(date.year + 1, 1, 1) - pd.Timedelta(days=1)
    else:
        last_day = pd.Timestamp(date.year, date.month + 1, 1) - pd.Timedelta(days=1)
    return last_day.day

def monthly_costing():
    st.subheader("Monthly Costing Analysis")

    if not st.session_state['monthly_mapping_done']:
        st.warning("Please complete the monthly data mapping before proceeding.")
        st.stop()
    
    monthly_df_mapped = st.session_state.get('monthly_df_mapped')
    
    if monthly_df_mapped is None:
        st.error("No monthly data available. Please upload and map your data first.")
        st.stop()

    # Convert Payment Date using user's selected format
    if 'date_formats' in st.session_state and 'Payment Date' in st.session_state.date_formats:
        try:
            format_str = st.session_state.date_formats['Payment Date'].replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
            monthly_df_mapped['Payment Date'] = pd.to_datetime(monthly_df_mapped['Payment Date'], format=format_str)
        except Exception as e:
            st.error(f"Error converting dates: {str(e)}")
            st.stop()

    # Convert Payment Date to datetime if it's not already
    monthly_df_mapped['Payment Date'] = pd.to_datetime(monthly_df_mapped['Payment Date'])
    monthly_df_mapped['Days in Month'] = monthly_df_mapped['Payment Date'].apply(get_days_in_month)

    monthly_df_mapped["Salary Cost"] = af.clean_and_convert_to_float(monthly_df_mapped["Salary Cost"])
    monthly_df_mapped["Week Work Hours"] = af.clean_and_convert_to_float(monthly_df_mapped['Week Work Hours'])
    monthly_df_mapped["Base Salary"] = af.clean_and_convert_to_float(monthly_df_mapped["Base Salary"])

    # KPI calculations
    total_records = len(monthly_df_mapped)
    total_distinct_records = monthly_df_mapped.drop_duplicates().shape[0]
    avg_emp_cost = monthly_df_mapped['Salary Cost'].mean()
    mid_emp_cost = monthly_df_mapped['Salary Cost'].median()

    # Display KPIs
    left_column, center_column = st.columns(2)
    with left_column:
        st.subheader(f'Total Records: {total_records:,}')
        st.subheader(f'Total Distinct Records: {total_distinct_records:,}')
    
    with center_column:
        st.subheader(f'Average Employee Cost: {avg_emp_cost:,.2f}')
        st.subheader(f'Median Employee Cost: {mid_emp_cost:,.2f}')
        

    # Add new expander for vacation provision calculations
    with st.expander("***Vacation Day Provision Calculator***"):
        st.subheader("Vacation Day Provision Calculator")
        
        # Get user input for provision percentage
        provision_percentage = st.number_input(
            "Enter Provision Percentage (e.g., 0.25 for 25%)",
            min_value=0.0,
            max_value=1.0,
            value=0.25,
            step=0.01,
            format="%.2f"
        )
        
        # Add option to filter data
        st.subheader("Optional: Filter Data")
        use_filters = st.checkbox("Use Filters", value=False)
        
        filtered_df = monthly_df_mapped.copy()

        # Ensure Payment Date is in datetime format using the user's selected format
        if 'date_formats' in st.session_state and 'Payment Date' in st.session_state.date_formats:
            try:
                format_str = st.session_state.date_formats['Payment Date'].replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
                filtered_df['Payment Date'] = pd.to_datetime(filtered_df['Payment Date'], format=format_str)
            except Exception as e:
                st.error(f"Error converting dates: {str(e)}")
                st.stop()
        
        if use_filters:
            # Get all available columns from the dataframe
            available_columns = filtered_df.columns.tolist()
            filtered_df['Employee ID'] = filtered_df['Employee ID'].astype("string") 
            
            # Add "Select All" option
            all_columns = ['Select All'] + available_columns
            
            # Let user select which columns to filter
            selected_filter_columns = st.multiselect(
                'Select Columns to Filter',
                options=all_columns,
                default=[]
            )
            
            # Handle "Select All" option
            if 'Select All' in selected_filter_columns:
                selected_filter_columns = available_columns
            
            if selected_filter_columns:
                # Create columns for filters
                filter_col1, filter_col2 = st.columns(2)
                
                with filter_col1:
                    for col in selected_filter_columns[:len(selected_filter_columns)//2]:
                        if filtered_df[col].dtype in ['object', 'string']:
                            # Categorical filters
                            unique_values = filtered_df[col].unique().tolist()
                            selected_values = st.multiselect(f'Filter by {col}', unique_values, default=unique_values)
                            if selected_values:
                                filtered_df = filtered_df[filtered_df[col].isin(selected_values)]
                        
                        elif filtered_df[col].dtype == 'datetime64[ns]':
                            # Date filter with proper formatting
                            min_date = filtered_df[col].min()
                            max_date = filtered_df[col].max()
                            date_range = st.date_input(
                                f'Filter by {col} Range',
                                value=(min_date, max_date),
                                min_value=min_date,
                                max_value=max_date
                            )
                            if len(date_range) == 2:
                                filtered_df = filtered_df[
                                    (filtered_df[col].dt.date >= date_range[0]) &
                                    (filtered_df[col].dt.date <= date_range[1])
                                ]
                        else:
                            # Numeric filters with number inputs
                            min_val = float(filtered_df[col].min())
                            max_val = float(filtered_df[col].max())
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                min_input = st.number_input(
                                    f'Min {col}',
                                    min_value=min_val,
                                    max_value=max_val,
                                    value=min_val,
                                    step=1.0
                                )
                            with col2:
                                max_input = st.number_input(
                                    f'Max {col}',
                                    min_value=min_val,
                                    max_value=max_val,
                                    value=max_val,
                                    step=1.0
                                )
                            
                            filtered_df = filtered_df[
                                (filtered_df[col] >= min_input) &
                                (filtered_df[col] <= max_input)
                            ]
                
                with filter_col2:
                    for col in selected_filter_columns[len(selected_filter_columns)//2:]:
                        if filtered_df[col].dtype in ['object', 'string']:
                            # Categorical filters
                            unique_values = filtered_df[col].unique().tolist() 
                            selected_values = st.multiselect(f'Filter by {col}', unique_values, default=unique_values)
                            if selected_values:
                                filtered_df = filtered_df[filtered_df[col].isin(selected_values)]
                        
                        elif filtered_df[col].dtype == 'datetime64[ns]':
                            # Date filter with proper formatting
                            min_date = filtered_df[col].min()
                            max_date = filtered_df[col].max()
                            date_range = st.date_input(
                                f'Filter by {col} Range',
                                value=(min_date, max_date),
                                min_value=min_date,
                                max_value=max_date
                            )
                            if len(date_range) == 2:
                                filtered_df = filtered_df[
                                    (filtered_df[col].dt.date >= date_range[0]) &
                                    (filtered_df[col].dt.date <= date_range[1])
                                ]
                        else:
                            # Numeric filters with number inputs
                            min_val = float(filtered_df[col].min())
                            max_val = float(filtered_df[col].max())
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                min_input = st.number_input(
                                    f'Min {col}',
                                    min_value=min_val,
                                    max_value=max_val,
                                    value=min_val,
                                    step=1.0
                                )
                            with col2:
                                max_input = st.number_input(
                                    f'Max {col}',
                                    min_value=min_val,
                                    max_value=max_val,
                                    value=max_val,
                                    step=1.0
                                )
                            
                            filtered_df = filtered_df[
                                (filtered_df[col] >= min_input) &
                                (filtered_df[col] <= max_input)
                            ]
        
        # Get user input for sample size
        max_records = len(filtered_df)
        sample_size = st.number_input(
            "Enter Number of Sample Records to Display",
            min_value=1,
            max_value=max_records,
            value=min(5, max_records),
            step=1
        )
        
        # Calculate vacation provision
        filtered_df['Vacation Provision'] = (
            filtered_df['Base Salary'] / 
            filtered_df['Days in Month'] * 
            (provision_percentage + 1)
        )
        
        # Display sample of calculations based on user input
        st.write(f"Sample Calculations (First {sample_size} records):")
        
        # Let user select which columns to display
        display_columns = st.multiselect(
            'Select Columns to Display',
            options=['Select All'] + filtered_df.columns.tolist(),
            default=['Employee ID', 'Employee Name', 'Payment Date', 'Base Salary', 'Days in Month', 'Vacation Provision']
        )
        
        # Handle "Select All" option for display columns
        if 'Select All' in display_columns:
            display_columns = filtered_df.columns.tolist()
        
        if display_columns:
            sample_df = filtered_df[display_columns].head(sample_size)
            
            # Format date columns according to user's preference
            if 'Payment Date' in display_columns and 'date_formats' in st.session_state:
                date_format = st.session_state.date_formats.get('Payment Date')
                if date_format:
                    sample_df['Payment Date'] = sample_df['Payment Date'].dt.strftime(
                        date_format.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
                    )
            
            st.dataframe(sample_df)
        else:
            st.warning("Please select at least one column to display")
        
        # Add explanation of calculation
        st.markdown("""
        **Calculation Formula:**
        ```
        Vacation Provision = (Base Salary / Days in Month) * (Provision Percentage + 1)
        ```
        
        **Example:**
        - Base Salary: 10,000
        - Days in Month: 30
        - Provision Percentage: 0.25
        - Calculation: (10,000 / 30) * (0.25 + 1) = 416.67
        """)
        
        # Add download button for the calculations
        if display_columns:
            csv = sample_df.to_csv(index=False)
            st.download_button(
                "Download Sample Calculations",
                csv,
                "vacation_provision_sample.csv",
                "text/csv",
                key='download-vacation-provision'
            )

    # Working hours condition

    with st.expander("***working hours analysis***"):

        try:
            #st.write("##")
            #st.markdown("Insert condition on working hours")
            condition_input = float(st.number_input("**Insert condition on working hours**",step=1))
            df_filtered = monthly_df_mapped[monthly_df_mapped['Week Work Hours'] > condition_input]
            chart_data = df_filtered.groupby('Department')['Week Work Hours'].count()
         
            st.subheader("***See Bar Chart visual (Insert condition first)***")
            st.bar_chart(chart_data)

            # Visualization of filtered data
            st.subheader("***Click to see the visual related population***")
            st.data_editor(df_filtered, num_rows="dynamic")

            filtered_data = {
                "Result Data": df_filtered
            }

                # Download filtered results
            excel_data = af.export_to_excel(filtered_data)
            st.download_button("Download Result", data=excel_data, file_name="Monthly_Result.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        except ValueError:
        
            st.info("**Insert a number to continue**", icon='🔄')

    # In monthly_costing function, update the December Payment Summary section
    if 'monthly_df_mapped' in st.session_state:
        df = st.session_state['monthly_df_mapped']

        # Display data with formatted dates
        with st.expander("***December Payment Summary***"):
            st.markdown("### December Payment Summary")
            december_data = df[df['Payment Date'].dt.month == 12].copy()
            
            # Format the date before display
            if 'Payment Date' in december_data.columns:
                december_data['Payment Date'] = format_date_column(december_data, 'Payment Date')
                st.dataframe(december_data)
            
                # Calculate summaries
                # Convert to numeric first to ensure proper calculations
                december_data['Salary'] = pd.to_numeric(december_data['Salary'], errors='coerce')
                december_data['Income Tax Deduction'] = pd.to_numeric(december_data['Income Tax Deduction'], errors='coerce')
                december_data['National Insurance'] = pd.to_numeric(december_data['National Insurance'], errors='coerce')
        
                total_salaries = december_data['Salary'].sum()
                total_income_tax = december_data['Income Tax Deduction'].sum()
                total_national_insurance = december_data['National Insurance'].sum()

                summary_data = pd.DataFrame({
                    'Description': ['Total Salaries', 'Total Income Tax Deductions', 'Total National Insurance'],
                    'Amount': [total_salaries, total_income_tax, total_national_insurance]
                })
            
                # Format numbers with commas for thousands
                def format_number(x):
                    try:
                        return f"{float(x):,.2f}"
                    except (ValueError, TypeError):
                        return str(x)
                    
                summary_data['Amount'] = summary_data['Amount'].apply(format_number)
                    
                st.dataframe(summary_data)

                # Export to Excel with formatted dates
                december_samples_dict = {
                    "Relevant December Data": december_data,
                    "December Payment Summary": summary_data,
                } 
            
                excel_data = af.export_to_excel(december_samples_dict)
                st.download_button(
                    "Download December Payment Summary",
                    data=excel_data,
                    file_name="december_payment_summary.xlsx",
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    with st.expander("***Financial Analysis Year-over-Year***"):
        # Create a copy of the dataframe for display purposes
        display_df = monthly_df_mapped.copy()
        
        # Extract year and month
        display_df['Year'] = display_df['Payment Date'].dt.year
        display_df['Month'] = display_df['Payment Date'].dt.month

        # Quick Overview Section
        st.subheader("📊 Quick Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Years", display_df['Year'].nunique())
        with col2:
            st.metric("Average Monthly Cost", f"${display_df['Salary Cost'].mean():,.2f}")
        with col3:
            st.metric("Total Employees", display_df['Employee ID'].nunique())

        # Analysis Tabs
        analysis_tab, material_tab, trends_tab = st.tabs(["📈 Analysis", "🔍 Material Changes", "📊 Trends"])

        with analysis_tab:
            # Filter Section
            st.subheader("Filter Data")
            col1, col2 = st.columns(2)
            
            with col1:
                years = st.multiselect(
                    "Select Years",
                    options=sorted(display_df['Year'].unique()),
                    default=[]
                )
                months = st.multiselect(
                    "Select Months",
                    options=range(1, 13),
                    default=[],
                    format_func=lambda x: datetime.strptime(str(x), "%m").strftime("%B")
                )
                departments = st.multiselect(
                    "Select Departments",
                    options=display_df['Department'].unique(),
                    default=[]
                )
            
            with col2:
                employees = st.multiselect(
                    "Select Employees",
                    options=display_df['Employee ID'].unique(),
                    default=[]
                )
                metric = st.selectbox(
                    "Select Metric",
                     options=['Salary Cost', 'Salary', 'Income Tax Deduction', 'National Insurance'],
                    
                )

            # Apply filters
            filtered_data = display_df.copy()
            if years:
                filtered_data = filtered_data[filtered_data['Year'].isin(years)]
            if months:
                filtered_data = filtered_data[filtered_data['Month'].isin(months)]
            if departments:
                filtered_data = filtered_data[filtered_data['Department'].isin(departments)]
            if employees:
                filtered_data = filtered_data[filtered_data['Employee ID'].isin(employees)]

            # Display filtered data
            st.subheader("Filtered Data")
            st.dataframe(filtered_data, use_container_width=True)

            # Summary Metrics
            st.subheader("Summary Metrics")
            col1, col2, col3 = st.columns(3)
            
            # Convert metric data to numeric, handling any non-numeric values
            numeric_data = pd.to_numeric(filtered_data[metric], errors='coerce')
            
            with col1:
                st.metric("Total", f"₪ {numeric_data.sum():,.2f}")
            with col2:
                st.metric("Average", f"₪ {numeric_data.mean():,.2f}")
            with col3:
                st.metric("Median", f"₪ {numeric_data.median():,.2f}")

            # Trend Chart
            st.subheader(f"{metric} Trend")
            # Ensure numeric conversion for trend data as well
            trend_data = filtered_data.groupby(['Year', 'Month']).agg({metric: lambda x: pd.to_numeric(x, errors='coerce').sum()}).reset_index()
            trend_data['Date'] = pd.to_datetime(trend_data[['Year', 'Month']].assign(DAY=1))
            fig = px.line(trend_data, x='Date', y=metric, title=f"{metric} Trend Over Time",
                         text=trend_data[metric].round(2).astype(str))
            fig.update_traces(
                textposition="top center",
                textfont=dict(
                    size=14,
                    color='black',
                    family="Arial Black"
                )
            )
            fig.update_layout(
                yaxis_title=f"Total {metric}",
                xaxis_title="Date",
                showlegend=True,
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True)

        with material_tab:
            st.subheader("Material Change Analysis")
            
            # Analysis method selection
            analysis_method = st.radio(
                "Select Analysis Method",
                ["Percentage Change", "Absolute Amount"],
                horizontal=True
            )

            if analysis_method == "Percentage Change":
                threshold = st.number_input(
                    "Enter percentage threshold for material changes",
                    min_value=0.0,
                    max_value=100.0,
                    value=10.0,
                    step=0.1,
                    format="%.1f"
                )
                threshold_type = "percentage"
            else:
                threshold = st.number_input(
                    "Enter amount threshold in shekels",
                    min_value=0.0,
                    value=1000.0,
                    step=100.0,
                    format="%.0f"
                )
                threshold_type = "amount"

            # Calculate changes per employee
            filtered_data = filtered_data.sort_values(['Employee ID', 'Payment Date'])
            # Calculate changes for each employee separately
            employee_changes = []
            for emp_id in filtered_data['Employee ID'].unique():
                emp_data = filtered_data[filtered_data['Employee ID'] == emp_id].copy()
                emp_data['Change'] = emp_data[metric].pct_change() * 100
                emp_data['Absolute Change'] = emp_data[metric].diff()
                employee_changes.append(emp_data)
            
            # Combine all employee changes
            all_changes = pd.concat(employee_changes)
            
            # Identify material changes
            if threshold_type == "percentage":
                material_changes = all_changes[abs(all_changes['Change']) > threshold]
            else:
                material_changes = all_changes[abs(all_changes['Absolute Change']) > threshold]

            # Display material changes
            st.subheader("Material Changes by Employee")
            
            if not material_changes.empty:
                # Create tabs for each employee with material changes
                employee_tabs = st.tabs([f"Employee {emp_id}" for emp_id in material_changes['Employee ID'].unique()])
                
                for tab, emp_id in zip(employee_tabs, material_changes['Employee ID'].unique()):
                    with tab:
                        emp_material_changes = material_changes[material_changes['Employee ID'] == emp_id]
                        
                        # Calculate summary statistics for this employee
                        total_changes = len(emp_material_changes)
                        avg_change = emp_material_changes['Change'].mean() if threshold_type == "percentage" else emp_material_changes['Absolute Change'].mean()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Material Changes", total_changes)
                        with col2:
                            st.metric("Average Change", 
                                    f"{avg_change:.2f}%" if threshold_type == "percentage" else f"₪{avg_change:,.2f}")
                        
                        # Style the dataframe
                        def highlight_material_changes(row):
                            if threshold_type == "percentage":
                                change = row['Change']
                            else:
                                change = row['Absolute Change']
                            
                            if abs(change) > threshold:
                                return ['background-color: #ffcccc'] * len(row)
                            return [''] * len(row)

                        styled_df = emp_material_changes.style.apply(highlight_material_changes, axis=1)
                        st.dataframe(styled_df, use_container_width=True)
                        
                        # Add a line chart for this employee's changes
                        fig = px.line(emp_material_changes, 
                                    x='Payment Date', 
                                    y=metric,
                                    title=f"{metric} Trend for Employee {emp_id}",
                                    text=emp_material_changes[metric].round(2).astype(str))
                        fig.update_traces(
                            textposition="top center",
                            textfont=dict(
                                size=14,
                                color='black',
                                family="Arial Black"
                            )
                        )
                        fig.update_layout(
                            yaxis_title=f"{metric}",
                            xaxis_title="Date",
                            showlegend=True,
                            font=dict(size=14)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                # Download all material changes
                st.download_button(
                    "Download All Material Changes",
                    material_changes.to_csv(index=False),
                    "material_changes.csv",
                    "text/csv"
                )
            else:
                st.info("No material changes found based on the selected threshold.")

        with trends_tab:
            # Department Analysis
            st.subheader("Department Analysis")
            dept_data = filtered_data.groupby(['Year', 'Department'])[metric].sum().reset_index()
            fig = px.bar(dept_data, x='Year', y=metric, color='Department', 
                        title=f"{metric} by Department",
                        text=dept_data[metric].round(2).astype(str))
            fig.update_traces(
                textposition="outside",
                textfont=dict(
                    size=14,
                    color='black',
                    family="Arial Black"
                )
            )
            fig.update_layout(
                yaxis_title=f"Total {metric}",
                xaxis_title="Year",
                showlegend=True,
                uniformtext_minsize=14,
                uniformtext_mode='hide',
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True)

            # Monthly Analysis
            st.subheader("Monthly Analysis")
            monthly_data = filtered_data.groupby('Month')[metric].mean().reset_index()
            # Convert month integer to month name, ensuring month is valid
            monthly_data['Month_Name'] = monthly_data['Month'].apply(lambda x: datetime.strptime(str(x), "%m").strftime("%B") if x in range(1, 13) else "Unknown")
            fig = px.line(monthly_data, x='Month_Name', y=metric, 
                         title=f"Average {metric} by Month",
                         text=monthly_data[metric].round(2).astype(str))
            fig.update_traces(
                textposition="top center",
                textfont=dict(
                    size=14,
                    color='black',
                    family="Arial Black"
                )
            )
            fig.update_layout(
                yaxis_title=f"Average {metric}",
                xaxis_title="Month",
                showlegend=True,
                xaxis={'categoryorder': 'array', 'categoryarray': [datetime.strptime(str(m), "%m").strftime("%B") for m in range(1, 13)],
                       'tickfont': dict(size=14)},
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True)

        # Download Options
        st.subheader("Download Data")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download Filtered Data",
                filtered_data.to_csv(index=False),
                "filtered_data.csv",
                "text/csv"
            )
        with col2:
            summary = filtered_data.groupby('Year')[metric].agg(['sum', 'mean', 'median']).reset_index()
            st.download_button(
                "Download Summary",
                summary.to_csv(index=False),
                "summary_stats.csv",
                "text/csv"
            )


def annual_costing(): 

    st.subheader("Annual Costing Analysis")

    # Ensure the user has completed data mapping before proceeding
    if not st.session_state.get('annual_mapping_done', False):
        st.warning("Please complete the annual data mapping before proceeding.")
        st.stop()

    # Load mapped data from session state
    annual_df_mapped = st.session_state.get('annual_df_mapped')

    if annual_df_mapped is not None:

        # KPI calculations 
        left_column, center_column, right_column = st.columns(3)
        total_records = len(annual_df_mapped)
        total_distinct_records = annual_df_mapped.drop_duplicates().shape[0]
        avg_total_pay = annual_df_mapped['Total Payments'].mean()
        mid_total_pay = annual_df_mapped['Total Payments'].median()
        total_unique_employee_number = annual_df_mapped['Employee ID'].nunique()

        # Assume the user has already uploaded data and loaded it into session state
        if 'annual_df_mapped' in st.session_state:
            df = st.session_state['annual_df_mapped']

            # Ensure date columns are parsed correctly
            df['Employee Start Date'] = pd.to_datetime(df['Employee Start Date'], errors='coerce')
            df['Employee End Date'] = pd.to_datetime(df['Employee End Date'], errors='coerce')

            # If you are calculating these numbers from the DataFrame, example:
            total_employees_end_year = df[df['Employee End Date'].isna()]['Employee ID'].nunique()
            total_employees_left = df[df['Employee End Date'].notna()]['Employee ID'].nunique()
            total_new_employees = df[df['Employee Start Date'] > pd.Timestamp(year=pd.to_datetime('today').year - 1, month=12, day=31)]['Employee ID'].nunique()

            kpi_data = {
            'Description KPI': [
                'Total Records',
                'Total Distinct Records',
                'Total Unique Employees',
                'Average Employee Cost',
                'Median Employee Cost',
                'Total Employees at End of Year',
                'Total Employees Left During Year',
                'Total New Employees This Year'
            ],
            'KPI Number': [
                total_records,
                total_distinct_records,
                total_unique_employee_number,
                round(avg_total_pay, 3),
                round(mid_total_pay, 3),
                total_employees_end_year,
                total_employees_left,
                total_new_employees
            ]
        }

            st.subheader("Summary table")
            kpi_summary_df = pd.DataFrame(kpi_data)
            st.write(kpi_summary_df.style.format({'KPI Number':'{:,}'}))

            # Proceed with other analyses, visualizations, or download options
        else:
            st.error("No annual data mapped. Please upload and map your data first.")       

        # Visualization and charts
        with left_column:
            df_for_first_pie = annual_df_mapped[['Department', 'Total Payments']]
            fig = px.pie(df_for_first_pie, values='Total Payments', names='Department', title='Total Payments by Department')
            fig.update_traces(
                textinfo='percent+label',
                hoverinfo='percent+label',
                insidetextorientation='horizontal',
                outsidetextfont=dict(size=15, color='black'),
                insidetextfont=dict(size=15, color='white')
            )
            fig.update_layout(uniformtext_minsize=15, uniformtext_mode='show')
            st.plotly_chart(fig)
            file_download_first_pie = af.convert_df_utf(df_for_first_pie)
            st.download_button("Download result for first pie", file_download_first_pie, "result_first_pie_chart.csv", "csv", key='download-first-pie-file')

        with center_column:
            df_for_second_pie = annual_df_mapped[['Department', 'Employee ID']].drop_duplicates()
            department_counts = df_for_second_pie['Department'].value_counts()
            total_employees = department_counts.sum()
            department_percentages = (department_counts / total_employees) * 100

            labels = [f"{department} ({count} employees, {percentage:.2f} %)" for department, count, percentage in zip(department_counts.index, department_counts.values, department_percentages.values)]
            fig = px.pie(values=department_counts.values, names=department_counts.index, title='Employee Distribution by Department', labels=labels)
            fig.update_traces(textinfo='percent+text+value')
            st.plotly_chart(fig)
            file_download_second_pie = af.convert_df(department_percentages)
            st.download_button("Download result for second pie", file_download_second_pie, "result_second_pie_chart.csv", "text/csv", key='download-second-pie-file')
        
        with st.expander("***Check Percent Difference for employee***"):
        # Employee analysis based on percentage difference
            st.subheader("Check Percent Difference for employee")
            annual_df_mapped['Percentage Difference'] = annual_df_mapped['Total Payments'].ffill().pct_change()
            employee_selection = st.selectbox('Choose employee to analyze:', options=annual_df_mapped['Employee ID'].unique(), placeholder='Choose employee number')

            df_for_emp_analysis = annual_df_mapped[['Employee ID', 'Percentage Difference', 'Total Payments']]
            df_filtered = df_for_emp_analysis[df_for_emp_analysis['Employee ID'] == employee_selection]
            df_filtered = df_filtered.rename_axis('Row Number in File', axis=0)
            df_filtered['Table_Row_Number'] = df_filtered.reset_index().index + 1

            st.subheader("***See employee related analysis***")
            st.table(df_filtered[['Table_Row_Number', 'Employee ID', 'Total Payments', 'Percentage Difference']])
            df_chart = df_filtered.set_index('Table_Row_Number')[['Total Payments']]
            st.bar_chart(df_chart, use_container_width=True)
            st.line_chart(df_chart)

        # Ranking employees based on salary
        
        
        try:

            with st.expander("***Click to see employee salary ranking***"):

                st.subheader("Highest Ranking Employee Annual Salaries")

                ranked_df = annual_df_mapped.groupby('Employee ID')['Total Payments'].max().reset_index()
                ranked_df = ranked_df.sort_values(by='Total Payments', ascending=False).reset_index(drop=True)
                ranked_df['Rank'] = range(1, len(ranked_df) + 1)
                limit_rank = st.selectbox("Choose rank Size/Range", options=ranked_df['Rank'], placeholder="choose rank range")
                ranked_df_filtered = ranked_df[ranked_df['Rank'] <= limit_rank]
                st.table(ranked_df_filtered[['Rank', 'Employee ID', 'Total Payments']])
                st.bar_chart(ranked_df_filtered.set_index('Rank')['Total Payments'])
                ranking_file_download = af.convert_df(ranked_df_filtered)
                st.download_button("Download ranking result", ranking_file_download, "ranking_result.csv", "text/csv", key='download-ranking-file')
        
        except Exception as e:
            st.info("Result will be presented after uploading a data file or on error.")

        with st.expander("***Employee Sampling Based on Status***"):
            # New functionality for employee categorization and sampling
            st.subheader("Employee Sampling Based on Status")

            # Categorizing employees based on status
            year_end = pd.Timestamp(year=pd.to_datetime('today').year, month=12, day=31)
            active_employees = annual_df_mapped[annual_df_mapped['Employee End Date'].isna()]
            left_employees = annual_df_mapped[annual_df_mapped['Employee End Date'].notna() & (annual_df_mapped['Employee End Date'] <= year_end)]
            new_employees = annual_df_mapped[annual_df_mapped['Employee Start Date'] > year_end.replace(year=year_end.year - 1)]

            # Sampling input
            st.subheader("Specify Sample Sizes")
            sample_active = st.number_input("Number of samples from active employees", min_value=0, value=5)
            sample_left = st.number_input("Number of samples from employees who left", min_value=0, value=5)
            sample_new = st.number_input("Number of samples from new employees", min_value=0, value=5)

            # Sampling dataframes
            sampled_active = active_employees.sample(min(sample_active, len(active_employees)))
            sampled_left = left_employees.sample(min(sample_left, len(left_employees)))
            sampled_new = new_employees.sample(min(sample_new, len(new_employees)))

            # Export to Excel
            samples_dict = {
                "Active Employees": sampled_active,
                "Left Employees": sampled_left,
                "New Employees": sampled_new
            }

            excel_data = af.export_to_excel(samples_dict)
            st.download_button("Download Employee Samples", data=excel_data, file_name="employee_samples.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


    with st.expander("***Financial Analysis Year-over-Year***"):
        if 'annual_df_mapped' not in st.session_state:
            st.warning("No monthly data mapped. Please upload and map your data first.")
            st.stop()

        annual_df_mapped = st.session_state['annual_df_mapped']
        annual_df_mapped['Employee Start Date'] = pd.to_datetime(annual_df_mapped['Employee Start Date'], errors='coerce')
        annual_df_mapped['Year'] = annual_df_mapped['Employee Start Date'].dt.year
        annual_df_mapped['Month'] = annual_df_mapped['Employee Start Date'].dt.month

        # Quick Overview Section
        st.subheader("📊 Quick Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Years", annual_df_mapped['Year'].nunique())
        with col2:
            st.metric("Average Monthly Cost", f"${annual_df_mapped['Total Payments'].mean():,.2f}")
        with col3:
            st.metric("Total Employees", annual_df_mapped['Employee ID'].nunique())

        # Analysis Tabs
        analysis_tab, material_tab, trends_tab = st.tabs(["📈 Analysis", "🔍 Material Changes", "📊 Trends"])

        with analysis_tab:
            # Filter Section
            st.subheader("Filter Data")
            col1, col2 = st.columns(2)
            
            with col1:
                years = st.multiselect(
                    "Select Years",
                    options=sorted(annual_df_mapped['Year'].unique()),
                    default=sorted(annual_df_mapped['Year'].unique())[-2:]
                )
                months = st.multiselect(
                    "Select Months",
                    options=range(1, 13),
                    default=range(1, 13),
                    format_func=lambda x: datetime.strptime(str(x), "%m").strftime("%B")
                )
                departments = st.multiselect(
                    "Select Departments",
                    options=annual_df_mapped['Department'].unique(),
                    default=annual_df_mapped['Department'].unique()
                )
            
            with col2:
                employees = st.multiselect(
                    "Select Employees",
                    options=annual_df_mapped['Employee ID'].unique(),
                    default=[]
                )
                metric = st.selectbox(
                    "Select Metric",
                    options=['Total Payments']
                )

            # Apply filters
            filtered_data = annual_df_mapped.copy()
            if years:
                filtered_data = filtered_data[filtered_data['Year'].isin(years)]
            if months:
                filtered_data = filtered_data[filtered_data['Month'].isin(months)]
            if departments:
                filtered_data = filtered_data[filtered_data['Department'].isin(departments)]
            if employees:
                filtered_data = filtered_data[filtered_data['Employee ID'].isin(employees)]

            # Display filtered data
            st.subheader("Filtered Data")
            st.dataframe(filtered_data, use_container_width=True)

            # Summary Metrics
            st.subheader("Summary Metrics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total", f"${filtered_data[metric].sum():,.2f}")
            with col2:
                st.metric("Average", f"${filtered_data[metric].mean():,.2f}")
            with col3:
                st.metric("Median", f"${filtered_data[metric].median():,.2f}")

            # Trend Chart
            st.subheader(f"{metric} Trend")
            trend_data = filtered_data.groupby(['Year', 'Month'])[metric].sum().reset_index()
            trend_data['Date'] = pd.to_datetime(trend_data[['Year', 'Month']].assign(DAY=1))
            fig = px.line(trend_data, x='Date', y=metric, title=f"{metric} Trend Over Time",
                         text=trend_data[metric].round(2).astype(str))
            fig.update_traces(
                textposition="top center",
                textfont=dict(
                    size=14,
                    color='black',
                    family="Arial Black"
                )
            )
            fig.update_layout(
                yaxis_title=f"Total {metric}",
                xaxis_title="Date",
                showlegend=True,
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True)

        with material_tab:
            st.subheader("Material Change Analysis")
            
            # Analysis method selection
            analysis_method = st.radio(
                "Select Analysis Method",
                ["Percentage Change", "Absolute Amount"],
                horizontal=True
            )

            if analysis_method == "Percentage Change":
                threshold = st.number_input(
                    "Enter percentage threshold for material changes",
                    min_value=0.0,
                    max_value=100.0,
                    value=10.0,
                    step=0.1,
                    format="%.1f"
                )
                threshold_type = "percentage"
            else:
                threshold = st.number_input(
                    "Enter amount threshold in shekels",
                    min_value=0.0,
                    value=1000.0,
                    step=100.0,
                    format="%.0f"
                )
                threshold_type = "amount"

            # Calculate changes per employee
            filtered_data = filtered_data.sort_values(['Employee ID', 'Employee Start Date'])
            
            # Calculate changes for each employee separately
            employee_changes = []
            for emp_id in filtered_data['Employee ID'].unique():
                emp_data = filtered_data[filtered_data['Employee ID'] == emp_id].copy()
                emp_data['Change'] = emp_data[metric].pct_change() * 100
                emp_data['Absolute Change'] = emp_data[metric].diff()
                employee_changes.append(emp_data)
            
            # Combine all employee changes
            all_changes = pd.concat(employee_changes)
            
            # Identify material changes
            if threshold_type == "percentage":
                material_changes = all_changes[abs(all_changes['Change']) > threshold]
            else:
                material_changes = all_changes[abs(all_changes['Absolute Change']) > threshold]

            # Display material changes
            st.subheader("Material Changes by Employee")
            
            if not material_changes.empty:
                # Create tabs for each employee with material changes
                employee_tabs = st.tabs([f"Employee {emp_id}" for emp_id in material_changes['Employee ID'].unique()])
                
                for tab, emp_id in zip(employee_tabs, material_changes['Employee ID'].unique()):
                    with tab:
                        emp_material_changes = material_changes[material_changes['Employee ID'] == emp_id]
                        
                        # Calculate summary statistics for this employee
                        total_changes = len(emp_material_changes)
                        avg_change = emp_material_changes['Change'].mean() if threshold_type == "percentage" else emp_material_changes['Absolute Change'].mean()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Material Changes", total_changes)
                        with col2:
                            st.metric("Average Change", 
                                    f"{avg_change:.2f}%" if threshold_type == "percentage" else f"₪{avg_change:,.2f}")
                        
                        # Style the dataframe
                        def highlight_material_changes(row):
                            if threshold_type == "percentage":
                                change = row['Change']
                            else:
                                change = row['Absolute Change']
                            
                            if abs(change) > threshold:
                                return ['background-color: #ffcccc'] * len(row)
                            return [''] * len(row)

                        styled_df = emp_material_changes.style.apply(highlight_material_changes, axis=1)
                        st.dataframe(styled_df, use_container_width=True)
                        
                        # Add a line chart for this employee's changes
                        fig = px.line(emp_material_changes, 
                                    x='Employee Start Date', 
                                    y=metric,
                                    title=f"{metric} Trend for Employee {emp_id}",
                                    text=emp_material_changes[metric].round(2).astype(str))
                        fig.update_traces(
                            textposition="top center",
                            textfont=dict(
                                size=14,
                                color='black',
                                family="Arial Black"
                            )
                        )
                        fig.update_layout(
                            yaxis_title=f"{metric}",
                            xaxis_title="Date",
                            showlegend=True,
                            font=dict(size=14)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                # Download all material changes
                st.download_button(
                    "Download All Material Changes",
                    material_changes.to_csv(index=False),
                    "material_changes.csv",
                    "text/csv"
                )
            else:
                st.info("No material changes found based on the selected threshold.")

        with trends_tab:
            # Department Analysis
            st.subheader("Department Analysis")
            dept_data = filtered_data.groupby(['Year', 'Department'])[metric].sum().reset_index()
            fig = px.bar(dept_data, x='Year', y=metric, color='Department', 
                        title=f"{metric} by Department",
                        text=dept_data[metric].round(2).astype(str))
            fig.update_traces(
                textposition="outside",
                textfont=dict(
                    size=14,
                    color='black',
                    family="Arial Black"
                )
            )
            fig.update_layout(
                yaxis_title=f"Total {metric}",
                xaxis_title="Year",
                showlegend=True,
                uniformtext_minsize=14,
                uniformtext_mode='hide',
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True)

            # Monthly Analysis
            st.subheader("Monthly Analysis")
            monthly_data = filtered_data.groupby('Month')[metric].mean().reset_index()
            monthly_data['Month_Name'] = monthly_data['Month'].apply(lambda x: datetime.strptime(str(x), "%m").strftime("%B"))
            fig = px.line(monthly_data, x='Month_Name', y=metric, 
                         title=f"Average {metric} by Month",
                         text=monthly_data[metric].round(2).astype(str))
            fig.update_traces(
                textposition="top center",
                textfont=dict(
                    size=14,
                    color='black',
                    family="Arial Black"
                )
            )
            fig.update_layout(
                yaxis_title=f"Average {metric}",
                xaxis_title="Month",
                showlegend=True,
                xaxis={'categoryorder': 'array', 'categoryarray': [datetime.strptime(str(m), "%m").strftime("%B") for m in range(1, 13)],
                       'tickfont': dict(size=14)},
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True)

        # Download Options
        st.subheader("Download Data")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download Filtered Data",
                filtered_data.to_csv(index=False),
                "filtered_data.csv",
                "text/csv"
            )
        with col2:
            summary = filtered_data.groupby('Year')[metric].agg(['sum', 'mean', 'median']).reset_index()
            st.download_button(
                "Download Summary",
                summary.to_csv(index=False),
                "summary_stats.csv",
                "text/csv"
            )

# Helper function to format dates according to user
def format_date_column(df, column_name):
    if 'date_formats' in st.session_state and column_name in st.session_state.date_formats:
        date_format = st.session_state.date_formats[column_name]
        format_str = date_format.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
        return df[column_name].dt.strftime(format_str)
    return df[column_name]

# Main app navigation


if app_navigation == "Home":
    home()
elif app_navigation == "Mapping Client Data":
    
    mapping_data("monthly", 
                 ["Employee ID", "Employee Name", "Base Salary","Hourly Rate", "Salary Cost", "Week Work Hours", "Department","Payment Date","Salary","Income Tax Deduction","National Insurance"], 
                 "monthly_column_mapping",
                 'monthly_uploaded')
    
    mapping_data("annual", 
                 ["Employee ID", "Total Payments", "Department","Employee Start Date", "Employee End Date"], 
                 "annual_column_mapping",
                 'annual_uploaded')
    
    # mapping_data("employee", 
    #              ["Employee ID", "Total Gross Salary", "Total Employee Cost"], 
    #              "employee_column_mapping",
    #              'employee_uploaded')
    
elif app_navigation == "Monthly Costing":
    monthly_costing()
elif app_navigation == "Annual Costing":
    annual_costing()
# elif app_navigation == "Employee Calculation":
#     employee_calculation()
