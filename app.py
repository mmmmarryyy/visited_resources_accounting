from flask import Flask, request, jsonify
import time
from urllib.parse import urlparse
import validators
import sqlite3
import signal
import sys

app = Flask(__name__)

def get_db_connection():
    global conn, cursor
    if app.config['TESTING']:
        conn = sqlite3.connect("test.db", check_same_thread=False)
    else:
        conn = sqlite3.connect("prod.db", check_same_thread=False)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visited_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT NOT NULL,
        timestamp INTEGER NOT NULL
    )
    """)
    conn.commit()

get_db_connection()

flag = False
def signal_handler(sig, frame):
    if flag:
        cursor.execute("DROP TABLE IF EXISTS visited_links")
        conn.commit()
        print("Clear database")

    sys.exit(0)

@app.route("/visited_links", methods=["POST"])
def add_visited_links():
    try:
        data = request.get_json()
        if "links" in data:
            links = data.get("links")
        else:
            return jsonify({"status": f"bad request (can't find key `links` in body)"}), 400
        timestamp = int(time.time())

        for link in links:
            if not validators.url(link):
                app.logger.info(f"link is invalid: {link}")
                return jsonify({"status": f"bad request (invalid URL `{link}`)"}), 400

        for link in links:
            domain = urlparse(link).netloc
            cursor.execute("INSERT INTO visited_links (domain, timestamp) VALUES (?, ?)", (domain, timestamp))
        
        conn.commit()

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        app.logger.error(f"Error processing visited_links request: {str(e)}")
        return jsonify({"status": "internal server error"}), 500


@app.route("/visited_domains", methods=["GET"])
def get_visited_domains():
    try:
        from_ts = request.args.get("from", 0, type=int)
        to_ts = request.args.get("to", int(time.time()), type=int)

        cursor.execute("""
        SELECT DISTINCT domain 
        FROM visited_links 
        WHERE timestamp BETWEEN ? AND ?
        """, (from_ts, to_ts))

        domains = [row[0] for row in cursor.fetchall()]

        return jsonify({"domains": domains, "status": "ok"}), 200

    except Exception as e:
        app.logger.error(f"Error processing visited_domains request: {str(e)}")
        return jsonify({"status": "internal server error"}), 500

if __name__ == "__main__":
    flag = "--clear-db" in sys.argv

    signal.signal(signal.SIGINT, signal_handler)
    app.run(host='0.0.0.0', port=5000, debug=True)