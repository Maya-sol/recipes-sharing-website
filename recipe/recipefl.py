from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from datetime import datetime
from sqlalchemy import or_, func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'My SecRet Key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128))

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return self.password == password

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User', backref='recipes')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4, max=12)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RecipeForm(FlaskForm):
    title = StringField('Recipe Title', validators=[DataRequired(), Length(max=100)])
    ingredients = TextAreaField('Ingredients', validators=[DataRequired()])
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    submit = SubmitField('Post Recipe')

@app.route('/')
def home():
    recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
    return render_template('home.html', recipes=recipes)

@app.route('/register', methods=['GET', 'POST']) 
def register():
    form = RegistrationForm()
    if form.is_submitted():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        print("User added successfully!")
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login')) 
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required 
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(
            title=form.title.data,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            author=current_user
        )
        db.session.add(recipe)
        db.session.commit()
        flash('Recipe posted successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('add.html', form=form)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        recipes = Recipe.query.filter(
            or_(
                func.lower(Recipe.title).contains(func.lower(query)),
                func.lower(Recipe.ingredients).contains(func.lower(query)),
                func.lower(Recipe.instructions).contains(func.lower(query))
            )
        ).order_by(Recipe.created_at.desc()).all()
    else:
        recipes = []
    return render_template('search.html', recipes=recipes, query=query)

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('view_recipe.html', recipe=recipe)

if __name__ == "__main__":
    app.run(debug=True)
