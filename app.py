from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
from datetime import datetime
from dbtools import create_connection, add_link, get_links
try:
    from preview_routes import preview_bp
except ImportError:
    print("Warning: preview_routes not found, creating empty blueprint")
    from flask import Blueprint
    preview_bp = Blueprint('preview', __name__)
import os
import sys
import importlib.util
import argparse
import requests
import subprocess
import time
import signal
import atexit
from threading import Thread

class AddLinkService:
    """
    Classe per gestionar el servei addlink com a procés separat
    """
    def __init__(self, config_file, host='127.0.0.1', port=5001):
        self.config_file = config_file
        self.host = host
        self.port = port
        self.process = None
        self.base_url = f"http://{host}:{port}"
        
    def start(self):
        """Inicia el servei addlink"""
        try:
            # Comprova si ja està funcionant
            if self.is_running():
                print(f"Servei addlink ja està funcionant a {self.base_url}")
                return True
                
            print(f"Iniciant servei addlink a {self.base_url}...")
            
            # Inicia el procés addlink
            cmd = [
                sys.executable, 'addlink.py',
                '-c', self.config_file,
                '--web',
                '--host', self.host,
                '--port', str(self.port),
                '--log', 'file'
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Espera que el servei estigui llest
            for _ in range(30):  # Màxim 30 segons
                if self.is_running():
                    print(f"✅ Servei addlink iniciat correctament")
                    return True
                time.sleep(1)
                
            print("❌ Error: El servei addlink no s'ha pogut iniciar")
            return False
            
        except Exception as e:
            print(f"Error iniciant servei addlink: {e}")
            return False
    
    def stop(self):
        """Atura el servei addlink"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print("Servei addlink aturat")
            except subprocess.TimeoutExpired:
                self.process.kill()
                print("Servei addlink forçat a aturar")
            except Exception as e:
                print(f"Error aturant servei addlink: {e}")
    
    def is_running(self):
        """Comprova si el servei està funcionant"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def add_link_via_api(self, description, url, type_id=None, icon=""):
        """Afegeix un enllaç via API del servei"""
        try:
            data = {
                "description": description,
                "url": url,
                "type_id": type_id,
                "icon": icon
            }
            
            response = requests.post(
                f"{self.base_url}/api/addlink",
                json=data,
                timeout=10
            )
            
            if response.status_code == 201:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.json()}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

def load_config(config_file):
    """
    Carrega un mòdul de configuració dinàmicament des d'un fitxer
    """
    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"El fitxer de configuració '{config_file}' no existeix.")
    
    spec = importlib.util.spec_from_file_location("config", config_file)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    return config_module

