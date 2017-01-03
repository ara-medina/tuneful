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
            "id": {"type": "int"},
            "name": {"type": "string"}
        }
    }
}


@app.route("/api/songs", methods=["GET"])
def songs_get():
    """Get a list of songs as JSON"""
    
    songs = session.query(Song).all()
    songs = songs.order_by(Song.id)
    
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")
    
@app.route("/api/songs", methods=["POST"])
def songs_post():
    """Add a new song to the db"""
    
    data = request.json
    
    try: 
        validate(data, song_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
        
    song = Song(name=data["file.name"], file_id=data["file.id"])
    session.add(song)
    session.commit()
    
    
