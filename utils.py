import io
import re
import os
import requests
import psycopg2 as pg
import pytesseract
from pdf2image import convert_from_bytes


# List with the file names containing the dtcs
automaker_db_tables_names_dict = {
    "acura_dtcs": "Acura",
    "audi_dtcs": "Audi",
    "bmw_dtcs": "BMW",
    "buick_dtcs": "Buick",
    "cadillac_dtcs": "Cadillac",
    "chevrolet_dtcs": "Chevrolet",
    "chrysler_dtcs": "Chrysler",
    "dodge_dtcs": "Dodge",
    "ford_dtcs": "Ford",
    "generic_dtcs": "Generic",
    "geo_dtcs": "Geo",
    "gmc_dtcs": "GMC",
    "honda_dtcs": "Honda",
    "hyundai_dtcs": "Hyundai",
    "hummer_dtcs": "Hummer",
    "infiniti_dtcs": "Infiniti",
    "isuzu_dtcs": "Isuzu",
    "jaguar_dtcs": "Jaguar",
    "jeep_dtcs": "Jeep",
    "kia_dtcs": "Kia",
    "land_rover_dtcs": "Land Rover",
    "lexus_dtcs": "Lexus",
    "mazda_dtcs": "Mazda",
    "mercedes_benz_dtcs": "Mercedes-Benz",
    "mini_dtcs": "Mini",
    "mitsubishi_dtcs": "Mitsubishi",
    "nissan_dtcs": "Nissan",
    "oldsmobile_dtcs": "Oldsmobile",
    "pontiac_dtcs": "Pontiac",
    "saturn_dtcs": "Saturn",
    "subaru_dtcs": "Subaru",
    "toyota_dtcs": "Toyota",
    "volkswagen_dtcs": "Volkswagen"
}


