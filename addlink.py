#!/usr/bin/env python3
"""
Mòdul independent per afegir enllaços
Pot funcionar com a CLI, API standalone o ser importat per altres aplicacions
"""

import sqlite3
from sqlite3 import Error
from datetime import datetime
from os import path
import sys
import logging
import argparse
import importlib.util
from typing import Optional, Tuple
from flask import Flask, request, render_template, jsonify

def load_config(config_file):
    """
    Carrega un mòdul de configuració dinàmicament des d'un fitxer
    """
    if not path.isfile(config_file):
        raise FileNotFoundError(f"El fitxer de configuració '{config_file}' no existeix.")
    
    spec = importlib.util.spec_from_file_location("config", config_file)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    return config_module

def setup_logging(log_mode):
    """
    Configura el sistema de logging
    """
    # Neteja handlers existents
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    if log_mode == 'file' or log_mode == 'all':
        file_handler = logging.FileHandler('addlink.log')
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
    """
    Crea una connexió a la base de dades SQLite
    """
    conn = None
    try:
        # Assegura't que el directori existeix
        db_dir = path.dirname(db_file)
        if db_dir and not path.exists(db_dir):
            logging.info(f"Creant directori de base de dades: {db_dir}")
            import os
            os.makedirs(db_dir, exist_ok=True)
        
        if not path.isfile(db_file):
            logging.info(f"Base de dades {db_file} no existeix. Creant nova base de dades.")
            conn = sqlite3.connect(db_file)
            
            if path.isfile("base.sql"):
                logging.info("Important esquema de base de dades des de base.sql")
                with open('base.sql', 'r') as f:
                    sql_statements = f.read().split(';')
                    for statement in sql_statements:
                        if statement.strip():
                            conn.execute(statement)
                conn.commit()
                logging.info("Base de dades creada correctament")
            else:
                logging.warning("No s'ha trobat l'esquema de BD. Assegura't que base.sql existeix.")
                return None
        else:
            logging.info(f"Connectant a la base de dades existent: {db_file}")
            conn = sqlite3.connect(db_file)

    except Error as e:
        logging.error(f"Error connectant a la base de dades: {e}")
        return None

    return conn

def add_link(conn: sqlite3.Connection, task: Tuple[datetime, str, str, Optional[int], str]) -> int:
    """
    Afegeix un nou enllaç a la base de dades
    """
    sql = '''INSERT INTO links(date, description, url, type, icon)
             VALUES(?, ?, ?, ?, ?)'''
    try:
        cur = conn.cursor()
        cur.execute(sql, task)
        conn.commit()
        return cur.lastrowid
    except Error as e:
        logging.error(f"Error afegint l'enllaç: {e}")
        raise

