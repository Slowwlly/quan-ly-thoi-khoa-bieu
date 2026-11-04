"""Ung dung web quan ly thoi khoa bieu. Chay: python app.py  →  http://127.0.0.1:5000"""
import os
import secrets
from flask import Flask, jsonify, send_from_directory
from tkb.db import close_db, init_db
from tkb.errors import AppError
from tkb.seed import seed

ROOT = os.path.dirname(os.path.abspath(__file__))


def create_app(config=None):
    app = Flask(__name__, static_folder=os.path.join(ROOT, 'static'), static_url_path='/static')
    app.config.update(
        DATABASE=os.path.join(ROOT, 'instance', 'tkb.sqlite3'),
        # Dat bien moi truong TKB_SECRET_KEY khi trien khai that; mac dinh sinh ngau nhien moi lan chay.
        SECRET_KEY=os.environ.get('TKB_SECRET_KEY') or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SEED_DEMO=True,
    )
    if config:
        app.config.update(config)
    init_db(app.config['DATABASE'])
    if app.config['SEED_DEMO']:
        seed(app.config['DATABASE'], today=app.config.get('SEED_TODAY'))

    from tkb.controllers import auth, danh_muc, tkb
    for m in (auth, tkb, danh_muc):
        app.register_blueprint(m.bp)
    app.teardown_appcontext(close_db)

    @app.errorhandler(AppError)
    def loi_nghiep_vu(e):
        return jsonify({'loi': e.message}), e.status

    @app.errorhandler(404)
    def khong_thay(_e):
        return jsonify({'loi': 'Khong tim thay'}), 404

    @app.errorhandler(405)
    def sai_phuong_thuc(_e):
        return jsonify({'loi': 'Phuong thuc khong duoc ho tro'}), 405

    @app.errorhandler(Exception)
    def loi_he_thong(e):
        app.logger.exception(e)
        return jsonify({'loi': 'Loi he thong, vui long thu lai'}), 500

    @app.get('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    return app


if __name__ == '__main__':
    create_app().run(debug=True)
