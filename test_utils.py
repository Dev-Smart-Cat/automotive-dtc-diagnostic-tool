import os
import pytest
from utils import automaker_db_tables_names_dict, query_descriptions, db_connection


# Test 1: dictionary structure
def test_automaker_dict_is_not_empty():
    # The dictionary must have automakers in it,
    # to check this, len() check if the dict has content
    assert len(automaker_db_tables_names_dict) > 0


def test_automaker_dict_keys_end_with_dtcs():
    # Every table name in the dict must follow the pattern "automakername_dtcs"
    for key in automaker_db_tables_names_dict:
        assert key.endswith("_dtcs"), f"{key} does not end with '_dtcs'"


def test_automaker_dict_values_are_string():
    # Every automaker name must be a non-empty string
    for key, value in automaker_db_tables_names_dict.items():
        assert isinstance(value, str)
        assert len(value) > 0


# Test 2
def test_query_description_returns_string_when_input_is_string():
    # Tets the first part of the function, when the content
    # of the form is not a dtc and a literal string returns
    result = query_descriptions("Ford", "no dtcs", automaker_db_tables_names_dict)
    assert result == "no dtcs"


# Test 5: database connection
def test_db_connection():
    # Skip the DB credentials when not available
    # This happens on forks or local runs without a .env file
    if not os.getenv("HOST_NAME"):
        pytest.skip("No DB credentials available - skipping DB test")
    
    conn = db_connection()      # Attempt open a Postgres connection
    assert conn is not None     # asserting object exists
    conn.close()                # Close the connection after testing
