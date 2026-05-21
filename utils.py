import io
import re
import os
import requests
import psycopg2 as pg
import pytesseract
import streamlit as st
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

    # Convert from BytesIO object to PIL.Image of page 1
    # dpi (Dots Per Inch): pixels density per inch when converting from image to PDF.
    # As higher as dpi is, better is the image quality
    images_page1 = convert_from_bytes(pdf_bytes.read(), first_page=1, last_page=1, dpi=600)

    # Convert from PIL.Image object to text/string
    ocr_text_page1 = pytesseract.image_to_string(images_page1[0])

    # Seach for the automake name in the page 1
    automake_match = re.search(r'VIN For Vehicle[^\n]*\n.*?\d{4}(?!-)\s+([A-Za-z]+)', ocr_text_page1, re.DOTALL | re.IGNORECASE)

    # Condition to confirm the automaker name was captured
    if automake_match:
        # Select the 2nd group on the string where the automaker name is located 
        make_name = automake_match.group(1).strip()
    else:
        make_name = "Not Automaker"

    # re.search: search for the pattern in the text
    orig_dtc_field_raw_string = re.search(r'Error codes with the ORIGINAL MODULE[^\n]*:\n\n(.*?)(?=\n\n|\Z)', ocr_text_page1, re.DOTALL)

    # group(1): returns the 2nd part of the string, which is end of the string
    # and remove the spaces
    orig_dtc_field_string = orig_dtc_field_raw_string.group(1).strip() if orig_dtc_field_raw_string else "no data extracted"

    # re.findall(): return a list with all DTCs found inside the string
    orig_dtcs_match = re.findall(r'[PCBU][0-9A-F]{4}', orig_dtc_field_string, re.IGNORECASE)

    # Condition to get the 2nd part of the string if text was captured
    if orig_dtcs_match:
        # group(1): returns the 2nd part of the string, which is end of the string
        # and remove the spaces 
        orig_dtcs = orig_dtcs_match
    else:
        orig_dtcs = orig_dtc_field_string

    # Page 2

    pdf_bytes.seek(0)
    images_page2 = convert_from_bytes(pdf_bytes.read(), first_page=2, last_page=2, dpi=600)
    ocr_text_page2 = pytesseract.image_to_string(images_page2[0])
    
    fs1_dtc_field_raw_string = re.search(r'Error codes with.*?MODULE[^\n]*:\n\n(.*?)(?=\n\n|\Z)', ocr_text_page2, re.DOTALL)
    fs1_dtc_field_string = fs1_dtc_field_raw_string.group(1).strip() if fs1_dtc_field_raw_string else "no data extracted"

    # Fallback dpi=100 when field content was not captured
    if "Any Key Instructions" in fs1_dtc_field_string:
        pdf_bytes.seek(0)
        images_page2 = convert_from_bytes(pdf_bytes.read(), first_page=2, last_page=2, dpi=100)
        ocr_text_page2 = pytesseract.image_to_string(images_page2[0])
        fs1_dtc_field = re.search(r'Error codes with.*?MODULE[^\n]*:\n{1,2}(.*?)(?=\n\n|\Z)', ocr_text_page2, re.DOTALL)
        fs1_dtc_field_string = fs1_dtc_field.group(1).strip() if fs1_dtc_field else "no data extracted"

        # Fallback dpi=200 when field content still not captured
        if "Any Key Instructions" in fs1_dtc_field_string:
            pdf_bytes.seek(0)
            images_page2 = convert_from_bytes(pdf_bytes.read(), first_page=2, last_page=2, dpi=200)
            ocr_text_page2 = pytesseract.image_to_string(images_page2[0])
            fs1_dtc_field = re.search(r'Error codes with.*?MODULE[^\n]*:\n{1,2}(.*?)(?=\n\n|\Z)', ocr_text_page2, re.DOTALL)
            fs1_dtc_field_string = fs1_dtc_field.group(1).strip() if fs1_dtc_field else "no data extracted" 

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

    # Loop to iterate over the dict with the table names and automakers
    for table_name, maker_name in automaker_db_tables_names_dict.items():
        # Condition using case insensitive to confirm when the automaker matches
        # with the name in the dictionary
        if maker_name.lower() == make_name.lower():
            # Assign the table name to a variable 
            automaker_table = table_name
            break

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
                # Assign the description value (first column of the returned row, which is tuple) to the variable
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

def insert_dtc(automaker, code, description):
    """
    Inserts a new DTC cpde and description into the specified table.

    Args:
        table (str): PostgreSQL table name (e.g. 'generic_dtcs')
        code (str): DTC code (e.g 'U0100')
        description (str): DTC description
    """
    
    conn = db_connection()          # Create a object connection
    cur = conn.cursor()             # pyscopg2 object responsible for executing queries
    # Insert the data, where %s references each data from each column
    cur.execute(
        f"INSERT INTO {automaker} (automaker, code, description) VALUES (%s, %s, %s)",
        (automaker, code, description)
    )
    conn.commit()                   # Commit the query
    
    # Close the db connection
    cur.close()
    conn.close()