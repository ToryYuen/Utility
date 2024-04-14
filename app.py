from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import time
import json
import redis

# Redis Connection
r = redis.Redis(host='127.0.0.1', port=6379)

# Flask app and Flask_Sqlite
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
db = SQLAlchemy(app)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(200), nullable=False)
    content = db.Column(db.String(850), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        return '<Task %r>' % self.id


# Create DB
with app.app_context():
    db.create_all()


@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        url = request.form['content']
        message = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "url": url,
        }
        r.lpush("download", json.dumps(message))
        return redirect('/')

    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template("index.html", tasks=tasks)


@app.route("/delete/<int:id>")
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was an issue deleting that result'


@app.route('/view/<int:id>', methods=['GET', 'POST'])
def view(id):
    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue updating your task'

    else:
        return render_template('view.html', task=task)


if __name__ == '__main__':
    app.run(debug=True)