def interactive_add_link(config_module, description: str, url: str, type_id: Optional[int], icon: str) -> None:
    """
    Mode interactiu per afegir enllaços
    """
    try:
        conn = create_connection(config_module.dbpath)
        if not conn:
            raise Exception("No s'ha pogut establir connexió amb la base de dades")
        
        link_id = add_link(conn, (datetime.now(), description, url, type_id, icon))
        conn.close()
        
        logging.info(f"Enllaç afegit correctament amb ID: {link_id}")
        print(f"Enllaç afegit correctament! ID: {link_id}")
        
    except Exception as e:
        logging.error(f"Error en mode interactiu: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def create_web_app(config_module):
    """
    Crea una aplicació Flask standalone per afegir enllaços
    """
    app = Flask(__name__)
    
    # Configura templates si existeix el directori
    template_dir = path.join(path.dirname(__file__), "templates", getattr(config_module, 'theme', 'default'))
    if path.exists(template_dir):
        app.template_folder = template_dir

    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f"Error intern del servidor: {error}")
        return jsonify({"error": "Error intern del servidor", "details": str(error)}), 500

    @app.errorhandler(400)
    def bad_request(error):
        logging.error(f"Sol·licitud incorrecta: {error}")
        return jsonify({"error": "Sol·licitud incorrecta", "details": str(error)}), 400

    @app.route('/', methods=['GET', 'POST'])
    def index():
        try:
            conn = create_connection(config_module.dbpath)
            if not conn:
                return jsonify({"error": "No s'ha pogut connectar a la base de dades"}), 500

            if request.method == 'POST':
                description = request.form.get('description', '').strip()
                url = request.form.get('url', '').strip()
                type_id = request.form.get('type_id')
                icon = request.form.get('icon', '').strip()
                
                # Validació bàsica
                if not description or not url:
                    return jsonify({"error": "Descripció i URL són obligatoris"}), 400
                
                if type_id:
                    try:
                        type_id = int(type_id)
                    except ValueError:
                        type_id = None
                
                link_id = add_link(conn, (datetime.now(), description, url, type_id, icon))
                conn.close()
                
                logging.info(f"Enllaç afegit via web amb ID: {link_id}")
                return jsonify({"message": "Enllaç afegit correctament!", "id": link_id}), 201
            
            # GET request - mostra el formulari
            cur = conn.cursor()
            cur.execute("SELECT * FROM type")
            types = cur.fetchall()
            conn.close()
            
            # Si hi ha templates, usa'ls
            if path.exists(app.template_folder):
                return render_template('addlink.html', types=types)
            else:
                # Formulari HTML simple
                form_html = """
                <!DOCTYPE html>
                <html>
                <head><title>Afegir Enllaç</title></head>
                <body>
                    <h2>Afegir Nou Enllaç</h2>
                    <form method="post">
                        <p>
                            <label>Descripció:</label><br>
                            <input type="text" name="description" required>
                        </p>
                        <p>
                            <label>URL:</label><br>
                            <input type="url" name="url" required>
                        </p>
                        <p>
                            <label>Tipus:</label><br>
                            <select name="type_id">
                                <option value="">Selecciona un tipus</option>
                """
                for type_row in types:
                    form_html += f'<option value="{type_row[0]}">{type_row[1]}</option>'
                
                form_html += """
                            </select>
                        </p>
                        <p>
                            <label>Icona:</label><br>
                            <input type="text" name="icon">
                        </p>
                        <p>
                            <input type="submit" value="Afegir Enllaç">
                        </p>
                    </form>
                </body>
                </html>
                """
                return form_html
                
        except Exception as e:
            logging.error(f"Error en la ruta index: {e}")
            return jsonify({"error": "Error processant la sol·licitud", "details": str(e)}), 500
    
    @app.route('/api/addlink', methods=['POST'])
    def api_addlink():
        try:
            conn = create_connection(config_module.dbpath)
            if not conn:
                return jsonify({"error": "No s'ha pogut connectar a la base de dades"}), 500

            data = request.get_json()
            if not data:
                return jsonify({"error": "No s'han rebut dades JSON"}), 400
            
            description = data.get('description', '').strip()
            url = data.get('url', '').strip()
            type_id = data.get('type_id')
            icon = data.get('icon', '').strip()

            if not description or not url:
                return jsonify({"error": "Descripció i URL són obligatoris"}), 400

            link_id = add_link(conn, (datetime.now(), description, url, type_id, icon))
            conn.close()
            
            logging.info(f"Enllaç afegit via API amb ID: {link_id}")
            return jsonify({"message": "Enllaç afegit correctament!", "id": link_id}), 201

        except Exception as e:
            logging.error(f"Error en l'API: {e}")
            return jsonify({"error": "Error processant la sol·licitud", "details": str(e)}), 500

    @app.route('/health', methods=['GET'])
    def health_check():
        """Endpoint per verificar que el servei funciona"""
        try:
            conn = create_connection(config_module.dbpath)
            if conn:
                conn.close()
                return jsonify({"status": "healthy", "database": "connected"}), 200
            else:
                return jsonify({"status": "unhealthy", "database": "disconnected"}), 503
        except Exception as e:
            return jsonify({"status": "unhealthy", "error": str(e)}), 503

    return app

def main():
    """
    Funció principal
    """
    parser = argparse.ArgumentParser(description='Mòdul per afegir enllaços')
    parser.add_argument('-c', '--config', type=str, default='config.py',
                       help='Fitxer de configuració (per defecte: config.py)')
    parser.add_argument('-d', '--description', type=str, help='Descripció de l\'enllaç')
    parser.add_argument('-u', '--url', type=str, help='URL de l\'enllaç')
    parser.add_argument('-t', '--type_id', type=int, help='ID del tipus d\'enllaç')
    parser.add_argument('-i', '--icon', type=str, default='', help='Icona de l\'enllaç')
    parser.add_argument('-w', '--web', action='store_true', help='Inicia servidor web')
    parser.add_argument('-l', '--log', type=str, choices=['screen', 'file', 'all'], 
                       default='screen', help='Mode de logging')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host del servidor web')
    parser.add_argument('--port', type=int, default=5001, help='Port del servidor web')
    parser.add_argument('--debug', action='store_true', help='Mode debug')
    
    args = parser.parse_args()

    # Configura logging
    setup_logging(args.log)

    try:
        # Carrega configuració
        config = load_config(args.config)
        logging.info(f"Configuració carregada des de: {args.config}")
        
        if args.web:
            # Mode servidor web
            app = create_web_app(config)
            logging.info(f"Iniciant servidor web a {args.host}:{args.port}")
            app.run(host=args.host, port=args.port, debug=args.debug)
        else:
            # Mode línia de comandes
            if args.description and args.url:
                interactive_add_link(config, args.description, args.url, args.type_id, args.icon)
            else:
                logging.error("En mode CLI, descripció i URL són obligatoris")
                print("Error: Proporciona almenys descripció (-d) i URL (-u)")
                sys.exit(1)
                
    except FileNotFoundError as e:
        logging.error(f"Fitxer no trobat: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error general: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()