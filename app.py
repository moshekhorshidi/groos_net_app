import app_functions as af
import streamlit as st 
from streamlit_option_menu import option_menu
import pandas as pd 
#import matplotlib.pyplot as plt
import plotly.express as px


# -- set a page config and style -- 

st.set_page_config(page_title = 'Gross Net Analysis WebApp',
                    page_icon=':bar_chart:',
                    layout='wide')

st.title("Gross Net Analysis Web Aplication")

# if needed for page style, after deployment
# header {visibility: hidden;}
# #MainMenu {visibility: hidden;}

app_css_page_style = """

<style>
footer {visibility: hidden;}
</style>

"""
st.markdown (app_css_page_style, unsafe_allow_html=True)

app_nevigation_options_2 = {"Monthly Costing": 1, "Annual Costing": 2, "Employee Calculation": 3}

with st.sidebar:
    app_navigation = option_menu(
        menu_title= 'App Navigation',
        options= list(app_nevigation_options_2),
        icons= ['clock-fill','bar-chart-fill','percent'],
        menu_icon= ['three-dots-vertical']
    )

# --- if app navigation needed to be drop down list. 
#app_nevigation_options = {"Monthly Costing": 1, "Annual Costing": 2, "Employee Calculation": 3}
#app_nav = st.sidebar.selectbox('**App Navigation**', options = list(app_nevigation_options))
# --- if app navigation needed to be drop down list. 

first_page_file = st.sidebar.file_uploader("Uplaod monthly costing file", type=["csv"],key=1)
second_page_file = st.sidebar.file_uploader("Uplaod annual costing file", type=["xlsx"],key=2)
third_page_file = st.sidebar.file_uploader("Upload employee calculation file", type=["xlsx"],key=3)


def monthly_costing():

    left_column, center_column = st.columns(2)

    #file_upload_to_app = st.sidebar.file_uploader("Uplaod monthly costing file", type=["csv"],key=1)
    file_upload_to_app = first_page_file
    
    st.subheader("Monthly costing analysis")

    if file_upload_to_app is None:
        
        st.info("**File Not uploaded**", icon = '🔄')
        st.stop()

    else:
        
        
        # -- load data file to cash memory
        df = af.load_csv_data(file_upload_to_app)
        # -- clean data 
        # -- set data type on file uploded to cash memory
        df["שעות עבודה"] = df["שעות עבודה"].astype(float)
        df["מספר עובד"] =  df["מספר עובד"].astype(str)
        df["מחיר לשעה"] = df["מחיר לשעה"].str.strip().replace("",1).astype(float).fillna(0)
        df['עלות שכר'] = df['שעות עבודה']*df["מחיר לשעה"]
        # add extra col for working hours, need to get more depth data
        df["week_work_hours"] = df["שעות עבודה"]/4
        df['department'] = df['שם מחלקה']
        # present data preview to app user 
        with st.expander("***Click to see file data preview***"):
            st.dataframe(df)

        # -- kpi on page from file
        total_records_in_data_file = df['Row_Number'].count()
        total_distinct_records_in_data_file = df.drop_duplicates().count().iloc[0]
        avg_emp_cost = df['עלות שכר'].mean()
        mid_emp_cost = df['עלות שכר'].median()

        with left_column:
            st.subheader(f'Total Records: {total_records_in_data_file:,}')
            st.subheader(f'Total distinct Records: {total_distinct_records_in_data_file:,}')
        
        with center_column:
            st.subheader(f'Average employee cost: {round(avg_emp_cost,3):,}')
        
        with center_column:
            st.subheader(f'Median employee cost: {round(mid_emp_cost,3):,}')

    try: 
        
        # viz user filter on dataframed under viz, and bar chart vizual element 
        st.subheader("Insert condition on working hours")
        condition_input = float(st.text_input("insert condition: "))
        condition = df['week_work_hours'] < condition_input
        df_filterd = df[condition]
        chart_data_selected = df_filterd[['department','week_work_hours']]
        chart_data_grouped_for_visual = chart_data_selected.groupby("department").count()
        st.bar_chart(chart_data_grouped_for_visual)
        # extra space
        st.markdown("##")
        # viz main pop
        with st.expander("***Click to see the visual related population***"):
            st.table(df_filterd)
            
        file_to_download = af.convert_df(df_filterd)
        st.download_button("Download Result",file_to_download,"Monthly_Result.csv","text/csv",key='download-Monthly-Result')

    except:

        st.info("**Insert number to continue**", icon = '🔄')

