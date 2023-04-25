import atexit
import sched
import time
import speech_recognition as sr
from threading import Thread
from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
from flask_mail import Mail, Message
from pydub import AudioSegment
import os





db = SQLAlchemy()
app = Flask(__name__)
app2 = Flask(__name__)

scheduler = sched.scheduler(time.time, time.sleep)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Payment.db"
app.config["SQLALCHEMY_BINDS"] = {
    'Payments' : 'sqlite:///Payments.db',
    'Archives' : 'sqlite:///Archives.db'
} 

app.config['MAIL_SERVER']='smtp.gmail.com'  
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'rizviproject2022@gmail.com'
app.config['MAIL_PASSWORD'] = 'chjaynvccukcoqut'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)
db.init_app(app)

    

class Payments(db.Model):
    __bind_key__ = 'Payments'
    paymentNumber = db.Column(db.Integer, primary_key=True)
    paymentTitle = db.Column(db.String(80), nullable=False)
    paymentAmount = db.Column(db.Integer, nullable=False)
    paymentEmail = db.Column(db.String(80))
    dateCreated = db.Column(db.DateTime, default=datetime.now)
    # t = datetime.utcnow
    # delta = timedelta(days=1)
    # temp = datetime.combine(datetime.date(1,1,1),t) + delta
    # remind = db.Column(db.Date, default = temp)
    paymentMethod = db.Column(db.String(20), nullable  = False)
    paymentDescription = db.Column(db.String(100), nullable = True)

with app.app_context():
    db.create_all

class Archives(db.Model):
    __bind_key__ = 'Archives'
    paymentNumber = db.Column(db.Integer, primary_key=True)
    paymentTitle = db.Column(db.String(80), nullable=False)
    paymentAmount = db.Column(db.Integer, nullable=False)
    paymentEmail = db.Column(db.String(80))
    dateCreated = db.Column(db.DateTime, default=datetime.now)
    paymentMethod = db.Column(db.String(20), nullable  = False)
    paymentDescription = db.Column(db.String(100), nullable = False)
    paymentStatus = db.Column(db.String(100), nullable = False)

with app.app_context():
    db.create_all

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    # Retrieve the audio file from the HTTP request
    audio_file = request.files['audio']

    # Save the audio file to disk
    audio_file.save('recording.wav')

    # Return a JSON response to the client
    response = {'message': 'Audio file saved successfully'}

    process_audio()
    return jsonify(response)

def process_audio():
    r = sr.Recognizer()

    

    try:
        audio_file = AudioSegment.from_file('recording.wav')
        audio_file.export('recording.wav', format='wav')
        with sr.AudioFile('recording.wav') as source:   
            audio = r.record(source)
            query = r.recognize_google(audio,language = 'en-in')
    except Exception as e:
        print(e)
        query = ''
        return redirect("/")
    query = query.lower()
    try:
        if 'delete entry' in query:
            print(query)
            query = query.replace("delete entry ", "")
            paymentNumber = query
            print("assigned")
            paymentquery = Payments.query.filter_by(paymentNumber=paymentNumber).first()
            print("filtered")
            db.session.delete(paymentquery)
            print("deleted")
            db.session.commit()
            os.remove('recording.wav')
            query = ''
            return redirect('/')
    except Exception as a:
        print(a)
        print("failed")
        os.remove('recording.wav')
        query = ''
        return redirect('/')
            
            






@app.route("/", methods=['GET', 'POST'])
def home_page():
    if request.method == 'POST':
        paymentTitle = request.form['paymentTitle']
        paymentAmount = request.form['paymentAmount']
        paymentMethod = request.form['paymentMethod']
        paymentDescription = request.form['paymentDescription']
        paymentEmail = request.form['paymentEmail']
        payment = Payments(paymentTitle = paymentTitle, paymentAmount = paymentAmount, paymentMethod = paymentMethod, paymentDescription = paymentDescription, paymentEmail = paymentEmail)
        archive = Archives(paymentTitle = paymentTitle, paymentAmount = paymentAmount, paymentMethod = paymentMethod, paymentDescription = paymentDescription, paymentEmail = paymentEmail, paymentStatus = 'Added')
        db.session.add(payment)
        db.session.add(archive)
        db.session.commit()
    paymentquery = Payments.query.order_by(Payments.dateCreated).all()
    archive = Archives.query.order_by(Archives.dateCreated).all()
    return render_template('index.html', paymentquery = paymentquery, archive = archive)

