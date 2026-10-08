import streamlit as st
from utils import insert_dtc, automaker_db_tables_names_dict, dtc_exists, delete_dtc
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
    # Condition to show a warning when the button was presses, but no DTC information was given
    if not code.strip() or not desc.strip():
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

st.divider()

st.subheader("Delete DTC")

# Initialize session_state for delete automaker selectbox
if "delete_automaker" not in st.session_state:
    st.session_state["delete_automaker"] = automaker[0]

# Display the automaker name, which point to the table name
delete_automaker = st.selectbox("Automaker", automakers, key="delete_automaker")
# Text input for the dtc number
delete_code = st.text_input("DTC to delete", placeholder="e.g. U0100", key="delete_code")

# Button to execute the query deletion
if st.button("Delete DTC", type="primary"):
    # Condition when no dtc was entered
    if not delete_code.strip():
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
