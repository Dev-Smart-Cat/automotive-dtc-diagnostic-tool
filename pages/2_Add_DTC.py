import streamlit as st
from utils import insert_dtc, automaker_db_tables_names_dict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", override=True)       # Load the .env from the project root

st.title("Add DTC")

# Build table options from the existing dict + generic
automakers = list(automaker_db_tables_names_dict.values())

# Choose the automaker table name where the new dtc will be updated,
# and two text input boxes
automaker = st.selectbox("Automaker", automakers)           
code = st.text_input("DTC", placeholder="e.g U0100")
desc = st.text_input("DTC Description", placeholder="e.g. Lost Communication with ECM")

if st.button("Add DTC", type="primary"):            # Button to update the db
    if not code.strip() or not desc.strip():        # Condition to show a warning when the button was presses, but no DTC information was given
        st.warning("Please fill in both fields.")
    else:
        try:
            # List compreension for to confirm the get the table name based on the automaker given
            # next(): stops at the first result where v == automaker
            table_name = next(k for k, v in automaker_db_tables_names_dict.items() if v == automaker)
            # Call the function to update the db with the new dtc       
            insert_dtc(automaker, table_name, code.strip().upper(), desc.strip())
            st.success(f"{code.upper()} added to {table_name} sucessfully!")
        except Exception as e:
            st.error(f"Error inserting DTC: {e}")