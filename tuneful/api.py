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

@app.route("/api/song/<int:id>", methods=["GET"])
def song_get(id):
    """ Single song endpoint """
    song = session.query(Song).get(id)
     
    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")
        
    data = json.dumps(song.as_dictionary())
    return Response(data, 200, mimetype="application/json")
    
@app.route("/api/songs/<id>")
def songs_edit(id):
    """Edit a song"""
    data = request.json
    
    try: 
        validate(data, song_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
        
    song = session.query(Song).get(id)
    song.name = data["file.name"]
    song.file_id = data["file.id"]
    
    session.commit()
    
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for(song_get, id=song.id)}
    return Response(data, 201, headers=headers, mimetype="application/json")

@app.route("/api/songs/<int:id>", methods=["DELETE"])
def song_delete(id):
    """ Delete a single song """
    song = session.query(Song).get(id)
    
    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")
        
    session.delete(song)
    session.commit()
    
    data = json.dumps([])
    return Response(data, 200, mimetype="application/json")
    
