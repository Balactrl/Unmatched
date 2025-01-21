import pandas as pd
import streamlit as st
from io import BytesIO

# Function to read the main file based on extension
def read_main_file(file):
    file_extension = file.name.split('.')[-1].lower()
    try:
        if file_extension == 'csv':
            return pd.read_csv(file, usecols=['VENDITEMID'], dtype={'VENDITEMID': str}, encoding='ISO-8859-1')
        elif file_extension == 'xlsx':
            return pd.read_excel(file, usecols=['VENDITEMID'], dtype={'VENDITEMID': str})
        else:
            st.error("Unsupported file type for main file! Please upload a CSV or Excel file.")
            return None
    except Exception as e:
        st.error(f"Error reading main file: {e}")
        return None

# Function to process each subfile in chunks
def process_subfile(file2, df1, all_unmatched_data, chunk_size=100000):
    try:
        chunk_iter = pd.read_csv(file2, usecols=['ItemCode', 'ItemName', 'InvQty', 'ConvFact'], dtype={'ItemCode': str}, encoding='ISO-8859-1', chunksize=chunk_size)
        for chunk in chunk_iter:
            chunk['ItemCode'] = chunk['ItemCode'].str.strip().str.lstrip('0').str.upper()
            merged_df = pd.merge(df1, chunk, left_on='VENDITEMID', right_on='ItemCode', how='right', indicator=True)
            unmatched_df = merged_df[merged_df['_merge'] == 'right_only']
            result_df = unmatched_df[['ItemCode', 'ItemName', 'InvQty', 'ConvFact']].drop_duplicates(subset=['ItemCode'])
            all_unmatched_data = pd.concat([all_unmatched_data, result_df], ignore_index=True)
        return all_unmatched_data
    except Exception as e:
        st.error(f"Error processing subfile {file2.name}: {e}")
        return all_unmatched_data

# Function to convert DataFrame to Excel
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Unmatched Data')
    processed_data = output.getvalue()
    return processed_data

# Streamlit application layout
st.title("File Processing with Multi-File Support")

# Upload the main file (file1) - CSV or Excel
main_file = st.file_uploader("Upload Main File (file1) - CSV or Excel", type=['csv', 'xlsx'])
if main_file is not None:
 
    df1 = read_main_file(main_file)
    if df1 is not None:
        df1['VENDITEMID'] = df1['VENDITEMID'].str.strip().str.lstrip('0').str.upper()
      

# Upload multiple subfiles (file2) - CSV only
subfiles = st.file_uploader("Upload Subfiles (file2) - CSV Only", type=['csv'], accept_multiple_files=True)
if subfiles and main_file is not None and df1 is not None:
    st.write(f"Processing {len(subfiles)} subfiles...")

    # Initialize an empty dataframe for unmatched data
    all_unmatched_data = pd.DataFrame()

    # Process each subfile
    for file2 in subfiles:
        st.write(f"Processing {file2.name}...")
        all_unmatched_data = process_subfile(file2, df1, all_unmatched_data)

    # If unmatched data exists, allow downloading it
    if not all_unmatched_data.empty:
        st.write("Processing complete!")
        st.write("Preview of unmatched data:")
        st.dataframe(all_unmatched_data.head())

        # Convert the DataFrame to Excel and add a download button
        excel_data = convert_df_to_excel(all_unmatched_data)
        st.download_button(
            label="Download Unmatched Data as Excel",
            data=excel_data,
            file_name="all_unmatched_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.write("No unmatched data found.")