def create_app(config_module, addlink_service):
    """
    Crea l'aplicació Flask amb la configuració especificada
    """
    # Defineix la ruta absoluta al directori del teu projecte
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Defineix la ruta al teu directori de templates personalitzat
    custom_template_dir = os.path.join(project_dir, "templates", config_module.theme)
    
    # Crea l'aplicació Flask amb la configuració personalitzada
    app = Flask(__name__, template_folder=custom_template_dir)
    app.secret_key = getattr(config_module, 'secret_key', 'dev-secret-key-change-me')
    
    # Registra el blueprint només si existeix
    try:
        app.register_blueprint(preview_bp)
    except Exception as e:
        print(f"Warning: Could not register preview_bp: {e}")
    
    @app.route('/', methods=['GET'])
    def home():
        try:
            return render_template('index.html')
        except Exception as e:
            # Si no hi ha template, retorna HTML simple
            print(f"Warning: Could not render index.html: {e}")
            return '''
            <!DOCTYPE html>
            <html>
            <head><title>SLink3 - Home</title></head>
            <body>
                <h1>Benvingut a SLink3</h1>
                <ul>
                    <li><a href="/addlink">Afegir Enllaç</a></li>
                    <li><a href="/view">Veure Enllaços</a></li>
                    <li><a href="/addlink_iframe">Afegir Enllaç (iframe)</a></li>
                    <li><a href="/service/status">Estat Serveis</a></li>
                </ul>
            </body>
            </html>
            '''

    @app.route('/addlink', methods=['GET', 'POST'])
    def addlink_page():
        """Ruta que utilitza el servei addlink separat"""
        if request.method == 'POST':
            description = request.form.get('description', '').strip()
            url = request.form.get('url', '').strip()
            type_id = request.form.get('type_id')
            icon = request.form.get('icon', '').strip()
            
            if not description or not url:
                if addlink_service:
                    flash('Descripció i URL són obligatoris', 'error')
                    return redirect(url_for('addlink_page'))
                else:
                    return '<h2>Error: Descripció i URL són obligatoris</h2><a href="/addlink">Tornar</a>'
            
            # Converteix type_id a int si és necessari
            if type_id:
                try:
                    type_id = int(type_id)
                except ValueError:
                    type_id = None
            
            # Si hi ha servei addlink, l'utilitza
            if addlink_service and addlink_service.is_running():
                result = addlink_service.add_link_via_api(description, url, type_id, icon)
                
                if result['success']:
                    flash('Enllaç afegit correctament!', 'success')
                    return redirect(url_for('view_links'))
                else:
                    flash(f'Error afegint l\'enllaç: {result["error"]}', 'error')
                    return redirect(url_for('addlink_page'))
            else:
                # Fallback: afegeix directament a la BD
                try:
                    conn = create_connection(config_module.dbpath)
                    if conn:
                        add_link(conn, (datetime.now(), description, url, type_id, icon))
                        conn.close()
                        return '<h2>Enllaç afegit correctament!</h2><a href="/view">Veure enllaços</a> | <a href="/addlink">Afegir altre</a>'
                    else:
                        return '<h2>Error de connexió a la base de dades</h2><a href="/addlink">Tornar</a>'
                except Exception as e:
                    return f'<h2>Error: {e}</h2><a href="/addlink">Tornar</a>'
        
        # GET request - mostra el formulari
        try:
            conn = create_connection(config_module.dbpath)
            if not conn:
                flash('Error de connexió a la base de dades', 'error')
                return redirect(url_for('home'))

            cur = conn.cursor()
            cur.execute("SELECT * FROM type")
            types = cur.fetchall()
            conn.close()
            
            return render_template('addlink.html', types=types)
            
        except Exception as e:
            print(f"Error in addlink_page: {e}")
            # Fallback: formulari HTML simple si no hi ha template
            types_options = ""
            try:
                conn = create_connection(config_module.dbpath)
                if conn:
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM type")
                    types = cur.fetchall()
                    conn.close()
                    for type_row in types:
                        types_options += f'<option value="{type_row[0]}">{type_row[1]}</option>'
            except:
                pass
                
            return f'''
            <!DOCTYPE html>
            <html>
            <head><title>Afegir Enllaç</title></head>
            <body>
                <h2>Afegir Nou Enllaç</h2>
                <form method="post">
                    <p><label>Descripció:</label><br><input type="text" name="description" required></p>
                    <p><label>URL:</label><br><input type="url" name="url" required></p>
                    <p><label>Tipus:</label><br>
                       <select name="type_id">
                           <option value="">Selecciona un tipus</option>
                           {types_options}
                       </select>
                    </p>
                    <p><label>Icona:</label><br><input type="text" name="icon"></p>
                    <p><input type="submit" value="Afegir Enllaç"></p>
                </form>
                <a href="/">← Tornar</a>
            </body>
            </html>
            '''

    @app.route('/addlink_iframe')
    def addlink_iframe():
        """Mostra addlink en un iframe del servei separat"""
        if not addlink_service or not addlink_service.is_running():
            return '''
            <h2>El servei addlink no està disponible</h2>
            <p>Prova d'utilitzar <a href="/addlink">el formulari integrat</a></p>
            <a href="/">← Tornar a l'inici</a>
            '''
        
        try:
            return render_template('addlink_iframe.html', 
                                 addlink_url=addlink_service.base_url)
        except:
            return f'''
            <iframe src="{addlink_service.base_url}" width="100%" height="600px"></iframe>
            <a href="/">← Tornar</a>
            '''

    @app.route('/view', methods=['GET'])
    def view_links():
        try:
            conn = create_connection(config_module.dbpath)
            if not conn:
                return '<h2>Error de connexió a la base de dades</h2><a href="/">← Tornar</a>'

            order = request.args.get('order', 'desc')
            limit = int(request.args.get('limit', 10))

            links = get_links(conn, order=order, limit=limit)
            conn.close()

            try:
                return render_template('view.html', links=links)
            except:
                # Fallback HTML
                links_html = ""
                for link in links:
                    links_html += f'''
                    <li>
                        <strong>{link[2]}</strong><br>
                        <a href="{link[3]}" target="_blank">{link[3]}</a><br>
                        <small>Data: {link[1]} | Tipus: {link[5]} | Icona: {link[4]}</small>
                    </li>
                    '''
                
                return f'''
                <!DOCTYPE html>
                <html>
                <head><title>Enllaços</title></head>
                <body>
                    <h2>Enllaços ({len(links)})</h2>
                    <ul>{links_html}</ul>
                    <a href="/">← Tornar</a>
                </body>
                </html>
                '''
        except Exception as e:
            return f'<h2>Error: {e}</h2><a href="/">← Tornar</a>'

    @app.route('/api/links', methods=['GET'])
    def api_links():
        conn = create_connection(config_module.dbpath)
        if not conn:
            return jsonify({"error": "Unable to establish a connection to the database."}), 500

        order = request.args.get('order', 'desc') 
        limit = int(request.args.get('limit', 10))

        links = get_links(conn, order=order, limit=limit)
        conn.close()

        return jsonify(links), 200

    @app.route('/api/addlink', methods=['POST'])
    def api_addlink():
        """API que delega al servei addlink"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "No s'han rebut dades JSON"}), 400
        
        description = data.get('description', '').strip()
        url = data.get('url', '').strip()
        type_id = data.get('type_id')
        icon = data.get('icon', '').strip()

        if not description or not url:
            return jsonify({"error": "Descripció i URL són obligatoris"}), 400

        # Delega al servei addlink
        result = addlink_service.add_link_via_api(description, url, type_id, icon)
        
        if result['success']:
            return jsonify(result['data']), 201
        else:
            return jsonify({"error": result['error']}), 500

    @app.route('/service/status')
    def service_status():
        """Estat del servei addlink"""
        status = {
            "addlink_service": {
                "running": addlink_service.is_running(),
                "url": addlink_service.base_url
            }
        }
        return jsonify(status)
    
    return app

def main():
    """
    Funció principal que gestiona els arguments de línia de comandes
    """
    parser = argparse.ArgumentParser(description='Executa l\'aplicació Flask amb servei addlink separat')
    parser.add_argument('-c', '--config', type=str, default='config.py', 
                       help='Ruta al fitxer de configuració (per defecte: config.py)')
    parser.add_argument('--host', type=str, default='127.0.0.1', 
                       help='Adreça del servidor web principal (per defecte: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, 
                       help='Port del servidor web principal (per defecte: 5000)')
    parser.add_argument('--addlink-host', type=str, default='127.0.0.1',
                       help='Adreça del servei addlink (per defecte: 127.0.0.1)')
    parser.add_argument('--addlink-port', type=int, default=5001,
                       help='Port del servei addlink (per defecte: 5001)')
    parser.add_argument('--debug', action='store_true', 
                       help='Executa en mode debug')
    parser.add_argument('--no-addlink-service', action='store_true',
                       help='No inicia el servei addlink separat')
    
    args = parser.parse_args()
    
    try:
        # Carrega la configuració
        config = load_config(args.config)
        print(f"Configuració carregada des de: {args.config}")
        
        # Crea el servei addlink
        addlink_service = None
        if not args.no_addlink_service:
            addlink_service = AddLinkService(
                args.config,
                args.addlink_host,
                args.addlink_port
            )
            
            # Inicia el servei addlink
            if not addlink_service.start():
                print("Advertència: No s'ha pogut iniciar el servei addlink")
                print("L'aplicació funcionarà sense el servei addlink")
                addlink_service = None
            
            # Registra la funció per aturar el servei en sortir
            if addlink_service:
                atexit.register(addlink_service.stop)
        
        # Crea l'aplicació principal
        app = create_app(config, addlink_service)
        
        print(f"Iniciant aplicació principal a {args.host}:{args.port}")
        if addlink_service and addlink_service.is_running():
            print(f"Servei addlink disponible a {addlink_service.base_url}")
        
        # Executa l'aplicació principal
        app.run(host=args.host, port=args.port, debug=args.debug)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error carregant la configuració: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAturant aplicació...")
        sys.exit(0)

if __name__ == '__main__':
    main()