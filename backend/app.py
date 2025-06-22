from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import html
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configure session with retry mechanism
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# Fetch questions from OpenTDB API
def get_questions():
    url = "https://opentdb.com/api.php?amount=10&type=multiple"
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('response_code') != 0:
            raise Exception(f"API error: Response code {data.get('response_code')}")
        questions = []
        for item in data['results']:
            question = {
                'text': html.unescape(item['question']),
                'correct': html.unescape(item['correct_answer']),
                'incorrect': [html.unescape(ans) for ans in item['incorrect_answers']],
            }
            question['answers'] = question['incorrect'] + [question['correct']]
            random.shuffle(question['answers'])
            questions.append(question)
        return questions
    except (requests.exceptions.RequestException, KeyError, ValueError) as e:
        app.logger.error(f"Failed to fetch questions: {e}")
        return []

# Store quiz state (in-memory for simplicity)
quiz_state = {
    'questions': [],
    'current_index': 0,
    'score': 0
}

@app.route('/api/start_quiz', methods=['GET'])
def start_quiz():
    global quiz_state
    quiz_state = {
        'questions': get_questions(),
        'current_index': 0,
        'score': 0
    }
    if not quiz_state['questions']:
        return jsonify({'error': 'Failed to fetch questions'}), 500
    return jsonify({
        'question': quiz_state['questions'][0]['text'],
        'answers': quiz_state['questions'][0]['answers'],
        'score': quiz_state['score']
    })

@app.route('/api/answer', methods=['POST'])
def answer():
    global quiz_state
    data = request.json
    user_answer = data['answer']
    current_question = quiz_state['questions'][quiz_state['current_index']]
    
    if user_answer == current_question['correct']:
        quiz_state['score'] += 1
        quiz_state['current_index'] += 1
        if quiz_state['current_index'] < len(quiz_state['questions']):
            next_question = quiz_state['questions'][quiz_state['current_index']]
            return jsonify({
                'correct': True,
                'question': next_question['text'],
                'answers': next_question['answers'],
                'score': quiz_state['score']
            })
        else:
            return jsonify({
                'correct': True,
                'finished': True,
                'score': quiz_state['score']
            })
    else:
        return jsonify({
            'correct': False,
            'score': quiz_state['score'],
            'correct_answer': current_question['correct']
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Support Railway's dynamic port
    app.run(host='0.0.0.0', port=port)