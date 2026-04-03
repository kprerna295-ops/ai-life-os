from flask import Flask, render_template, request, jsonify, redirect, session
import os
from dotenv import load_dotenv
from openai import OpenAI
import splite3

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------- DB INIT --------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, task TEXT)')

    conn.commit()
    conn.close()

init_db()

# -------- AUTH --------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        conn = sqlite3.connect('database.db')
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)).fetchone()
        conn.close()

        if user:
            session['user'] = u
            return redirect('/dashboard')

    return render_template('login.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        conn = sqlite3.connect('database.db')
        conn.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# -------- ROUTES --------
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('database.db')
    count = len(conn.execute("SELECT * FROM tasks").fetchall())
    conn.close()
    return render_template('dashboard.html', count=count)

@app.route('/assistant')
def assistant():
    return render_template('assistant.html')

@app.route('/resume')
def resume():
    return render_template('resume.html')

@app.route('/files')
def files():
    return render_template('files.html', files=os.listdir(UPLOAD_FOLDER))

@app.route('/planner')
def planner():
    conn = sqlite3.connect('database.db')
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return render_template('planner.html', tasks=tasks)

# -------- TASK --------
@app.route('/add_task', methods=['POST'])
def add_task():
    task = request.form['task']
    conn = sqlite3.connect('database.db')
    conn.execute("INSERT INTO tasks (task) VALUES (?)",(task,))
    conn.commit()
    conn.close()
    return redirect('/planner')

@app.route('/delete_task/<int:id>')
def delete_task(id):
    conn = sqlite3.connect('database.db')
    conn.execute("DELETE FROM tasks WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect('/planner')

# -------- RESUME --------
@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    file = request.files['file']
    path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(path)

    # Read resume text (basic)
    text = ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except:
        text = "Resume uploaded"

    try:
        # AI analysis
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a resume analyzer."},
                {"role": "user", "content": f"Analyze this resume:\n{text}"}
            ]
        )

        analysis = res.choices[0].message.content

    except:
        # fallback
        analysis = "Resume uploaded successfully. Improve by adding projects, skills, and achievements."

    return render_template('resume.html', file=file.filename, analysis=analysis)

# -------- AI --------
@app.route('/chat', methods=['POST'])
def chat():
    msg = request.json['message']

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"Career mentor"},
                {"role":"user","content":msg}
            ]
        )
        reply = res.choices[0].message.content

    except:
        # fallback if API fails
        if "job" in msg.lower():
            reply = "Focus on DSA + projects."
        else:
            reply = "AI currently unavailable."

    return jsonify({"reply": reply})
if __name__ == '__main__':
    app.run(debug=True)