import streamlit as st
import pandas as pd
from utils import insert_dtc, automaker_db_tables_names_dict, extract_dtcs_from_file, dtc_exists, delete_dtc
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", override=True)       # Load the .env from the project root


#---------------------------Add a single DTC----------------------------#

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

            # Check if the DTC already exists before inserting
            if dtc_exists(table_name, code.strip()):
                st.warning(f"{code.upper()} already exists in {table_name}.")
            else:
                # Call the function to update the db with the new dtc       
                insert_dtc(automaker, table_name, code.strip().upper(), desc.strip())
                st.success(f"{code.upper()} added to {table_name} sucessfully!")
        except Exception as e:
            st.error(f"Error inserting DTC: {e}")

#---------------------------DTCs Extraction from PDF file----------------------------#

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

    df = pd.DataFrame(st.session_state["bulk_dtcs"])
    df.insert(0, "skip", False)         # Checkboc column - True = skip, False = insert

    edited_df = st.data_editor(df, use_container_width=True)

    if st.button("Insert All into Database", type="primary"):
        try:
            to_insert = edited_df[edited_df["skip"] == False]       # Filter out checked rows
            for _, row in to_insert.iterrows():
                insert_dtc(bulk_automaker, st.session_state["bulk_table"], row["code"], row["description"])
            st.success(f"{len(to_insert)} DTCs inserted successfully!")
            del st.session_state["bulk_dtcs"]
        except Exception as e:
            st.error(f"Error: {e}")

#---------------------------Delete DTC----------------------------#

st.divider()

st.subheader("Delete DTC")

# Initialize session_state for delete automaker selectbox
if "delete_automaker" not in st.session_state:
    st.session_state["delete_automaker"] = automaker[0]


delete_automaker = st.selectbox("Automaker", automakers, key="delete_automaker")            # Display the automaker name, which point to the table name
delete_code = st.text_input("DTC to delete", placeholder="e.g. U0100", key="delete_code")   # Text input for the dtc number

# Button to execute the query deletion
if st.button("Delete DTC", type="primary"):
    if not delete_code.strip():     # Condition when no dtc was entered
        st.warning("Please enter a DTC code.")
    else:
        # Error handling when errors occur
        try:
            table_name = next(k for k, v in automaker_db_tables_names_dict.items() if v == delete_automaker)
            deleted = delete_dtc(table_name, delete_code.strip())       # Call the function to delete the dtc
            # Condition to display a success message when deleted,
            # otherwise display a message the dtc was not found.
            if deleted:
                st.success(f"{delete_code.upper()} deleted from {table_name} successfully!")
            else:
                st.warning(f"{delete_code.upper()} not found in {table_name}")
        except Exception as e:
            st.error(f"Error: {e}")
