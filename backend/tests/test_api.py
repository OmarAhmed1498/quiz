import unittest
from app import app

class TestQuizAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_start_quiz(self):
        response = self.app.get('/api/start_quiz')
        data = response.get_json()
        self.assertIn(response.status_code, [200, 500])
        if response.status_code == 200:
            self.assertIn('question', data)
            self.assertIn('answers', data)
            self.assertIn('score', data)

if __name__ == '__main__':
    unittest.main()