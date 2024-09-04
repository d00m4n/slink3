from flask import Flask, request, render_template, jsonify
from datetime import datetime
from dbtools import create_connection, add_link
from config import dbpath

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

@app.route('/api/addlink', methods=['POST'])
def api_addlink():
    conn = create_connection(dbpath)
    if not conn:
        return jsonify({"error": "Unable to establish a connection to the database."}), 500

    data = request.get_json()
    description = data.get('description')
    url = data.get('url')
    type_id = data.get('type_id')
    icon = data.get('icon', '')

    if not description or not url:
        return jsonify({"error": "Please provide at least a description and a URL."}), 400

    add_link(conn, (datetime.now(), description, url, type_id, icon))
    conn.close()

    return jsonify({"message": "Link added successfully!"}), 201

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='192.168.150.11', help='Web server host')
    parser.add_argument('--port', type=int, default=5000, help='Web server port')
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port)