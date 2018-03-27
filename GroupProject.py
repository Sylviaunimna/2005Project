"""This module is used to create and host a forum for users to login and make topic posts."""

from flask import Flask, request, flash, url_for, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy import and_


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test018.sqlite3'
app.config['SECRET_KEY'] = "random string"
db = SQLAlchemy(app)


class User(db.Model):
    """This User class retrieves the 'Username' and 'Password' of a created account from the database.

        :param id: Identification number assigned to the specific user login credentials determined by linear increment.
        :param username: A name containing up to 15 characters created by the user to be referenced for login and post author identification.
        :param password: A password containing up to 10 characters created by the user to be referenced for login authentication.
        :type id: Integer
        :type username: String
        :type password: String
        :return: Returns null by default upon function success.
    """

    __tablename__ = 'user'
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(15))
    password = db.Column('password', db.String(10))
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Post(db.Model):
    """This Post class handles the creation and viewing of new posts, as well as replies to posts.

        :param postID: The identification number to reference an original post, linearly determined.
        :param replyID: The identification number to reference a reply, linearly determined.
        :param title: The user-created name of the post.
        :param content: The user-created body text of the post.
        :param topic: The user created group/topic used to generally identify the post for quick searching.
        :param author: The username of the user who created the post/reply.
        :param replies: The number of replies to an original post.
        :type postID: Integer
        :type replyID: Integer
        :type title: String
        :type content: String
        :type topic: String
        :type author: String
        :type replies: Integer
        :return: Returns null by default upon success.
    """

    __tablename__ = 'post'
    postID = db.Column('post_id', db.Integer, primary_key=True,)
    replyID = db.Column('reply_id', db.Integer)
    title = db.Column(db.String(100))
    content = db.Column(db.String(250))
    topic = db.Column(db.String(20))
    author = db.Column(db.String(15))
    replies = db.Column('replies', db.Integer)
    subscriptions = db.relationship('Subscription', backref='post', lazy=True)

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

class Subscription(db.Model):
    """This is a placeholder doc string

    """

    __tablename__ = 'subscription'
    subID = db.Column('sub_id', db.Integer, primary_key=True)
    userID = db.Column(db.String(15), db.ForeignKey('user.id'), nullable=False)
    topic = db.Column('topic', db.String(20))
    postID = db.Column(db.Integer, db.ForeignKey('post.post_id'), nullable=False)
    postTitle = db.Column('postTitle', db.String(100))
    notification = db.Column('notification', db.Boolean)

    def __init__(self, user, topic, postID = 0):
        self.userID = user
        self.topic = topic
        self.postID = postID
        if postID is not 0:
            self.postTitle = Post.query.filter_by(postID=postID).first().title
        self.notification = False

# class Groups(db.Model):
#    """This is a placeholder doc string
#
#    """
#
#    __tablename__ = 'groups'
#    groupID = db.Column('group_id', db.Integer, primary_key=True)
#    userID = db.Column(db.String(15), db.ForeignKey('user.id'), nullable=False)
#    group_name = db.Column('group_name', db.String(20))
#
#    def __init__(self, group_name, userID, groupID = 0):
#        self.group_name = group_name
#        self.userID = userID
#        self.groupID = groupID
#        if session.get('username'):
#            self.author = session['username']
#        else:
#            self.author = "Anonymous"


@app.route('/new', methods=['GET', 'POST'])
def new():
    """Creates a new post with a title, content and topic

    :return: Returns the HTML template 'new.html'.
    """
    if request.method == 'POST':
        if session.get('username') is None:
            flash('Error: Must be logged in to post')
        elif not request.form['title' ] or not request.form['content']:
            flash('Please enter all the fields', 'error')
        else:
            post = Post(request.form['title'], request.form['content'], request.form['topic'])
            subs = Subscription.query.filter(Subscription.topic == request.form['topic'])
            for sub in subs:
                sub.notification = True
            db.session.add(post)
            db.session.commit()
            flash('Record was successfully added')
            return redirect(url_for('show_all'))
    return render_template('new.html')


