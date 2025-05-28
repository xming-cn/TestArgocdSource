import os
import flask
import psycopg2

DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'default_password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'mydatabase')


app = flask.Flask(__name__)

def get_connection():
    retry_count = 0
    max_retries = 3
    last_error = None

    while retry_count < max_retries:
        try:
            retry_count += 1
            print(f"Connection attempt {retry_count} of {max_retries}")
            
            return psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                connect_timeout=10
            )
        except psycopg2.OperationalError as e:
            last_error = e
            print(f"Connection attempt {retry_count} failed: {str(e)}")
            if retry_count < max_retries:
                import time
                time.sleep(5)  # Wait 5 seconds before retrying
            else:
                print("All connection attempts failed")
                raise last_error

def init_db():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS counters (
                    id SERIAL PRIMARY KEY,
                    count INTEGER DEFAULT 0
                )
            """)
            cursor.execute("INSERT INTO counters (count) VALUES (0) ON CONFLICT DO NOTHING")
            conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/increase_count', methods=['POST'])
def increase_count():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return flask.jsonify({'status': 'error', 'message': 'Could not connect to database'}), 500
        
        cursor = conn.cursor()
        cursor.execute("UPDATE counters SET count = count + 1 WHERE id = 1")
        conn.commit()
        return flask.jsonify({'status': 'success'})
    except Exception as e:
        return flask.jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/get_count', methods=['GET'])
def get_count():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return flask.jsonify({'status': 'error', 'message': 'Could not connect to database'}), 500
            
        cursor = conn.cursor()
        cursor.execute("SELECT count FROM counters WHERE id = 1")
        result = cursor.fetchone()
        if result is None:
            return flask.jsonify({'status': 'error', 'message': 'No counter found'}), 404
        return flask.jsonify({'count': result[0]})
    except Exception as e:
        return flask.jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

init_db()
app.run(host='0.0.0.0', port=80)
