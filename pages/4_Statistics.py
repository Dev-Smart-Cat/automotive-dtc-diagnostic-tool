import streamlit as st
from utils import get_extraction_stats_by_date
from pathlib import Path
from dotenv import load_dotenv
import datetime

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

st.title("📊 Extraction Statistics")
st.markdown("Daily performance of the PDF DTC extraction.")
st.divider()

selected_date = st.date_input("Select date", value=datetime.date.today())   # Section to select the date

try:
    # Call the function to count the PDF extraction performance
    stats = get_extraction_stats_by_date(selected_date)
    # Sum the stats
    total = stats["correct"] + stats["incorrect"]
    # Set 3 columns to show the extraction performance separating by 3 measurements
    col1, col2, col3 = st.columns(3)
    # Total extraction
    col1.metric("📄 Total processed", total)
    # Correct extraction
    col2.metric("✅ Correct", stats['correct'])
    # Incorrect extraction
    col3.metric("❌ Incorrect", stats["incorrect"])

except Exception as e:
    st.error(f"Error: {e}")