@app.route('/replyto/<int:post_id>', methods=['GET', 'POST'])
def replyto(post_id):
    """Creates a reply to the post referenced by the original post ID.

    :param post_id: The ID number of the original post to be replied to.
    :type post_id: Integer
    :return: Returns the HTML template 'reply.html'.
    """

    if request.method == 'POST':
        if session.get('username') is None:
            flash('Error: Must be logged in to post')
        elif not request.form['content']:
            flash('Please enter a reply between 1 and 250 characters', 'error')
        else:
            replyto = Post.query.filter_by(postID = post_id).first()
            replyto.replies = replyto.replies + 1
            subs = Subscription.query.filter(or_(Subscription.postID == post_id,Subscription.topic == replyto.topic))
            for sub in subs:
                sub.notification = True
            post = Post("Reply", request.form['content'], replyto.topic, post_id)
            db.session.add(post)
            db.session.commit()
            flash('Record was successfully added')
            return redirect(url_for('show_all'))
    return render_template('reply.html', posts=Post.query.filter(or_(Post.replyID == post_id, Post.postID == post_id)))

@app.route('/subscribetotopic/<topic>')
def subscribetotopic(topic):
    """Subscribes the user to their selected topic keyword.

    :param topic: The topic name to be referenced when checking for notifications.
    :type topic: String
    :return: Returns the HTML template 'show_all.html'.
    """
    if session.get('username') is None:
        flash('Error: Must be logged in to subscribe')
    elif Subscription.query.filter(and_(Subscription.topic == topic, Subscription.userID == session['username'])).first() is None:
        sub = Subscription(session['username'], topic)
        db.session.add(sub)
        db.session.commit()
        flash(str(session['username']) + " subscribed to topic " + topic)
    else:
        flash("You're already subscribed to topic " + topic)
    return redirect(url_for('show_all'))

@app.route('/subscribetopost/<int:post_id>')
def subscribetopost(post_id):
    """Subscribes the user to their selected post keyword.

    :param post_id: The post id to be referenced when checking for notifications.
    :type post_id: Integer
    :return: Returns the HTML template 'show_all.html'.
    """

    if session.get('username') is None:
        flash('Error: Must be logged in to subscribe')
    elif Subscription.query.filter(and_(Subscription.postID == post_id, Subscription.userID == session['username'])).first() is None:
        sub = Subscription(session['username'], None, post_id)
        db.session.add(sub)
        db.session.commit()
        flash(str(session['username']) + " subscribed to post " + str(post_id))
    else:
        flash("You're already subscribed to post " + str(post_id))
    return redirect(url_for('show_all'))

@app.route('/mysubs')
def showSubs():
    """Generates a list of all subscriptions that a user has made.

    :return: Returns the HTML template 'mysubs.html'.
    """
    if session.get('username') is None:
        flash('Error: Must be logged in to view subscriptions')
    else:
        subs = Subscription.query.filter(Subscription.userID == session['username'])
        x = render_template('mysubs.html', subTopics=Subscription.query.filter(and_(Subscription.userID == session['username'], Subscription.postID == 0)), subPosts=db.session.query(Subscription).filter(and_(Subscription.userID == session['username'], (Subscription.topic == None))))
        for sub in subs:
            sub.notification = False
        db.session.commit()
        return x

@app.route('/topic/<topic>')
def showTopic(topic):
    return render_template('show_all.html', posts=Post.query.filter(and_(Post.replyID == 0, Post.topic == topic)))

@app.route('/')
def show_all():
    """Creates a compilation of all templates to view the overall project.

    :return: Returns the HTML template 'show_all.html'.
    """
    return render_template('show_all.html', posts=Post.query.filter(Post.replyID == 0))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Checks the user login credentials to authenticate the login attempt.

    :return: Returns the redirect url for 'show_all.html' if successfully logged in;
             Returns the redirect url for 'login.html' if unsuccessful login attempt;
             Returns the HTML template 'login.html' if an error occurred.
    """
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
    """Creates a new user object with a unique username and password.

    :return: Returns the redirect url for 'show_all.html' if successfully registered;
             Returns the redirect url for 'register.html' if unsuccessful register attempt;
             Returns the HTML template 'register.html' if an error occurred.
    """
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
    """Logs out the current user from the session.

    :return: Returns the redirect url for 'show_all.html'.
    """
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You were logged out')
    return redirect(url_for('show_all'))

@app.route('/group')
def create_group():
    """This is the stub for the create a group function.

    :return:
    """
    return render_template('group.html')

db.create_all()
if __name__ == '__main__':

    app.run()
