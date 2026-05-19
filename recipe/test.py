import pytest
import sqlalchemy as sa
from sqlalchemy.pool import StaticPool
from recipefl import app, db, Recipe

@pytest.fixture
def client():
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True

    test_engine = sa.create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )

    with app.app_context():
        original_engines = db._app_engines.get(app)
        db._app_engines[app] = {None: test_engine}
        db.create_all()
        with app.test_client() as test_client:
            yield test_client
        db.drop_all()
        db.session.remove()
        test_engine.dispose()
        if original_engines is not None:
            db._app_engines[app] = original_engines
        else:
            db._app_engines.pop(app, None)

    app.config['WTF_CSRF_ENABLED'] = True
    app.config['TESTING'] = False





def register(client):
    return client.post('/register', data={
        'username': 'alice',
        'email': 'alice@example.com',
        'password': 'pass1',
        'confirm': 'pass1',
    }, follow_redirects=True)


def login(client):
    return client.post('/login', data={
        'username': 'alice',
        'password': 'pass1',
    }, follow_redirects=True)


def test_home_loads(client):
    assert client.get('/').status_code == 200

def test_register_page_loads(client):
    assert client.get('/register').status_code == 200

def test_login_page_loads(client):
    assert client.get('/login').status_code == 200



def test_register(client):
    rv = register(client)
    assert b'Login' in rv.data

def test_login(client):
    register(client)
    rv = login(client)
    assert b'Welcome' in rv.data

def test_wrong_password(client):
    register(client)
    rv = client.post('/login', data={'username': 'alice', 'password': 'wrong'},
                     follow_redirects=True)
    assert b'Login' in rv.data

def test_logout(client):
    register(client)
    login(client)
    rv = client.get('/logout', follow_redirects=True)
    assert b'Welcome' in rv.data

def test_add_recipe(client):
    register(client)
    login(client)
    rv = client.post('/add', data={
        'title': 'Pasta',
        'ingredients': 'Noodles',
        'instructions': 'Boil',
    }, follow_redirects=True)
    assert b'Pasta' in rv.data


def test_add_recipe_requires_login(client):
    rv = client.get('/add')
    assert rv.status_code == 302

def test_view_recipe(client):
    register(client)
    login(client)
    client.post('/add',
                data={'title': 'Soup', 'ingredients': 'Water', 'instructions': 'Boil'},
                follow_redirects=True)
    recipe = Recipe.query.first()
    rv = client.get(f'/recipe/{recipe.id}')
    assert b'Soup' in rv.data

def test_view_missing_recipe(client):
    assert client.get('/recipe/999').status_code == 404


def test_search(client):
    register(client)
    login(client)
    client.post('/add',
                data={'title': 'Soup', 'ingredients': 'Water', 'instructions': 'Boil'},
                follow_redirects=True)
    rv = client.get('/search?q=soup')
    assert b'soup' in rv.data

def test_search_no_results(client):
    rv = client.get('/search?q=xyzzy')
    assert b'xyzzy' in rv.data
