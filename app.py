from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
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
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response
    return decorated_view

# Decorador para requerir login


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Ruta para el login


@app.route('/', methods=['GET', 'POST'])
@no_cache
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM usuarios WHERE email = %s AND password_hash = %s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['loggedin'] = True
            session['id'] = user['id']
            session['email'] = user['email']
            session['username'] = user['username']
            flash('Inicio de sesión exitoso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas. Intente nuevamente.', 'danger')

    return render_template('login.html')

# Ruta del dashboard (solo accesible si ha iniciado sesión)


@app.route('/dashboard')
@login_required
@no_cache
def dashboard():
    return render_template('dashboard.html', email=session['email'], username=session['username'])

# Ruta para listar todos los clientes


@app.route('/clientes')
@login_required
@no_cache
def cliente():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM clientes ORDER BY id ASC")
    clientes = cur.fetchall()
    cur.close()
    return render_template('clientes.html',
                           clientes=clientes,
                           email=session['email'],
                           username=session['username'])

# Ruta para mostrar formulario de creación de cliente


@app.route('/crear_clientes', methods=['GET', 'POST'])
@login_required
@no_cache
def crear_cliente():
    if request.method == 'POST':
        documento = request.form['documento']
        nombre = request.form['nombres']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        email = request.form['email']
        observaciones = request.form['observaciones']

        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO clientes (documento, nombres, telefono, direccion, email,observaciones)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (documento, nombre, telefono, direccion, email, observaciones))
            mysql.connection.commit()
            cur.close()
            flash('Cliente creado exitosamente!', 'success')
            return redirect(url_for('cliente'))
        except Exception as e:
            flash(f'Error al crear cliente: {str(e)}', 'danger')
            return redirect(url_for('crear_cliente'))

    return render_template('crear_cliente.html',
                           email=session['email'],
                           username=session['username'])

# Ruta para editar un cliente


@app.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
@login_required
@no_cache
def editar_cliente(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        documento = request.form['documento']
        nombre = request.form['nombres']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        email = request.form['email']
        observaciones = request.form['observaciones']
        try:
            cur.execute("""
                UPDATE clientes 
                SET documento = %s,nombres = %s,telefono = %s,direccion = %s, email = %s,  observaciones = %s
                WHERE id = %s
            """, (documento, nombre, telefono, direccion, email, observaciones, id))
            mysql.connection.commit()
            flash('Cliente actualizado exitosamente!', 'success')
            return redirect(url_for('cliente'))
        except Exception as e:
            flash(f'Error al actualizar cliente: {str(e)}', 'danger')
            return redirect(url_for('editar_cliente', id=id))

    # GET request - mostrar formulario con datos actuales
    cur.execute("SELECT * FROM clientes WHERE id = %s", (id,))
    cliente = cur.fetchone()
    cur.close()

    if not cliente:
        flash('Cliente no encontrado', 'danger')
        return redirect(url_for('cliente'))

    return render_template('editar_cliente.html', cliente=cliente)

# Ruta para eliminar un cliente


@app.route('/eliminar_cliente/<int:id>')
@login_required
@no_cache
def eliminar_cliente(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM clientes WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash('Cliente eliminado exitosamente!', 'success')
    except Exception as e:
        flash(f'Error al eliminar cliente: {str(e)}', 'danger')

    return redirect(url_for('cliente'))

# Ruta para crear pagina en mantenimiento


@app.route('/nuevo')
@no_cache
def nuevo():
    if 'loggedin' in session:
        return render_template('nuevo.html', email=session['email'], username=session['username'])
    return redirect(url_for('login'))

# Ruta para cerrar sesión


@app.route('/logout')
@no_cache
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    session.pop('username', None)
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
