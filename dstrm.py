import pandas as pd
import os
import streamlit as st

# Function to read the main file based on extension
def read_main_file(file):
    file_extension = file.name.split('.')[-1].lower()
    if file_extension == 'csv':
        return pd.read_csv(file, usecols=['VENDITEMID'], dtype={'VENDITEMID': str}, encoding='ISO-8859-1')
    elif file_extension == 'xlsx':
        return pd.read_excel(file, usecols=['VENDITEMID'], dtype={'VENDITEMID': str})
    else:
        st.error("Unsupported file type! Please upload a CSV or Excel file.")
        return None

# Function to process each subfile in chunks
def process_subfile(file2, chunk_size=100000):
    chunk_iter = pd.read_csv(file2, usecols=['ItemCode', 'ItemName', 'InvQty', 'ConvFact'], dtype={'ItemCode': str}, encoding='ISO-8859-1', chunksize=chunk_size)
    
    for chunk in chunk_iter:
        chunk['ItemCode'] = chunk['ItemCode'].str.strip().str.lstrip('0').str.upper()
        merged_df = pd.merge(df1, chunk, left_on='VENDITEMID', right_on='ItemCode', how='right', indicator=True)
        unmatched_df = merged_df[merged_df['_merge'] == 'right_only']
        result_df = unmatched_df[['ItemCode', 'ItemName', 'InvQty', 'ConvFact']].drop_duplicates(subset=['ItemCode'])
        global all_unmatched_data
        all_unmatched_data = pd.concat([all_unmatched_data, result_df], ignore_index=True)

# Streamlit application layout
st.title("File Processing")

# Upload the main file (file1) - CSV or Excel
main_file = st.file_uploader("Upload Main File (file1)", type=['csv', 'xlsx'])
if main_file is not None:
    df1 = read_main_file(main_file)
    if df1 is not None:
        df1['VENDITEMID'] = df1['VENDITEMID'].str.strip().str.lstrip('0').str.upper()

# Upload multiple subfiles (file2) - CSV only
subfiles = st.file_uploader("Upload Subfiles (file2)", type=['csv'], accept_multiple_files=True)
if subfiles:
    st.write(f"Processing {len(subfiles)} subfiles...")

    # Initialize empty dataframe for unmatched data
    all_unmatched_data = pd.DataFrame()

    # Process each subfile
    for file2 in subfiles:
        st.write(f"Processing {file2.name}...")
        process_subfile(file2)

    # Save all unmatched data to a single CSV file
    output_file = os.path.join(os.path.dirname(main_file.name), "all_unmatched_data.csv")
    all_unmatched_data.to_csv(output_file, index=False)
    
    st.write(f"All unmatched data saved to {output_file}")
    st.success("Processing complete. Results saved to all_unmatched_data.csv")
