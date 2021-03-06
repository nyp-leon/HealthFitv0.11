from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, RadioField, IntegerField, FloatField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from random import randint
from Exercises import Exercises
from Fitness import Record, YourPlan

app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Blzh1206'
app.config['MYSQL_DB'] = 'HealthFit'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#initialize MYSQL
mysql = MySQL(app)

#Check if logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please log in','danger')
            return redirect(url_for('login'))
    return wrap

@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/profile")
@is_logged_in
def profile():
    #Create cursor
    cur = mysql.connection.cursor()

    #Get profile data
    cur.execute("SELECT * FROM users")

    data = cur.fetchall()

    return render_template('profile.html', datas = data)

    cur.close()


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password')
    weight = IntegerField('Weight (KG)')
    height = FloatField('Height (M)')
    gender = RadioField('Gender',choices = [('M','Male'),('F','Female')])
    age = IntegerField('Age')

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(form.password.data) #sha256 is to encrypt pw
        weight = form.weight.data
        height = form.height.data
        gender = form.gender.data
        age = form.age.data


        #Create cursor
        cur = mysql.connection.cursor()

        #Execute query
        cur.execute("INSERT INTO users(name, email, username, password, weight, height, gender, age) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (name, email, username, password, weight, height, gender, age))

        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('You are now registered and can log in.','success')

        redirect(url_for('home'))
    return render_template('register.html', form=form)


#User login

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user_password = request.form['password']

        #Create cursor
        cur = mysql.connection.cursor()

        #Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        #cur.execute("SELECT name FROM users")
        if result > 0: #find if there is any result from db
            # get stored hash
            data = cur.fetchone()
            password = data['password']

            #Compare passwords
            if sha256_crypt.verify(user_password, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in','success')
                return redirect(url_for('home'))
            else:
                error = 'Invalid login'
                return render_template('login.html',error=error)
            #close connection here
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)


    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))

