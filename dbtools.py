import sqlite3
from sqlite3 import Error
from datetime import datetime
from os import path
import logging
from typing import Optional, Tuple

def create_connection(db_file: str) -> Optional[sqlite3.Connection]:
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        if not path.isfile(db_file):
            dbpath=path.dirname(db_file)
            logging.info(f"Database file {db_file} does not exist. Creating new database.")
            conn = sqlite3.connect(db_file)
            
            if path.isfile(f"base.sql"):
                logging.info("Importing database schema from base.sql")
                with open(f"base.sql", 'r') as f:
                    sql_statements = f.read().split(';')
                    for statement in sql_statements:
                        if statement.strip():
                            conn.execute(statement)
                conn.commit()
                logging.info("Database created successfully")
            else:
                logging.warning("No DB schema found. Please ensure base.sql exists in the current directory.")
                return None
        else:
            logging.info(f"Connecting to existing database: {db_file}")
            conn = sqlite3.connect(db_file)

    except Error as e:
        logging.error(f"Error connecting to the database: {e}")
        return None

    return conn

def add_link(conn: sqlite3.Connection, task: Tuple[datetime, str, str, Optional[int], str]) -> int:
    """
    Create a new task
    :param conn: Database connection
    :param task: Tuple with link data (date, description, url, type, icon)
    :return: ID of the inserted row
    """

    sql = ''' INSERT INTO links(date,description,url,type,icon)
              VALUES(?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()

    return cur.lastrowid

def interactive(conn: sqlite3.Connection, description: str, url: str, type_id: Optional[int], icon: str) -> None:
    """
    interactive mode
    """
    add_link(conn, (datetime.now(), description, url, type_id, icon))
    logging.info("Link added successfully!")