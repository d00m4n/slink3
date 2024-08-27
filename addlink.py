import sqlite3
from sqlite3 import Error
from datetime import datetime
from os import path
import sys
from typing import Optional, Tuple
import argparse
from flask import Flask, request, render_template
import logging

# custom imports
from config import dbpath, log

def setup_logging(log_mode):
    if log_mode == 'file' or log_mode == 'all':
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)

    if log_mode == 'screen' or log_mode == 'all':
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(stream_handler)

    logging.getLogger().setLevel(logging.INFO)

def create_connection(db_file: str) -> Optional[sqlite3.Connection]:
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        if not path.isfile(db_file):
            logging.info(f"Database file {db_file} does not exist. Creating new database.")
            conn = sqlite3.connect(db_file)
            
            if path.isfile("base.sql"):
                logging.info("Importing database schema from base.sql")
                with open('base.sql', 'r') as f:
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

def web_server() -> None:
    """
    Start a web server to input data via a web interface
    """
    app = Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        conn = create_connection(dbpath)
        if not conn:
            return "Unable to establish a connection to the database. Please check your configuration and try again."

        if request.method == 'POST':
            description = request.form['description']
            url = request.form['url']
            type_id = int(request.form['type_id']) if request.form['type_id'] else None
            icon = request.form['icon']
            
            add_link(conn, (datetime.now(), description, url, type_id, icon))
            conn.close()
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
    parser.add_argument('-l', '--log', type=str, choices=['screen', 'file', 'all'], default=log, help='Logging mode')
    args = parser.parse_args()

    setup_logging(args.log)

    if args.web:
        web_server()
    else:
        dbc = create_connection(dbpath)
        if dbc:
            if args.description and args.url:
                interactive(dbc, args.description, args.url, args.type_id, args.icon)
            else:
                logging.error("Please provide at least a description and a URL.")
                sys.exit(1)
        else:
            logging.error("Unable to establish a connection to the database. Please check your configuration and try again.")
            sys.exit(1)

if __name__ == "__main__":
    main()