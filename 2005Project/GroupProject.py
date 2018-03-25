from flask import Flask, request, flash, url_for, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test008.sqlite3'
app.config['SECRET_KEY'] = "random string"
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(15))
    password = db.Column('password', db.String(10))

    def __init__(self, username, password):
        self.username = username
        self.password = password


class Post(db.Model):
    __tablename__ = 'post'
    postID = db.Column('post_id', db.Integer, primary_key=True,)
    replyID = db.Column('reply_id', db.Integer)
    title = db.Column(db.String(100))
    content = db.Column(db.String(250))
    topic = db.Column(db.String(20))
    author = db.Column(db.String(15))
    replies = db.Column('replies', db.Integer)

    def __init__(self, title, content, topic, replyID = 0):
        self.replyID = replyID
        self.title = title
        self.content = content
        self.topic = topic
        self.replies = 0
        if session.get('username'):
            self.author = session['username']
        else:
            self.author = "Anonymous"


@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        if not request.form['title' ] or not request.form['content']:
            flash('Please enter all the fields', 'error')
        else:
            post = Post(request.form['title'], request.form['content'], request.form['topic'])
            db.session.add(post)
            db.session.commit()
            flash('Record was successfully added')
            return redirect(url_for('show_all'))
    return render_template('new.html')


@app.route('/replyto/<int:post_id>', methods=['GET', 'POST'])
def replyto(post_id):

    if request.method == 'POST':
        if not request.form['content']:
            flash('Please enter a reply between 1 and 250 characters', 'error')
        else:
            replyto = Post.query.filter_by(postID = post_id).first()
            replyto.replies = replyto.replies + 1
            post = Post("Reply", request.form['content'], replyto.topic, post_id)
            db.session.add(post)
            db.session.commit()
            flash('Record was successfully added')
            return redirect(url_for('show_all'))
    return render_template('reply.html')


@app.route('/')
def show_all():
    return render_template('show_all.html', users=User.query.all(), posts=Post.query.filter(Post.replyID == 0))


@app.route('/replies/<int:post_id>')
def show_replies(post_id):
    return render_template('show_all.html', users=User.query.all(), posts=Post.query.filter(or_(Post.replyID == post_id, Post.postID == post_id)))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        loginuser = User.query.filter_by(username = request.form['username']).first()
        if loginuser:
            if loginuser.password == request.form['password']:
                    session['username'] = request.form['username']
                    session['logged_in'] = True
                    flash('You were logged in as ' + session['username'])
                    return redirect(url_for('show_all'))
            
            else:
                flash('Incorrect Username and/or Password')
                return redirect(url_for('login'))
       
        else:
            flash('Incorrect Username and/or Password')
            return render_template('login.html')
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        if not request.form['username'] or not request.form['password']:
            flash('Please enter all the fields')
            render_template('register.html')
        else:
            loginuser = User.query.filter_by(username=request.form['username']).first()
            if not loginuser:
                user = User(request.form['username'], request.form['password'])
                db.session.add(user)
                db.session.commit()
                flash('User Successfully Registered')
                return redirect(url_for('show_all'))
            else:
                flash('Error: User already exists')
                return redirect(url_for('register'))
    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You were logged out')
    return redirect(url_for('show_all'))

@app.route('/group')
def group():
    return render_template('group.html')


db.create_all()
if __name__ == '__main__':

    app.run()
