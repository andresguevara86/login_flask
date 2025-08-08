from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import make_response
from flask_mysqldb import MySQL
import config
from functools import wraps

app = Flask(__name__)
app.secret_key = 'Andres_123'
# CONFIGURACION DE MYSQL
app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB
app.config['MYSQL_CURSORCLASS'] = config.MYSQL_CURSORCLASS

mysql = MySQL(app)
# Decorador para deshabilitar la caché


def no_cache(view):
    @wraps(view)
    def decorated_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response
    return decorated_view

# Ruta para el login


@app.route('/', methods=['GET', 'POST'])
@no_cache
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM usuario WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['loggedin'] = True
            session['id'] = user['id']
            session['email'] = user['email']
            session['usuario'] = user['usuario']
            flash('Inicio de sesión exitoso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas. Intente nuevamente.', 'danger')

    return render_template('login.html')

# Ruta del dashboard (solo accesible si ha iniciado sesión)


@app.route('/dashboard')
@no_cache
def dashboard():
    if 'loggedin' in session:
        return render_template('dashboard.html', email=session['email'], usuario=session['usuario'])
    return redirect(url_for('login'))

# Ruta para cerrar sesión


@app.route('/nuevo')
@no_cache
def nuevo():
    if 'loggedin' in session:
        return render_template('nuevo.html', email=session['email'], usuario=session['usuario'])
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
