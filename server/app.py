#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, session
from flask_migrate import Migrate

from models import db, Article, User, ArticleSchema, UserSchema

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

# Maximum number of articles a user can view before hitting the paywall.
MAX_PAGE_VIEWS = 3

@app.route('/clear')
def clear_session():
    # Reset the view counter so the user can browse articles again.
    # Useful for testing the paywall during development.
    session['page_views'] = 0
    return {'message': '200: Successfully cleared session data.'}, 200

@app.route('/articles')
def index_articles():
    articles = [ArticleSchema().dump(a) for a in Article.query.all()]
    return make_response(articles)

@app.route('/articles/<int:id>')
def show_article(id):
    # The paywall lives here on the backend so it can't be bypassed with
    # browser dev tools. The view count is stored in the session, which is
    # cryptographically signed and can't be tampered with by the client.

    # First visit: start the counter at 0 before counting this view.
    session['page_views'] = session.get('page_views', 0)

    # Every request to this route counts as a page view, including
    # repeat views of the same article.
    session['page_views'] += 1

    # Block access once the user has exceeded their free article limit.
    if session['page_views'] > MAX_PAGE_VIEWS:
        return {'message': 'Maximum pageview limit reached'}, 401

    # Still within the free limit: serve the requested article.
    article = Article.query.filter(Article.id == id).first()
    return make_response(ArticleSchema().dump(article), 200)


if __name__ == '__main__':
    app.run(port=5555)
