import streamlit as st
from utils import insert_dtc, automaker_db_tables_names_dict, extract_dtcs_from_file
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", override=True)       # Load the .env from the project root

st.title("Add DTC")

# Build table options from the existing dict + generic
automakers = list(automaker_db_tables_names_dict.values())

# Choose the automaker table name where the new dtc will be updated,
# and two text input boxes
automaker = st.selectbox("Automaker", automakers, key="automaker")           
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

#---------------------------PDF Extract from PDF file----------------------------#

st.divider()
st.subheader("Bulk Import from PDF")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")
# Build table options from the existing dict + generic
automakers = list(automaker_db_tables_names_dict.values())


# Initialize the session_state with a standaed value
if "bulk_automaker" not in st.session_state:
    st.session_state["bulk_automaker"] = automakers[0]

bulk_automaker = st.selectbox("Automaker (bulk)", automakers, key="bulk_automaker")

if uploaded_file and st.button("Extract from PDF"):
    with st.spinner("Extracting..."):
        dtcs = extract_dtcs_from_file(uploaded_file)
        st.session_state["bulk_dtcs"] = dtcs
        st.session_state["bulk_table"] = next(
            k for k, v in automaker_db_tables_names_dict.items() if v == bulk_automaker
        )

if "bulk_dtcs" in st.session_state:
    st.write(f"Found {len(st.session_state['bulk_dtcs'])} DTCs:")
    st.dataframe(st.session_state["bulk_dtcs"])         # Show the table to be checked

    if st.button("Insert All into Database", type="primary"):
        try:
            for dtc in st.session_state["bulk_dtcs"]:
                insert_dtc(bulk_automaker, st.session_state["bulk_table"], dtc["code"], dtc["description"])
            st.success(f"{len(st.session_state['bulk_dtcs'])} DTCs inserted sucessfully!")
            del st.session_state["bulk_dtcs"]       # Clean the session state after dtcs insertion
        except Exception as e:
            st.error(f"Error: {e}")