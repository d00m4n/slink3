import argparse
from datetime import datetime
import sys
import logging
from dbtools import create_connection, add_link, interactive
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

def main() -> None:
    """
    main function
    """
    parser = argparse.ArgumentParser(description='Add a new link to the database.')
    parser.add_argument('-d', '--description', type=str, help='Link description')
    parser.add_argument('-u', '--url', type=str, help='Link URL')
    parser.add_argument('-t', '--type_id', type=int, help='Link type ID')
    parser.add_argument('-i', '--icon', type=str, help='Link icon')
    parser.add_argument('-l', '--log', type=str, choices=['screen', 'file', 'all'], default=log, help='Logging mode')
    args = parser.parse_args()

    setup_logging(args.log)

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