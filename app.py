from utils import *
from pathlib import Path
from dotenv import load_dotenv

# Read variavles from a .env files and sets them in os.environ.
# Path.cwd(): standard Python library used to read the relative path from .env 
load_dotenv(Path(__file__).parent / ".env", override=True)

# ---------------- UI -------------------------
# Call the function to render the UI
render_ui(extract_from_pdf, query_descriptions, automaker_db_tables_names_dict)

# streamlit run app.py --server.port 8502