def Annual_costing(): 

    st.subheader("Annual costing analysis")
    #file_upload_to_app = st.sidebar.file_uploader("Uplaod annual costing file", type=["xlsx"],key=2)

    file_upload_to_app = second_page_file

    if file_upload_to_app is None:
        st.info("File Not uploaded", icon = '🔄')
        st.stop()

    else:

        left_column, center_column, right_column = st.columns(3)

        df = af.load_excel_data(file_upload_to_app)
        with st.expander("***Click to see file data preview***",expanded=True):
             st.dataframe(df,use_container_width=True)

         # -- kpi on page from file
        total_records_in_data_file = df['Row_Number'].count()
        total_distinct_records_in_data_file = df.drop_duplicates().count().iloc[0]
        avg_total_pay = df['total_payments'].mean()
        mid_total_pay = df['total_payments'].median()

        with left_column:
            st.subheader(f'Total Records: {total_records_in_data_file:,}')
            st.subheader(f'Total distinct Records: {total_distinct_records_in_data_file:,}')
        
        with center_column:
            st.subheader(f'Average employee cost: {round(avg_total_pay,3):,}')
        
        with center_column:
            st.subheader(f'Median employee cost: {round(mid_total_pay,3):,}')

        with right_column:
            total_unique_employee_number = df['emp_number'].nunique()
            st.subheader(f"total unique employees in file: ***{total_unique_employee_number}***")
        
    try: 
            
        left_column, center_column, right_column = st.columns(3)

        # ---- second approch for first pie chart ---- 
        #df_selected_for_first_pie = df[['department_name','total_payments']]
        #df_selected_grouped_for_first_pie = df_selected_for_first_pie.groupby("department_name").sum()
        #first_pie_labels = df_selected_for_first_pie['department_name'].unique().tolist()
        #first_pie_labels_hebrew = [dep_name[::-1] for dep_name in first_pie_labels]
        #sizes_first_pie =  df_selected_grouped_for_first_pie['total_payments'].tolist() 
        
        #fig_first_pie, ax = plt.subplots()
        #ax.pie(sizes_first_pie, labels=first_pie_labels_hebrew, autopct='%3.1f%%',  textprops={'fontsize': 8}, startangle=10)
        #ax.axis('equal')  # pie is drawn as a circle
        #plt.title('Salary Amounts Per Department\n\n')
        # ---- above is a second approch for first pie chart ----

        
        # ---- second approch for second pie chart ---- 
        #df_selected_for_second_pie = df[['department_name','emp_number']]
        #df_selected_grouped_for_second_pie = df_selected_for_second_pie.groupby("department_name").nunique()
        #second_pie_labels = df_selected_for_second_pie['department_name'].unique().tolist()
        #second_pie_labels_hebrew = [ dep_name[::-1] for dep_name in second_pie_labels ]
        #count_size_un = df_selected_grouped_for_second_pie['emp_number'].tolist()

        #total_count = sum(count_size_un)
        #df_selected_grouped_for_second_pie['percentage'] = (df_selected_grouped_for_second_pie['emp_number'] / total_count)
        #count = [ prc * total_count for prc in df_selected_grouped_for_second_pie['percentage'] ] 
        #autopct_format = lambda pct: f'{pct:.1f}%\n({round(pct/100*total_count)})'

        #fig_second_pie, ax_second_pie = plt.subplots()

        #ax_second_pie.pie(count, labels=second_pie_labels_hebrew, autopct = autopct_format,  textprops={'fontsize': 8}, startangle=10)
        #ax_second_pie.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        #plt.title('Total employees Per Department\n\n')
        # ---- above is a second approch for first pie chart ----

        with left_column:
            
            df_selected_for_first_pie = df[['department_name','total_payments']]
            
            fig = px.pie(df_selected_for_first_pie, values='total_payments', names='department_name', title='Total Payments by Department')
            
            fig.update_traces(
            textinfo='percent+label',
            hoverinfo='percent+label',
            insidetextorientation='horizontal',
            outsidetextfont=dict(size=15, color='black'),
            insidetextfont=dict(size=15, color='white'))

            fig.update_layout(uniformtext_minsize=15, uniformtext_mode='show')
            
            st.plotly_chart(fig)

            file_download_first_pie_pop = af.convert_df_utf(df_selected_for_first_pie)
            st.download_button("Download result for first pie",file_download_first_pie_pop,"result_first_pie_chart.csv","csv",key='download-first-pie-file') # need to test the output 

            
        with center_column:

            df_selected_for_second_pie = df[['department_name','emp_number']]

            df_unique = df_selected_for_second_pie.drop_duplicates(subset=['emp_number'])
            
            department_counts = df_unique['department_name'].value_counts()
            
            total_employees = department_counts.sum()
            
            department_percentages = (department_counts / total_employees) * 100

            labels = [f"{department} ({count} employees, {percentage:.2f} %)" for department, count, percentage in zip(department_counts.index, department_counts.values, department_percentages.values)]

            # Create pie chart
            fig = px.pie(data_frame=department_counts,
            values=department_counts.values,
            names=department_counts.index,
            title='Employee Distribution by Department', 
            labels=labels)


            fig.update_traces(textinfo='percent+text+value')
            
            st.plotly_chart(fig)

            file_download_second_pie_pop = af.convert_df(department_percentages)
            st.download_button("Download result for second pie",file_download_second_pie_pop,"result_second_pie_chart.csv","text/csv",key='download-second-pie-file') # need to test the output 

            
        st.subheader("check percent difference")
        df['Percentage Difference'] = df['total_payments'].ffill().pct_change() #* 100.0 
        df['emp_number'] = df['emp_number'].astype(str)

        user_emp_selection = st.selectbox('Choose employee to analyze:', options= df['emp_number'].unique(), placeholder = 'Choose employee number')

        df_selected_for_emp_analysis = df[['emp_number','Percentage Difference','total_payments']]
        df_filterd = df_selected_for_emp_analysis[df_selected_for_emp_analysis['emp_number'] == user_emp_selection]
        df_filterd.set_index('emp_number', inplace=False)
        df_filterd = df_filterd.rename_axis('row number in file', axis=0)
        df_filterd['Table_Row_Number'] = df_filterd.reset_index().index + 1
        
        with st.expander("***See employee related analysis***"):
            employee_total_count_in_file = df_filterd['emp_number'].count().item()
            st.write(f"Employee Selected:  **{user_emp_selection}**")
            st.write(f"Employee total coount:  **{employee_total_count_in_file}**")
            with st.container():
                st.dataframe(
                    df_filterd,
                    use_container_width= True,
                    column_order=['Table_Row_Number','emp_number','total_payments','Percentage Difference'])

            df_for_charts = df_filterd[['Table_Row_Number','total_payments']]
            st.bar_chart(df_for_charts.set_index('Table_Row_Number'), color='total_payments', use_container_width=True)
            st.line_chart(df_for_charts, x = 'Table_Row_Number' , y = 'total_payments')

    except: 

        st.info("result will be presented after uploading a data file")