@app.route('/ExGuide')
def guide():
    exercises_list = []
    int_list = []
    e1 = Exercises(
        "A push-up is a common exercise that involves beginning from the prone position,then raising and lowering the body using the arms.",
        "Pectoral muscles, Abdominal muscles, Triceps",
        ["Extend your legs backwards and place hands on the ground, slightly more than shoulder-width apart.",
        "Start by bending your elbows to lower your chest until it is just above the floor.",
        "Push yourself back to the starting position. An ideal push-up would be a 1-second push, pause and a 2 second down count.",
        "Repeat steps 1 to 3 for preferably 10 to 15 times."],
        "https://cdn-ami-drupal.heartyhosting.com/sites/muscleandfitness.com/files/styles/full_node_image_1090x614/public/media/1109-pushups_0.jpg?itok=QyFVWqN6")
    e2 = Exercises(
        'Crunching is an exercise that involves lying face-up on the floor,bending the knees then curling the shoulders towards the waist.',
        'Abdominal muscles',
        ['Lie on your back with your knees bent and feet flat on the floor hip-width apart.',
         'Place your hands behind your head such that your thumbs are behind your ears',
         'Hold your elbows to the sides, slightly facing in.',
         'Slightly tilt your chin, leaving some space between your chin and chest.',
         'Gently pull your abdominals inward.',
         'Curl up and forward so that your head, neck and shoulders lift off the floor',
         'Hold for a moment at the top of the movement in Step 6 and slowly lower yourself back down',
         'Repeat Steps 1 to 7 for preferably 10 to 15 times.'],
        "https://cdn2.coachmag.co.uk/sites/coachmag/files/styles/16x9_480/public/images/dir_30/mens_fitness_15427.jpg?itok=T3OF7wPv&timestamp=1369282187")
    e3 = Exercises(
        'Jumping Jacks is an exercise that involves jumping with the legs spread wide and hands touching overhead then returning to a position with the feet together and arms at the sides.',
        'Calve muscles, Shoulder muscles, Hip muscles',
        ['Stand with your feet together and pointing forward, arms hanging straight at the sides.',
         'In one jump, bend your knees and extend both legs out to the sides while simultaneously extending your arms out to the sides and then up and over the head.',
         'Immediately reverse this motion, jumping back to the starting or neutral standing position.',
         'Repeat Steps 1 to 3 for preferably 10 to 15 times.'],
        "https://hips.hearstapps.com/hmg-prod.s3.amazonaws.com/images/1104-jumping-jacks-1441032989.jpg")
    e4 = Exercises(
        'Tuck jumping is an exercise that involves standing in a shoulder width position, slowly descending into a squat and use your feet to explode off the floor while driving your knees towards your chest.',
        'Abdominal muscles, Hamstrings, Calve muscles',
        ['Start in a standing position, slightly bending your knees',
         'Hold your hands out at chest level.',
         'Lower your body quickly into a squatting position, then explode upwards bringing your knees up towards your chest.',
         'Repeat Steps 1 to 3 for preferably 10 to 15 times.'],
        "http://fitmw.com/wp-content/uploads/2015/07/Exercises-Tuck-Jump.jpg")
    e5 = Exercises(
        'Squatting is an exercise that involves standing in a shoulder width position, bending your knees all the way down and then explode back up to standing.',
        'Hip muscles, Hamstrings, Quads',
        ['Stand with your feet apart, directly under your hips, and place your hands on your hips.',
         'Standing up tall, put your shoulders back, lift your chest, and pull in your abdominal muscles.',
         'Bend your knees while keeping your upper body as straight as possible, like a sitting position. Lower yourself down as far as you can without leaning your upper body more than a few inches forward.',
         'Straighten your legs so you do not lock your knees when you reach a standing position.',
         'Repeat Steps 1 to 4 for preferably 10 to 15 times.'],
        "https://19jkon2dxx3g14btyo2ec2u9-wpengine.netdna-ssl.com/wp-content/uploads/2013/11/squats.jpg")
    e6 = Exercises(
        'Flutter kicks is an exercise that involves lying down face-up, straightening your legs until they are level with your hips and alternating between lifting each leg.',
        'Abdominal muscles, Hip muscles, Quads',
        ['Lie on your back with your legs extended and your arms alongside your hips, palms down.',
         'Lift your legs about 4 to 6 inches off the floor. Press your lower back into the floor or gym mat.',
         'Keep your legs straight as you rhythmically raise one leg higher, then switch. Move in a fluttering, up and down motion.',
         'Repeat Steps 1 to 3 for preferably 15 to 20 times.'],
        "https://i.pinimg.com/originals/74/d8/55/74d855acc30ffdfe3c7410f3c278918b.jpg")
    exercises_list.extend([e1, e2, e3, e4, e5, e6])

    exercise = ""
    exercise1 = ""
    exercise2 = ""

    while exercise == "":
        cycle = randint(0, 5)
        if cycle not in int_list:
            exercise = exercises_list[cycle]
            int_list.append(cycle)

    while exercise1 == "":
        cycle = randint(0, 5)
        if cycle not in int_list:
            exercise1 = exercises_list[cycle]
            int_list.append(cycle)

    while exercise2 == "":
        cycle = randint(0, 5)
        if cycle not in int_list:
            exercise2 = exercises_list[cycle]
            int_list.append(cycle)

    return render_template('ExGuide.html', exercise=exercise, exercise1=exercise1, exercise2=exercise2)

@app.route('/schedule')
def schedule():
    return render_template('schedule.html')

@app.route('/schedule/ToDoList')
def todolist():
    return render_template('todolist.html')

@app.route('/HealthTracker')
def HealthTracker():
    return render_template('HealthTracker.html')

@app.route('/fitness')
def fitness():
    r1 = Record('food1')
    p1 = YourPlan('2500', 'bulk')
    return render_template('fitness.html', items=r1, kcal=p1)

if __name__ == "__main__":
    app.secret_key='secret123'
    app.debug = True
    app.run()

