from utils import *
from pathlib import Path
from dotenv import load_dotenv

# Read variables from a .env files and sets them in os.environ.
# parent.parent to read the .env
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

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

            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

# Display results - persists when switching pages
if "make_name" in st.session_state:
    st.subheader(f"Automaker: {st.session_state['make_name']}")         # Display subheader

    # Original dtcs section
    st.markdown("**Original DTCs**")
    # Retrieve the dtcs descriptions from session state
    orig = st.session_state["orig_dtc_descriptions"]
    # Condition to confirm whether the dtc descriptions is a list.
    # When it is a list, join the code and their descriptions.
    # When it is not a list, assign the literal string to orig_dtc_lines variable to be displayed
    orig_dtc_lines = "\n".join(f"{d['code']} {d['description']}" for d in orig) if isinstance(orig, list) else (orig or "no dtcs")
    st.code(orig_dtc_lines, language=None)  # Display original dtcs and descriptions in a box

    # FS1 dtcs section
    st.markdown("**FS1 DTCs**")
    fs1 = st.session_state["fs1_dtc_descriptions"]      # Retrieve the fs1 dtcs descriptions from session state
    fs1_dtc_lines = "\n".join(f"{d['code']} {d['description']}" for d in fs1) if isinstance(fs1, list) else (fs1 or "no dtcs")
    st.code(fs1_dtc_lines, language=None)  # Display fs1 dtcs and descriptions in a box