# ------------ if needed as a section in the appp ----------------------------------
    #try: 
       # st.subheader("check duplicate values")
       #total_pop = df['emp_number'].count()
        #check_uniqe_pop = df['emp_number']
        #st.write(f"total records in file: ***{total_pop}***")
        #check_total_dup = check_uniqe_pop.nunique(0)
        #st.write(f"total unique records in file: ***{check_total_dup}***")
        #duplicate_pop = check_uniqe_pop
        # Value to count occurrences of
        #value_to_count = st.text_input("insert employee number to see if duplicate:")
        # Count occurrences of the value in each row
        #count_per_row = (duplicate_pop == value_to_count).sum(axis=0)
        #st.write(f"total for employee: {count_per_row}")
    #except:
        #st.info("result will be presented after uploading a data file")
# ------------ above code is if needed as a section in the appp ----------------------------------

    st.subheader("highest ranking employee annual salarys")

    try:
            
        max_salary_per_employee = df.groupby('emp_number')['total_payments'].max().reset_index()

        ranked_df = max_salary_per_employee.sort_values(by='total_payments', ascending=False).reset_index(drop=True)
        ranked_df['rank'] = range(1, len(ranked_df) + 1)
        ranked_df = ranked_df[["rank","emp_number","total_payments"]]

        limit_rank = st.selectbox("Choose rank Size/Range",options=ranked_df['rank'] , placeholder="choose rank range")
        
        with st.expander("***Click to see employee salary ranking***"):

            ranked_df_filterd = ranked_df[ranked_df['rank'] <= limit_rank]
            st.write(ranked_df_filterd)

            st.bar_chart(
            ranked_df_filterd, x="rank", y="total_payments", color="emp_number")

            ranking_file_download = af.convert_df(ranked_df_filterd)
            st.download_button("Download ranking result",ranking_file_download,"ranking_result.csv","text/csv",key='download-ranking-file') # need to test the output 
    
    except:
        
        st.info("result will be presented after uploading a data file")


