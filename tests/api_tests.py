import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO

import sys; print(list(sys.modules.keys()))
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session, Song, File



class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())

    def test_get_empty_songs(self):
        """ Getting songs from an empty db """
        response = self.client.get("/api/songs", headers=[("Accept", "application/json")])
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data, [])
        
    def test_get_songs(self):
        """ Getting songs from a populated db"""
        songA = Song()
        songA.file.name = "Example Song A"
        
        songB = Song()
        songB.file.name = "Example Song B"
        
        session.add_all([songA, songB])
        session.commit()
        
        response = self.client.get("/api/songs", headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(data), 2)
        
        songA = data[0]
        self.assertEqual(songA["file.name"], "Example Song A")

        songB = data[1]
        self.assertEqual(songB["file.name"], "Example Song B")

        
    def test_get_song(self):
        """ Getting a single song from a populated database """
        songA = Song()
        songA.file.name = "Example Song A"
        
        songB = Song()
        songB.file.name = "Example Song B"
        
        session.add_all([songA, songB])
        session.commit()

        response = self.client.get("/api/songs/{}".format(songB.id), headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        post = json.loads(response.data.decode("ascii"))
        self.assertEqual(songA["file.name"], "Example Song B")

    def test_get_non_existent_song(self):
        """ Getting a single song which doesn't exist """
        response = self.client.get("/api/song/1", headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], "Could not find post with id 1")
        
    def test_unsupported_accept_header(self):
        response = self.client.get("/api/songs", headers=[("Accept", "application/xml")])

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], "Request must accept application/json data")
        
    def test_delete_post(self):
        """ Deleting a single song from a populated database """
        songA = Song()
        songA.file.name = "Example Song A"
        
        songB = Song()
        songB.file.name = "Example Song B"

        session.add_all([songA, songB])
        session.commit()

        response = self.client.delete("/api/songs/{}".format(songB.id))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        song = json.loads(response.data.decode("ascii"))
        
        songs = session.query(Song).all()
        
        self.assertEqual(len(songs), 1)
        self.assertEqual(song, [])
        
    def test_song_post(self):
        """Posting a new song"""

        data = {
            "file": {
                "name": "Just a sample file"
            }
        }
        
        response = self.client.post("/api/songs",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,"/api/songs/1")
        
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["file.name"], "Just a sample file")
        
        songs = session.query(Song).all()
        self.assertEqual(len(songs), 1)
        
        song = songs[1]
        
    def test_unsupported_mimetype(self):
        data = "<xml></xml>"
        
        response = self.client.post("/api/songs",
            data=json.dumps(data),
            content_type="application/xml",
            headers=[("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"],
                         "Request must contain application/json data")
                         
    def test_invalid_data(self):
        data = {
            "file": {
                "name": 99
            }
        }
        
        response = self.client.post("/api/songs", data=json.dumps(data), content_type="application/json", headers=[("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 422)
        
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], "99 is not of type 'string'")
        
  