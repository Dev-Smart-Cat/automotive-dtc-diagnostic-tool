from utils import *
from pathlib import Path
from dotenv import load_dotenv
import datetime

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

st.title("📊 Extraction Statistics")
st.markdown("Daily performance of the PDF DTC extraction.")
st.divider()

selected_date = st.date_input("Select date", value=datetime.date.today())   # Section to select the date
stats = get_extraction_stats_by_date(selected_date)                         # Call the function to count the PDF extraction performance 

total = stats["correct"] + stats["incorrect"]    # Sum the stats
col1, col2, col3 = st.columns(3)                 # Set 3 columns to show the extraction performance separating by 3 measurements
col1.metric("📄 Total processed", total)         # Total extraction  
col2.metric("✅ Correct", stats['correct'])      # Correct extraction
col3.metric("❌ Incorrect", stats["incorrect"])  # Incorrect extraction