def db_connection():

    """
    Creates and returns a PostgreSQL database connection using credentials from environment variables.

    Returns:
        psycopg2.connection: Active database connection object.
    """

    # Return a object connection with the database from the env vars
    return pg.connect(
        host=os.getenv("HOST_NAME"),
        port=os.getenv("PORT_NUMBER"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("USER_NAME"),
        password=os.getenv("PASSWORD")
    )

def extract_from_pdf(url):

    """
    Downloads a PDF from the given URL, applies OCR on pages 1 and 2,
    and extract the automaker name and DTC codes from RMA from fields.

    Args: url (str): Public URL the RMA PDF form.

    Returns:
        tuple: (make_name, orig_dtcs, fs1_dtcs)
            - make_name (str): Automaker name extracted from page 1.
            - orig_dtcs (list | str): List of DTC codes from the original module, or "no dtcs".
            - fs1_dtcs (list | str): List of DTC codes from the Flagship One module, or "no dtcs".
    """

    # Return the response of te link,
    # 200: meaning it can be access
    # 404: failed to access the PDF
    response = requests.get(url)

    # Virtual PDF file - exists only in RAM, not on disk.
    # Faster access from RAM memory than disk memory.
    # When the program is ended, the memory is released.
    pdf_bytes = io.BytesIO(response.content)

    # Page 1
    # Automaker name extraction
    # Convert from BytesIO object to PIL.Image of page 1
    # dpi (Dots Per Inch): pixels density per inch when converting from image to PDF.
    # As higher as dpi is, better is the image quality
    images_page1 = convert_from_bytes(pdf_bytes.read(), first_page=1, last_page=1, dpi=600)
    # Convert from PIL.Image object to text/string
    ocr_text_page1 = pytesseract.image_to_string(images_page1[0])
    # Seach for the automake name in the page 1
    automake_match = re.search(
        r'VIN For Vehicle[^\n]*\n.*?\d{4}(?!-)\s+([A-Za-z]+)',
        ocr_text_page1, re.DOTALL | re.IGNORECASE
    )
    # Condition to confirm the automaker name was captured
    make_name = (
        automake_match.group(1).strip()
        if automake_match else "Not Automaker"
        )

    # DTC extraction
    orig_dtcs = None

    # Small letters -> use higher DPI -> more pixels per inch -> OCR reads correctly
    # Larger letters -> lower DPI is sufficient -> already enough pixels to recognize them
    # DPI and letter size are inversely proportional - the smaller the test,
    # the higher the DPI needed to capture it accurately.
    for dpi in [600, 200, 100]:
        # Return to the beginning of the page
        pdf_bytes.seek(0)
        images_page1 = convert_from_bytes(pdf_bytes.read(), first_page=1, last_page=1, dpi=dpi)
        ocr_text_page1 = pytesseract.image_to_string(images_page1[0])

        # re.search: search for the pattern in the text
        orig_dtc_field_raw_string = re.search(
            r'Error codes with the ORIGINAL MODULE[^\n]*:\n\n(.*?)(?=\n\n|\Z)',
            ocr_text_page1, re.DOTALL
        )
        # group(1): returns the 2nd part of the string,
        # which is end of the string and remove the spaces
        orig_dtc_field_string = (
            orig_dtc_field_raw_string.group(1).strip()
            if orig_dtc_field_raw_string else "no data extracted"
        )

        if "Steps taken to diagnose" not in orig_dtc_field_string:
            # When valid content was captured
            break

    # re.findall(): return a list with all DTCs found inside the string
    orig_dtcs_match = re.findall(r'[PCBU][0-9A-F]{4}', orig_dtc_field_string, re.IGNORECASE)
    # Condition to get the 2nd part of the string if text was captured
    orig_dtcs = orig_dtcs_match if orig_dtcs_match else orig_dtc_field_string

    # Page 2
    # Scalability performance O(1), meaning iterate over the dpi list once (1) until valid content is captured
    for dpi in [600, 200, 100]:
        pdf_bytes.seek(0)
        images_page2 = convert_from_bytes(pdf_bytes.read(), first_page=2, last_page=2, dpi=dpi)
        ocr_text_page2 = pytesseract.image_to_string(images_page2[0])
        # regex pattern:
        # "Error codes with": literal text, matching exactly those characters
        # . matches any character except newline, * zero or more times,
        # ? matches a few characters as possible
        # .*?: matches anything between the strings "Error codes with" and "MODULE" minimally
        # [^\n]: macthes the rest of the lines after "MODULE", without crossing to the next line
        # : literal colon
        # \n\n: two new line characters between the field name and the content
        # (.*?): capture any character in the group ()
        # (?=\n\n|\Z): (?=) checks what comes next without consuming it, \n\n two blank lines,
        # | or, \Z end of string
        # (?=\n\n|Z): stops capturing text when tow lines are found or at the end of string \Z
        fs1_dtc_field_raw_string = re.search(
            r'Error codes with.*?MODULE[^\n]*:\n\n(.*?)(?=\n\n|\Z)',
            ocr_text_page2, re.DOTALL
        )
        fs1_dtc_field_string = (
            fs1_dtc_field_raw_string.group(1).strip()
            if fs1_dtc_field_raw_string else "no data extracted"
        )
        if "Any Key Instructions" not in fs1_dtc_field_string:
            # Valid content found - stop iterate on the dpi list
            break

    fs1_dtcs_match = re.findall(r'[PCBU][0-9A-F]{4}', fs1_dtc_field_string, re.IGNORECASE)

    if fs1_dtcs_match:
        # group(1): returns the 2nd part of the string, which is end of the string
        # and remove the spaces
        fs1_dtcs = fs1_dtcs_match
    else:
        fs1_dtcs = fs1_dtc_field_string

    return make_name, orig_dtcs, fs1_dtcs


def query_descriptions(make_name, dtc_list, automaker_db_tables_names_dict):

    """
    Queries the PostgreSQL database for descriptions of the give DTC codes.
    When dtc_list is a string (literal text from the form field, not a valif DTC list),
    returns it directly wirhout querying the database.
    Searches the automaker-specific table first, then falls back to generic_dtcs.

    Args:
        make_name (str): Automaker name used to identify the target database table.
        dtc_list (list | str): List of DTC code string to look up,
                               or a literal string when no valid DTCs were found.
    Returns:
        list[dict] | str: List of dicts with keys "code" and "description" for each DTC,
                          or the original literal string when dtc_list is not a list.
    """

    # Return the literal string directly when dtc_list is not a list
    if isinstance(dtc_list, str):
        return dtc_list

    # Reset the table name to avoid this variable
    # inherit the description from the last automaker table name
    automaker_table = None

    # O(1) scalability performance, where iteration over the dict with name_table:
    # make_name is done only once (1),
    # going straight to the value that matches the make_name selected.
    # Opposite method than iterate over the dict even after finding the value O(n)
    reverse_dict = {
        v.lower(): k for k, v in automaker_db_tables_names_dict.items()
        if make_name.lower() == v.lower()
    }

    # Get the make table
    automaker_table = reverse_dict.get(make_name.lower())

    # Call the function to create db connection
    conn = db_connection()
    # psycopg2 object responsible for execute queries
    cur = conn.cursor()

    # List to append the dtcs got from the db
    dtc_descriptions_list = []

    # Iterate over the dtcs extracted from the PDF form to fetch their descriptions
    for dtc_code in dtc_list:

        # Reset the description variable to avoid this variable
        # inherit the description from the last dtc
        description = None

        # Search in the automaker's table
        if automaker_table:
            # Send the query to PostgreSQL to search for the DTC description
            # %s: psycopg2 placeholder used to replace the DTC in Python,
            # equivalent to executing from LOWER(%s) to LOWER('P0420').
            cur.execute(
                f"SELECT description FROM {automaker_table} WHERE LOWER(code) = LOWER(%s)",
                (dtc_code,)
            )
            # Retrieve the first row returned by the query,
            # returning a tuple with the results
            db_result = cur.fetchone()
            # Condition to confirm if the dtc description was fetched
            if db_result:
                # Assign the description value (first column of the returned row, which is tuple)
                # to the variable
                description = db_result[0]

        # Fallback: search in generic_dtcs
        if not description:
            cur.execute(
                "SELECT description FROM generic_dtcs WHERE LOWER(code) = LOWER(%s)",
                (dtc_code,)
            )
            db_result = cur.fetchone()
            if db_result:
                description = db_result[0]

        # NOT FOUND MESSAGE if not found in any table
        if not description:
            description = "DTC NOT IN THE DATABASE"

        # Append the result to a list
        dtc_descriptions_list.append({"code": dtc_code, "description": description})

    # VERY IMPORTANT: always close the database connection
    cur.close()
    conn.close()

    # Return a list with dtc descriptions
    return dtc_descriptions_list


def insert_dtc(automaker, table_name, code, description):

    """
    Inserts a new DTC code and description into the specified table.
    Skips insertion if the code already exists in the table.

    Args:
        automaker (str): Automaker name.
        table_name (str): PostgreSQL table name (e.g. 'generic_dtcs')
        code (str): DTC code (e.g 'U0100')
        description (str): DTC description
    Returns:
        bool: True if inserted, False if code already exists.
    """

    # Check if the DTC already exists before inserting
    if dtc_exists(table_name, code):
        return False
    # Create a object connection
    conn = db_connection()
    # pyscopg2 object responsible for executing queries
    cur = conn.cursor()
    # Insert the data, where %s references each data from each column
    cur.execute(
        f"INSERT INTO {table_name} (automaker, code, description) VALUES (%s, %s, %s)",
        (automaker, code, description)
    )
    # Commit the query
    conn.commit()

    # Close the db connection
    cur.close()
    conn.close()
    return True


def extract_dtcs_from_file(pdf_file):

    """
    Extracts DTC codes and descriptions from an uploaded PDF file via OCR.
    Expects each line in format: CODE Description (e.g. P0100 Mass Air Flow Sensor)

    Returns:
        list[dict]: List of dicts with keys 'code' and 'description'.
    """
    images = convert_from_bytes(pdf_file.read(), dpi=300)
    dtcs = []
    for image in images:
        text = pytesseract.image_to_string(image)
        matches = re.findall(r'([PCBU][0-9A-F]{4})\s+(.+)', text, re.IGNORECASE)
        for code, description in matches:
            dtcs.append({"code": code.upper(), "description": description.strip()})
    return dtcs


def dtc_exists(table, code):

    """
    Checks if a DTC code already exists in the specified table.

    Returns:
        bool: True if the code exists, False otherwise.
    """
    conn = db_connection()
    cur = conn.cursor()
    # SELECT 1 return literal 1 when the code exists
    cur.execute(
        f"SELECT 1 FROM {table} WHERE LOWER (code) = LOWER(%s)",
        (code,)
    )
    # Retrieves the first row returned by the query
    result = cur.fetchone()
    cur.close()
    conn.close()
    # Return False when the code does not exist
    return result is not None


def query_dtc_by_code(code):

    """
    Searches all automaker tables for a given DTC code.
    Groups results by unique descriptions, listing which tables share each description.

    Returns:
        list[dict]: Each dict has 'code', 'description', 'tables' (list of table names).
    """
    conn = db_connection()
    cur = conn.cursor()

    # Append to the dict key: description, value: list of table names
    grouped = {}

    # Loop to iterate over the all tables on the database
    for table_name in automaker_db_tables_names_dict.keys():
        cur.execute(
            f"SELECT code, description FROM {table_name} WHERE LOWER(code) = LOWER(%s)",
            (code,)
        )
        # Retrieves the first row return by the query
        row = cur.fetchone()
        # If row is not None, assign the description (index 1) to desc.
        if row:
            desc = row[1]
            # Condition to confirm the description is not in the dict
            if desc not in grouped:
                # If this description is not yet in grouped dict, initialize it with code,
                # description and empty tables list
                grouped[desc] = {"code": row[0], "description": desc, "tables": []}
            # Append the current table_name to the tables list for its description
            grouped[desc]["tables"].append(table_name)

    cur.close()
    conn.close()
    # Return a list of dicts, each with code, description and tables list
    return list(grouped.values())


def delete_dtc(table_name, dtc):

    """
    Deletes a DTC code from the specified table.

    Args:
        table_name (str): PostgreSQL table name (e.g. 'generic_dtcs').
    Returns:
        bool: True if deleted, False if code was not found.
    """
    # Condition to confirm whether the entered dtc exists in the database,
    # and return False when does not exist
    if not dtc_exists(table_name, dtc):
        return False

    # Create an object connection
    conn = db_connection()
    # psycopg object responsible for executing the query
    cur = conn.cursor()
    # Command to execute the deletion
    cur.execute(
        f"DELETE FROM {table_name} WHERE LOWER(code) = LOWER(%s)",
        (dtc,)
    )
    # Commit the deletion command
    conn.commit()
    cur.close()
    conn.close()
    return True


def log_extraction(pdf_url: str, status: str, orig_wrong_data: str = None, fs1_wrong_data: str = None):

    """
    Save one row per PDF processed into the extraction_log table.

    Args:
        pdf_url (str): The PDF URL that was processed.
        status (str): Extraction result - 'correct' if no fields were flagged,
                      'incorrect' if at least one fields was flagged as wrong.
        orig_wrong_data (str, optional): The Original DTCs text flagged as incorrectly
                                         extracted. None if original was correct.
        fs1_wrong_data (str, optional): The FS1 DTCs text flagged as incorrectly
                                        extracted. None if fs1 was correct.
    Returns:
        None
    """
    conn = db_connection()
    cur = conn.cursor()
    # SQL command to store the PDF extraction stats
    cur.execute(
        """
        INSERT INTO extraction_log (extracted_at, pdf_url, status, orig_wrong_data, fs1_wrong_data)
        VALUES (CURRENT_DATE, %s, %s, %s, %s)
        """,
        (pdf_url, status, orig_wrong_data, fs1_wrong_data)
    )
    # Commit the SQL command
    conn.commit()
    cur.close()
    conn.close()


def get_extraction_stats_by_date(date) -> dict:

    """
    Return correct and incorrect extraction counts for a given date.

    Queries extraction log grouped by status for the provided date.
    Used to display daily performance statistics on the PDF Extractor page.

    Args:
        date (datetime.date): The date to filter extractions by.
    Returns:
        dict: {'correct': int, 'incorrect': int}
    """
    conn = db_connection()
    cur = conn.cursor()
    # SQL command to count the status column
    cur.execute(
        """
        SELECT status, COUNT(*) FROM extraction_log
        WHERE extracted_at = %s
        GROUP BY status
        """,
        (date,)
    )
    rows = cur.fetchall()  # Fetch the data extracted
    cur.close()
    conn.close()
    stats = {"correct": 0, "incorrect": 0}  # Dictionary to append the status results
    # Loop to iterate over fetched rows
    for status, count in rows:
        if status in stats:
            stats[status] = count  # Count each status and append to the dict
    # Return the stats dic
