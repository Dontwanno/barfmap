import io
import os
from base64 import encodebytes

from PIL import Image
import uuid
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, send_file
)
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db



bp = Blueprint('feed', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, latitude, longitude, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    dict = {index:{key: post[key] for key in post.keys()} for index, post in enumerate(posts)}
    return "hoi dit is een test"


@bp.route('/create', methods=(['POST']))
# @login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        latitude, longitude = request.form['latitude'], request.form['longitude']
        user_id = request.form["userid"]
        db = get_db()
        db.execute(
            'INSERT INTO post (title, body, latitude, longitude, author_id)'
            ' VALUES (?, ?, ?, ?, ?)',
            (title, body, latitude, longitude, user_id)
        )
        db.commit()

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/test', methods=['POST'])
def upload():
    imagefile = request.files.get('imagefile')
    image = Image.open(imagefile)
    image = image.convert("RGB")
    filename = str(uuid.uuid4())
    image.save(os.path.join("./image_lib", filename + ".jpg"))
    return "check"

@bp.route('/test2',methods=['GET'])
def get_images():

    def get_response_image(image_path):
        pil_img = Image.open(image_path, mode='r')  # reads the PIL image
        byte_arr = io.BytesIO()
        pil_img.save(byte_arr, format='png')  # convert the PIL image to byte array
        encoded_img = encodebytes(byte_arr.getvalue()).decode('ascii')  # encode as base64
        return encoded_img

    encoded_imges = []
    result = os.listdir('./image_lib')
    for image_path in result:
        if ".jpg" in image_path:
            encoded_imges.append({image_path: get_response_image(os.path.join('./image_lib/', image_path))})
    return jsonify({"result": encoded_imges})
