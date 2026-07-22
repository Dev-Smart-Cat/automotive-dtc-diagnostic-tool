import os
import pytest
import psycopg2 as pg
from utils import automaker_db_tables_names_dict, query_descriptions, db_connection, dtc_exists, insert_dtc


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


# Fixture: creates a temporary test table before the test
# the table is dropped after the test, keeping the DB cleaned.
@pytest.fixture
def test_table():
    # Create an object connection and excecute object
    conn = pg.connect(
        HOST_NAME=os.getenv("HOST_NAME"),
        PORT_NUMBER=os.getenv("PORT_NUMBER"),
        DB_NAME=os.getenv("DB_NAME"),
        USER_NAME=os.getenv("USER_NAME"),
        PASSWORD=os.getenv("PASSWORD")
    )
    cur = conn.cursor()

    # Create a temporary table representing the automaker_dtc table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS test_dtcs (
                automaker TEXT,
                code TEXT,
                description TEXT
        )
    """)

    conn.commit()       # Commit the query to create the table

    cur.execute("DROP TABLE IF EXISTS test_dtcs")
    conn.commit()       # Commit drop table command
    # Close dp connection
    cur.close()
    conn.close()


# Test 6: insert a DTC and confirm it exists
def test_insert_and_exists(test_table):
    if not os.getenv("HOST_NAME"):
        pytest.skip("No DB credentials available - skip DB test")

    # Insert a new DTC to the test_table
    inserted = insert_dtc("Ford", test_table, "P0301", "Misfire on Cylinder #1")
    assert inserted is True      # must return true when insertion succeeds

    # Confirm the inserted DTC now exists in the table
    exists = dtc_exists(test_table, "P0301")
    assert exists is True    # must return true if the DTC is found


# Test 7: inserting the same DTC twice must be blocked
def test_insert_duplicate_is_blocked(test_table):
    if not os.getenv("HOST_NAME"):
        pytest.skip("No DB credentials available - skip DB test")

    insert_dtc("Ford", test_table, "P0301", "Misfire on Cylinder #1")

    # Second insert of the same code must return False, indicating it was not inserted
    duplicate = insert_dtc("Ford", test_table, "P0301", "Misfire on Cylinder #1")
    assert duplicate is False       # must return False when the DTC was not inserted because it already exists
