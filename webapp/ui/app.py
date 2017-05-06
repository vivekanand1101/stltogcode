import os
import uuid
import json

import flask
import werkzeug
from sqlalchemy.exc import SQLAlchemyError

from webapp import APP, SESSION
import webapp.lib
import webapp.lib.model as model


def _allowed_file_format(filename):
    ''' Check if the input file format is correct or not
    At present, just check form file extension '''

    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in APP.config['ALLOWED_EXTENSIONS']


@APP.route('/')
def home():
    ''' The index page of the application '''
    return flask.render_template('index.html')


@APP.route('/uploads', methods=['POST'])
@APP.route('/uploads/', methods=['POST'])
def fileuploads():
    ''' Handler for file uploads '''
    if 'file' not in flask.request.files:
        flask.flash("No file found in request")
        return flask.redirect(flask.url_for('home'))
    file = flask.request.files['file']
    # In case no file is selected
    if file.filename == "":
        flask.flash("No file selected")
        return flask.redirect(flask.url_for('home'))
    if file and _allowed_file_format(file.filename):
        filename = werkzeug.secure_filename(file.filename)
        uid = uuid.uuid4().hex
        file_obj = model.Conversion(
            uid=uid,
            secure_filename=filename
        )
        SESSION.add(file_obj)
        try:
            SESSION.commit()
        except SQLAlchemyError:
            flask.flash('Some db error occured while processing')
            SESSION.rollback()
            return flask.redirect(flask.url_for('home'))
        file.save(os.path.join(APP.config['UPLOAD_FOLDER'], uid + '-' + filename))
        return flask.redirect(flask.url_for('convert_file', uid=uid))

    flask.flash('Only stl files are allowed')
    return flask.redirect(flask.url_for('home'))


@APP.route('/convert/<uid>')
@APP.route('/convert/<uid>/')
def convert_file(uid):
    ''' Converion of file will take place from here '''

    file_obj = webapp.lib.get_file(SESSION, uid)
    if file_obj is None:
        return flask.redirect(flask.url_for('home'))

    # Send the json to a different server for processing
    webapp.lib.send_to_redis(uid)
    return flask.render_template(
        'convert.html', uid=uid, filename=file_obj.secure_filename)


@APP.route('/uploads/<uid>')
@APP.route('/uploads/<uid>/')
def uploaded_file(uid):
    ''' Show the uploaded file '''
    file_obj = webapp.lib.get_file(SESSION, uid)
    if file_obj is None:
        return flask.redirect(flask.url_for('home'))
    return flask.send_from_directory(
        APP.config['UPLOAD_FOLDER'], uid + '-' + file_obj.secure_filename)


@APP.route('/converted/<uid>')
@APP.route('/converted/<uid>/')
def converted_file(uid):
    ''' Show the uploaded file '''
    file_obj = webapp.lib.get_file(SESSION, uid)
    if file_obj is None:
        return flask.redirect(flask.url_for('home'))
    original_extension = file_obj.secure_filename.split('.')[-1]
    new_extension = webapp.APP.config['ALLOWED_EXTENSIONS'][original_extension]
    new_filename = webapp.lib.rreplace(
        file_obj.secure_filename, original_extension, new_extension, 1)
    return flask.send_from_directory(
        APP.config['OUTPUT_FOLDER'], uid + '-' + new_filename, as_attachment=True)
