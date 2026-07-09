import streamlit as st
from utils import query_dtc_by_code
from pathlib import Path
from dotenv import load_dotenv

# Load the .env from the project root
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

st.title("DTC Research")  # Set the page title

dtc = st.text_input("DTC Code", placeholder="e.g. P0300")  # space to input the code

# Condition to press the button and start the searching code process
if st.button("Search", type="primary"):
    if not dtc.strip():
        st.warning("Please enter a DTC code.")  # Warning when button is pressed without dtc input
    else:
        with st.spinner("Searching..."):        # Message showing code searching
            # Only the UI layer is responsible for error handling,
            # it is not responbility to utils.py handle errors
            try:
                results = query_dtc_by_code(dtc.strip())       # Call the function to query the dtc
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

        # Condition whether the dtc was found or not
        if not results:
            st.info(f"{dtc.upper()} not found in any table.")
        else:
            for r in results:
                # Display the dtc and description
                st.code(f"{r['code']} {r['description']}", language=None)
                # Display the table name (s) the dtc comes from
                st.caption(f"Found in: {', '.join(r['tables'])}")