def emp_calc():

    try: 
        
        st.subheader("employee calculation")
        #file_upload_to_app = st.sidebar.file_uploader("Upload employee calculation file", type=["xlsx"],key=3)

        file_upload_to_app = third_page_file

        if file_upload_to_app is None:

            st.info("File Not uploaded", icon = '🔄')
            st.stop()

        else:

            df = af.load_excel_data(file_upload_to_app)
            df['emp_id'] = df['emp_id'].astype(str)
            df['Total_Employer_contribution'] = df['total_emp_cost'] - df['total_gross_salary']

            with st.expander("***Click to see file data preview***"):
                 st.dataframe(df,use_container_width=True)

            filter_emp_number = st.selectbox("Choose employee to analyze:",df['emp_id'].unique())
           
            with st.expander("***Click to see selected employee***"):
                df_filterd = df[df['emp_id'] == filter_emp_number] 
                st.table(df_filterd)

                pension_multi_6 = 0.065
                pension_multi_7 = 0.075
                comp_multi = 0.0833
                edu_multi = 0.075

                ss = 'need more drtails about the calc'
                gemel = df_filterd['total_gross_salary']*pension_multi_6
                gemel1 = df_filterd['total_gross_salary']*pension_multi_7
                comp = df_filterd['total_gross_salary']*comp_multi
                edu = df_filterd['total_gross_salary']*edu_multi

                text = f"""
                
                Calculation of pension provisions for the selected employee:

                value for 6.5% : **{gemel.item()}**

                value for 7.5% : **{gemel1.item()}**

                Calculation of Compensation for the selected employee: 

                Value: **{comp.item()}**
                
                Calculation of aducation fund for the selected employee: 

                Value: **{edu.item()}**

                Calculation of Social Security for the selected employee: 

                Value: **{ss}**

                Total_funding for 6.5%: **{sum(gemel+comp+edu)}**

                Total_funding for 7.5%: **{sum(gemel1+comp+edu)}**
                
                """ 

                st.success(text)
    except:

            st.stop()  

# --- if app navigation needed to be drop down list. 
#app_nevigation_options = {"Monthly Costing": 1, "Annual Costing": 2, "Employee Calculation": 3}
#app_nav = st.sidebar.selectbox('**App Navigation**', options = list(app_nevigation_options))
# --- if app navigation needed to be drop down list. 

if app_nevigation_options_2[app_navigation] == 1:
    monthly_costing()
elif app_nevigation_options_2[app_navigation] == 2:
    Annual_costing()
elif app_nevigation_options_2[app_navigation] == 3:
    emp_calc()
