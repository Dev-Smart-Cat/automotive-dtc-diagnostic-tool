from utils import *
from pathlib import Path
from dotenv import load_dotenv

# Read variables from a .env files and sets them in os.environ.
# parent.parent to read the .env
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

# Initialize the checkbox flags as False when the app starts for the first time.
# The 'if not in' guard prevents resetting the value on every Streamlit rerun.
if "orig_wrong" not in st.session_state:
    st.session_state["orig_wrong"] = False
if "fs1_wrong" not in st.session_state:
    st.session_state["fs1_wrong"] = False

# ---------------- UI -------------------------
st.title("DTC Form Extractor")

# Text box to input the PDF link
url = st.text_input("PDF URL", placeholder="Paste the PDF link here...")

# Button to press after past the PDF link
if st.button("Extract", type="primary"):

    # Condition when the button is pressed and no PDF link present.
    # Otherwise start PDF extraction
    if not url.strip():
        st.warning("Please enter a PDF URL.")
    else:
        # Save PREVIOUS extraction before running new one
        if "pdf_url" in st.session_state:
            # Read current checkbox states 
            orig_flagged = st.session_state["orig_wrong"]   
            fs1_flagged = st.session_state["fs1_wrong"]
            # Read the current output dtc descriptions
            prev_orig = st.session_state.get("orig_dtc_descriptions")
            prev_fs1 = st.session_state.get("fs1_dtc_descriptions")

            # When prev_orig is a list
            # Iterate over all dicts, format each as "code description",
            # then join all lines together using GERERATOR EXPRESSION to be separated by a newline character,
            # and the output should be:
            # P0000 Code 1\nP0001 Code 2
            prev_orig_lines = "\n".join(f"{d['code']} {d['description']}" for d in prev_orig) if isinstance(prev_orig, list) else (prev_orig or "no dtcs")
            prev_fs1_lines = "\n".join(f"{d['code']} {d['description']}" for d in prev_fs1) if isinstance(prev_fs1, list) else (prev_fs1 or "no dtcs")

            # Condition to confirm when the checkboxes for wrong extraction is flagged,
            # resulting in calling the function to store the wrong extraction to the database
            if orig_flagged or fs1_flagged:
                log_extraction(
                    pdf_url=st.session_state["pdf_url"],
                    status="incorrect",
                    orig_wrong_data=prev_orig_lines if orig_flagged else None,
                    fs1_wrong_data=prev_fs1_lines if fs1_flagged else None
                )
            else:
                log_extraction(pdf_url=None, status="correct")

            # Reset to False the checkboxes after ending the current extraction
            st.session_state["orig_wrong"] = False
            st.session_state["fs1_wrong"] = False


        # Display progress
        with st.spinner("Extracting..."):
            try:
                make_name, orig_dtc, fs1_dtc = extract_from_pdf(url)            # Call the function to extract PDF content
                # Query db only when dtcs were found
                orig_dtc_descriptions = query_descriptions(make_name, orig_dtc, automaker_db_tables_names_dict)
                fs1_dtc_descriptions = query_descriptions(make_name, fs1_dtc, automaker_db_tables_names_dict)
                
                # Save the current sections with the automaker, original dtcs, fs1 dtcs
                st.session_state["make_name"] = make_name
                st.session_state["orig_dtc_descriptions"] = orig_dtc_descriptions
                st.session_state["fs1_dtc_descriptions"] = fs1_dtc_descriptions
                st.session_state["pdf_url"] = url

            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

# Display results - persists when switching pages
if "make_name" in st.session_state:
    st.subheader(f"Automaker: {st.session_state['make_name']}")         # Display subheader

    # Retrieve the dtcs descriptions from session state
    orig = st.session_state["orig_dtc_descriptions"]
    fs1 = st.session_state["fs1_dtc_descriptions"]

    # Condition to confirm whether the dtc descriptions is a list.
    # When it is a list, join the code and their descriptions.
    # When it is not a list, assign the literal string to orig_dtc_lines variable to be displayed
    orig_dtc_lines = "\n".join(f"{d['code']} {d['description']}" for d in orig) if isinstance(orig, list) else (orig or "no dtcs")
    fs1_dtc_lines = "\n".join(f"{d['code']} {d['description']}" for d in fs1) if isinstance(fs1, list) else (fs1 or "no dtcs")

    # Checkbox to flag when the data extracted was incorrect
    st.checkbox("Original DTCs incorrectly extracted", key="orig_wrong")
    st.markdown("**Original DTCs**")
    st.code(orig_dtc_lines, language=None)  # Display original dtcs and descriptions in a box

    st.checkbox("FS1 DTCs incorrectly extracted", key="fs1_wrong")
    st.markdown("**FS1 DTCs**")
    st.code(fs1_dtc_lines, language=None)  # Display fs1 dtcs and descriptions in a box