with app.app_context():
    db.create_all


@app.route('/update/<int:paymentNumber>', methods=['GET', 'POST'])
def update(paymentNumber):
    if request.method =='POST':
        payment =  Payments.query.filter_by(paymentNumber=paymentNumber).first()
        archive = Archives.query.filter_by(paymentNumber=paymentNumber).first()
        payment.paymentTitle = request.form['paymentTitle']
        payment.paymentAmount = request.form['paymentAmount']
        payment.paymentMethod = request.form['paymentMethod']
        payment.paymentEmail = request.form['paymentEmail']
        payment.paymentDescription = request.form['paymentDescription']
        db.session.add(payment)
        db.session.commit()
        paymentTitle = archive.paymentTitle
        paymentAmount = payment.paymentAmount
        paymentMethod = payment.paymentMethod
        paymentDescription = payment.paymentDescription
        paymentEmail = payment.paymentEmail
        paymentStatus = 'Updated'
        archive = Archives(paymentTitle = paymentTitle, paymentAmount = paymentAmount, paymentMethod = paymentMethod, paymentDescription = paymentDescription, paymentEmail = paymentEmail, paymentStatus = paymentStatus)
        db.session.add(archive)
        db.session.commit() 
        return redirect("/")
    paymentquery =  Payments.query.filter_by(paymentNumber=paymentNumber).first()
    return render_template('update.html', paymentquery = paymentquery)

@app.route('/delete/<int:paymentNumber>', methods=['GET', 'POST'])
def delete(paymentNumber):
    paymentquery =  Payments.query.filter_by(paymentNumber=paymentNumber).first()
    db.session.delete(paymentquery)
    db.session.commit()
    return redirect("/")

@app.route('/requests/<int:paymentNumber>', methods=['GET', 'POST'])
def requests(paymentNumber):
    if request.method =='POST':
        
        paymentEmail = request.form['paymentEmail']
        paymentTime = request.form['paymentTime']
        emailBody = request.form['emailBody']
        print(emailBody)
        print(paymentTime)

        if paymentTime == "1 minute":
            paymentSeconds = 60
        elif paymentTime == "15 minutes":
            paymentSeconds = 900
        elif paymentTime == "30 minutes":
            paymentSeconds = 1800
        elif paymentTime == "1 hour":
            paymentSeconds = 3600
        elif paymentTime == "8 hours":
            paymentSeconds = 28800
        elif paymentTime == "1 day":
            paymentSeconds = 86400
        elif paymentTime == "1 week":
            paymentSeconds = 604800
        else:
            paymentSeconds = 0
        print(paymentSeconds)

        if(paymentSeconds == 0):
            msg = Message('Reminder', sender = 'rizviproject2022@gmail.com', recipients=[paymentEmail])
            msg.body = 'This is a reminder for your Payment'
            if emailBody != "":
                msg.body = emailBody 
            mail.send(msg)
            return redirect("/")
        else:
            scheduler.enter(paymentSeconds, 1, Thread(target=send_email, args=(paymentEmail, emailBody)).start, ())
            scheduler.run()
            return redirect("/")
        
    paymentquery =  Payments.query.filter_by(paymentNumber=paymentNumber).first()
    return render_template('requests.html', paymentquery = paymentquery)

def send_email(email, body):
    with app.app_context():
        msg = Message('Reminder', sender = 'rizviproject2022@gmail.com', recipients=[email])
        msg.body = 'This is a reminder for your Payment'
        if body != "":
            msg.body = body
        mail.send(msg)
        return True
    




with app.app_context():
    db.create_all()

def start_scheduler():
    scheduler.run()
    
if __name__ == "__main__":
    atexit.register(lambda: scheduler.shutdown(wait=False))
    app.run(debug=True, port = 10000)