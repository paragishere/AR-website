from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import os
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS menu (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    image BLOB,
                    product_link TEXT,
                    description TEXT)''')  # Fixed syntax error
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    conn = get_db_connection()
    items = conn.execute('SELECT id, name, price, product_link FROM menu').fetchall()  # Fetch only necessary columns
    conn.close()
    cart_count = len(session.get('cart', []))
    return render_template('index.html', items=items, cart_count=cart_count)

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'cart' not in session:
        session['cart'] = []
    
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        action = request.form.get('action')
        if action == 'add':
            session['cart'].append(item_id)
        elif action == 'remove' and item_id in session['cart']:
            session['cart'].remove(item_id)
        session.modified = True
    
    conn = get_db_connection()
    cart_items = [conn.execute('SELECT * FROM menu WHERE id = ?', (item,)).fetchone() for item in session['cart']]
    total_price = sum(item['price'] for item in cart_items if item)
    conn.close()
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

# 🔒 Admin Authentication
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"  # Change this!

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))  # Secure admin panel

    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        product_link = request.form['product_link']
        image_file = request.files['image_file']

        if image_file:
            image_data = image_file.read()  # Read the image as binary data
            conn.execute('INSERT INTO menu (name, price, image, product_link, description) VALUES (?, ?, ?, ?, ?)', 
                         (name, price, image_data, product_link, description))
            conn.commit()
    
    items = conn.execute('SELECT id, name, price, product_link FROM menu').fetchall()
    conn.close()
    return render_template('admin.html', items=items)

# Route to serve images from the database
@app.route('/image/<int:item_id>')
def get_image(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT image FROM menu WHERE id = ?', (item_id,)).fetchone()
    conn.close()
    
    if item and item['image']:
        return send_file(io.BytesIO(item['image']), mimetype='image/jpeg')  # Serve image

    return 'No Image Found', 404
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    
    conn = get_db_connection()
    if query:
        items = conn.execute('SELECT * FROM menu WHERE name LIKE ?', ('%' + query + '%',)).fetchall()
    else:
        items = conn.execute('SELECT * FROM menu').fetchall()
    conn.close()
    
    return render_template('index.html', items=items, cart_count=len(session.get('cart', [])))

@app.route('/menu')
def menu():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM menu').fetchall()
    conn.close()
    cart_count = len(session.get('cart', []))
    return render_template('menu.html', items=items, cart_count=cart_count)



if __name__ == '__main__':
    app.run(debug=True)
