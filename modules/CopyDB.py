import sqlite3
import os

# Function to copy an existing SQLite database and add a new column 'marked' to each table
def copy_and_modify_db(source_db_path, destination_db_path):
    # Check if the destination database already exists
    if os.path.exists(destination_db_path):
        os.remove(destination_db_path)

    # Connect to the source database
    source_conn = sqlite3.connect(source_db_path)
    source_cursor = source_conn.cursor()

    # Create and connect to the destination database
    destination_conn = sqlite3.connect(destination_db_path)
    destination_cursor = destination_conn.cursor()

    # Query to retrieve the list of tables in the source database
    source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = source_cursor.fetchall()

    for table in tables:
        table_name = table[0]
        # Get the CREATE TABLE statement for the current table
        source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table_name}';")
        create_statement = source_cursor.fetchone()[0]

        # Modify the CREATE TABLE statement to add the 'marked' column
        modified_create_statement = create_statement.replace(")", ", marked TEXT)")

        # Execute the modified CREATE TABLE statement in the destination database
        destination_cursor.execute(modified_create_statement)

        # Copy data from the source table to the destination table
        source_cursor.execute(f"SELECT * FROM {table_name}")
        rows = source_cursor.fetchall()
        column_count = len(source_cursor.description)
        placeholders = ', '.join(['?'] * column_count) + ', ?'  # Extra placeholder for the 'marked' column
        for row in rows:
            destination_cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", row + (None,))

    # Commit changes and close connections
    destination_conn.commit()
    source_conn.close()
    destination_conn.close()

    print(f"Database '{source_db_path}' has been copied to '{destination_db_path}' with modifications.")

# Example usage
source_db = 'Ebbinghaus_last.db'  # Path to the source database
destination_db = 'Ebbinghaus.db'  # Path to the destination database
copy_and_modify_db(source_db, destination_db)
