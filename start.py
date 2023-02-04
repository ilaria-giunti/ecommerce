import streamlit as st
import pandas as pd
from pandas_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report
import sys
import os

#setup page
st.set_page_config(page_title='Data Profiler',page_icon='🚀',layout='wide')

#validate file
def validate_file(file):
    filename= file.name
    name, ext=os.path.splitext(filename)
    if ext in('.csv','.xlsx'):
        return ext
    else:
        return False

#validate size
def get_size(file):
    size_byte=sys.getsizeof(file)
    size_mb= size_byte/(1024*1024)
    return size_mb


#sidebar
with st.sidebar:
    uploader_file=st.file_uploader("Upload .csv,.xlsx files not exceeding 10MB")
    if uploader_file is not None:

        st.write("Modes of Operation")

        #display
        minimal=st.checkbox("Do you want minimal report")
        display_mode=st.radio('Display Mode',options=("Primay","Dark","Orange"))
        if display_mode == "Dark":
            dark_mode=True
            orange_mode=False
        elif display_mode =="Orange":
            dark_mode=False
            orange_mode=True
        else:
            dark_mode=False
            orange_mode=False


if uploader_file is not None:
    ext=validate_file(uploader_file)
    if ext:
        file_size= get_size(uploader_file)
        if file_size <= 10:

            if ext == '.csv':
                df=pd.read_csv(uploader_file)
            else:
                xl_file=pd.ExcelFile(uploader_file)
                sheet_tuple=tuple(xl_file.sheet_names)
                sheet_name=st.sidebar.selectbox('Select the Sheet',sheet_tuple)
                df=xl_file.parse(sheet_name)

            #generate report
            #spinner

            with st.spinner("Generating Report"):
                pr= ProfileReport(df,minimal=minimal,dark_mode=dark_mode,orange_mode=orange_mode)

            st_profile_report(pr)
        else:
            st.error(f'Maximum allowed file size is 10MB. But received {file_size} MB')
    else:
        st.error("Kindly Upload only .csv or .xlsx file")
else:
    st.title("Data Profiler")
    st.info("Upload your data in the left sidebar to generate profiling")