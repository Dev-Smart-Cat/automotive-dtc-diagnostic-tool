import streamlit as st
from utils import insert_dtc, automaker_db_tables_names_dict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", override=True)       # Load the .env from the project root

st.title("Add DTC")

# Build table options from the existing dict + generic
table_options = list(automaker_db_tables_names_dict.keys())

table = st.selectbox("Automaker", table_options)
code = st.text_input("DTC", placeholder="e.g U0100")
desc = st.text_input("DTC Description", placeholder="e.g. Lost Communication with ECM")

if st.button("Add", type="primary"):
    if not code.strip() or not desc.strip():
        st.warning("Please fill in both fields.")
    else:
        try:
            insert_dtc(table, code.strip().upper(), desc.strip())
            st.success(f"{code.upper()} added to {table} sucessfully!")
        except Exception as e:
            st.error(f"Error inserting DTC: {e}")