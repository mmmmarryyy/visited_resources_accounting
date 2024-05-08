import sys
sys.dont_write_bytecode = True

import unittest
from app import app, get_db_connection
import sqlite3

class TestApp(unittest.TestCase):
    URL = "http://localhost:5000"

    def setUp(self):
        self.app = app.test_client()
        self.app.application.config['TESTING'] = True
        with app.app_context():
            get_db_connection()
    
    def tearDown(self):
        conn = sqlite3.connect("test.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS visited_links")

    def test_add_valid_links(self):
        links = ["https://www.google.com/", "https://www.youtube.com/"]
        response = self.app.post(f"/visited_links", json={"links": links})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")

    def test_add_invalid_link(self):
        links = ["invalid_url", "https://www.example.com/"]
        response = self.app.post(f"/visited_links", json={"links": links})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], f"bad request (invalid URL `{links[0]}`)")

    def test_add_with_invalid_body(self):
        links = ["invalid_url", "https://www.example.com/"]
        response = self.app.post(f"/visited_links", json={"link": links})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], f"bad request (can't find key `links` in body)")

    def test_get_visited_domains(self):
        links = ["https://www.python.org/", "https://www.djangoproject.com/"]
        self.app.post(f"/visited_links", json={"links": links})

        response = self.app.get(f"/visited_domains")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.assertIn("www.python.org", response.json["domains"])
        self.assertIn("www.djangoproject.com", response.json["domains"])

    def test_empty_get_domains(self):
        response = self.app.get(f"/visited_domains")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.assertEqual([], response.json["domains"])

if __name__ == "__main__":
    unittest.main()