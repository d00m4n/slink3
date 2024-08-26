import sqlite3
from sqlite3 import Error
from datetime import datetime
from os import path
import sys
from typing import Optional, Tuple
import argparse
from flask import Flask, request, render_template

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
                sys.exit(1)

    except Error as e:
        print(f"Error connecting to the database: {e}")
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
    print("Link added successfully!")

def web_server() -> None:
    """
    Start a web server to input data via a web interface
    """
    app = Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        conn = create_connection(dbpath)
        if not conn:
            return "Unable to establish a connection to the database."

        if request.method == 'POST':
            description = request.form['description']
            url = request.form['url']
            type_id = int(request.form['type_id']) if request.form['type_id'] else None
            icon = request.form['icon']
            
            add_link(conn, (datetime.now(), description, url, type_id, icon))
            return "Link added successfully!"
        
        cur = conn.cursor()
        cur.execute("SELECT * FROM type")
        types = cur.fetchall()
        conn.close()
        return render_template('index.html', types=types)

    app.run()

def main() -> None:
    """
    main function
    """
    parser = argparse.ArgumentParser(description='Add a new link to the database.')
    parser.add_argument('-d', '--description', type=str, help='Link description')
    parser.add_argument('-u', '--url', type=str, help='Link URL')
    parser.add_argument('-t', '--type_id', type=int, help='Link type ID')
    parser.add_argument('-i', '--icon', type=str, help='Link icon')
    parser.add_argument('-w', '--web', action='store_true', help='Start web server')
    args = parser.parse_args()

    if args.web:
        web_server()
    else:
        dbc = create_connection(dbpath)
        if dbc:
            if args.description and args.url:
                interactive(dbc, args.description, args.url, args.type_id, args.icon)
            else:
                print("Please provide at least a description and a URL.")
                sys.exit(1)
        else:
            print("Unable to establish a connection to the database. Please check your configuration and try again.")
            sys.exit(1)
            
if __name__ == "__main__":
    main()