import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from tuneful import app
from .database import session
from .models import Song, File
from .utils import upload_path



song_schema = {
    "properties": {
        "file": {
            "type": "object",
            "properties": {
                "id" : {
                    "type": "integer"
                }
            }
        }
    }
}

# add tests for this 
@app.route("api/songs", methods=["GET"])
@decorators.accept("application/json")
def song_get():
    """Get a list of songs"""
    
    songs = session.query(Song)
    songs = songs.order_by(Song.id)
    
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")

#add tests for this
@app.route("api/songs", methods=["POST"])
@decorators.accept("application/json")
def song_post():
    """Add a new song"""
    data = request.json
    
    try: 
        validate(data, song_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
        
    song = Song(filename=data["file"]["filename"])
    session.add(song)
    session.commit()
    
    data = json.dumps(song.as_dictionary())
    return Response(data, 201, mimetype="application/json")
    
@app.route("/uploads/<filename>", methods=["GET"])
def uploaded_file(filename):
    """Retrieve files"""
    return send_from_directory(upload_path(), filename)
    
@app.route("/api/files", methods=["POST"])
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
    file = request.files.get("file")
    if not file:
        data = {"message": "Could not find file data"}
        return Response(json.dumps(data), 422, mimetype="application/json")

    filename = secure_filename(file.filename)
    db_file = models.File(filename=filename)
    session.add(db_file)
    session.commit()
    file.save(upload_path(filename))

    data = db_file.as_dictionary()
    return Response(json.dumps(data), 201, mimetype="application/json")
    
    
