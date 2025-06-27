from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import json
import random
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Секретный ключ для подписи сессии

# Конфигурация для серверной сессии
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 час

Session(app)

# Загрузка вопросов из JSON файла
with open('questions_and_answers_cleaned.json', 'r', encoding='utf-8') as f:
    questions_data = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_test', methods=['POST'])
def start_test():
    session.clear()
    num_questions = int(request.form.get('num_questions', 20))
    
    if not questions_data or len(questions_data) == 0:
        return redirect(url_for('index'))
    
    # Храним только индексы вопросов
    question_indices = random.sample(range(len(questions_data)), min(num_questions, len(questions_data)))
    session['question_indices'] = question_indices
    session['current_question'] = 0
    session['score'] = 0
    session['user_answers'] = []
    
    return redirect(url_for('show_question'))

@app.route('/question')
def show_question():
    if 'question_indices' not in session:
        return redirect(url_for('index'))
    
    current_idx = session['current_question']
    question_indices = session['question_indices']
    
    if current_idx >= len(question_indices):
        return redirect(url_for('show_results'))
    
    question = questions_data[question_indices[current_idx]]
    return render_template('test.html', 
                         question=question, 
                         question_num=current_idx+1, 
                         total_questions=len(question_indices))

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'question_indices' not in session:
        return redirect(url_for('index'))
    
    current_idx = session['current_question']
    question_indices = session['question_indices']
    question = questions_data[question_indices[current_idx]]
    
    selected_answer = int(request.form.get('answer', -1))
    is_correct = False
    
    if 0 <= selected_answer < len(question['answers']):
        is_correct = question['answers'][selected_answer]['is_correct']
        if is_correct:
            session['score'] += 1
    
    user_answers = session['user_answers']
    user_answers.append({
        'question_idx': question_indices[current_idx],
        'selected_answer': selected_answer,
        'is_correct': is_correct
    })
    session['user_answers'] = user_answers
    session['current_question'] = current_idx + 1
    
    return redirect(url_for('show_question'))

@app.route('/results')
def show_results():
    if 'question_indices' not in session or 'score' not in session:
        return redirect(url_for('index'))
    
    score = session['score']
    question_indices = session['question_indices']
    total_questions = len(question_indices)
    
    if total_questions == 0:
        return redirect(url_for('index'))
    
    # Восстанавливаем полные данные вопросов и ответов для отображения
    detailed_answers = []
    for answer in session['user_answers']:
        question_data = questions_data[answer['question_idx']]
        selected_answer_text = ""
        if 0 <= answer['selected_answer'] < len(question_data['answers']):
            selected_answer_text = question_data['answers'][answer['selected_answer']]['text']
        
        correct_answers = [i for i, ans in enumerate(question_data['answers']) if ans['is_correct']]
        correct_answers_texts = [question_data['answers'][i]['text'] for i in correct_answers]
        
        detailed_answers.append({
            'question_text': question_data['question'],
            'selected_answer': answer['selected_answer'],
            'selected_answer_text': selected_answer_text,
            'is_correct': answer['is_correct'],
            'correct_answers': correct_answers,
            'correct_answers_texts': correct_answers_texts,
            'all_answers': question_data['answers']
        })
    
    session.clear()
    
    return render_template('results.html', 
                         score=score, 
                         total_questions=total_questions,
                         user_answers=detailed_answers)

if __name__ == '__main__':
    # Создаем папку для сессий, если ее нет
    if not os.path.exists(app.config['SESSION_FILE_DIR']):
        os.makedirs(app.config['SESSION_FILE_DIR'])
    app.run(debug=True)