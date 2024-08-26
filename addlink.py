import sqlite3
from sqlite3 import Error
from datetime import datetime
from os import path
import sys
from typing import Optional, Tuple

# custom imports
from config import dbpath

def create_connection(db_file: str) -> Optional[sqlite3.Connection]:
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        
        if not path.isfile(dbpath):
            print("Creating new database")
            if path.isfile("base.sql"):
                with open('base.sql', 'r') as f:
                    sql = f.read()
                    conn.executescript(sql)
            else:
                print("No DB schema found.")
                sys.exit()

    except Error as e:
        print(e)

    return conn

def add_link(conn: sqlite3.Connection, task: Tuple[datetime, str, str, int, str]) -> int:
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

def interactive(conn: sqlite3.Connection) -> None:
    """
    interactive mode
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM type")
    rows = cur.fetchall()
    type_value = [f"{row[0]}.- {row[1].capitalize()}" for row in rows]
    type_value_str = ", ".join(type_value)
    
    description = input("- Description: ")
    url = input("- URL: ")
    
    type_select = None
    while type_select is None:
        type_select = int(input(f"- Type ({type_value_str}): "))
        if type_select not in [row[0] for row in rows]:
            type_select = None
            
    icon = input("- Icon: ")
    add_link(conn, (datetime.now(), description, url, type_select, icon))

def main() -> None:
    """
    main function
    """
    dbc = create_connection(dbpath)
    if dbc:
        interactive(dbc)

if __name__ == "__main__":
    main()