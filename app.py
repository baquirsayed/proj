import speech_recognition as sr
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
from flask_mail import Mail, Message
import pyttsx3
from word2number import w2n
from pydub import AudioSegment
import os
#import soundfile as sf
##from scipy.io import wavfile

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)


db = SQLAlchemy()
app = Flask(__name__)
app2 = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Payment.db"
app.config["SQLALCHEMY_BINDS"] = {
    'Payments' : 'sqlite:///Payments.db',
    'Archives' : 'sqlite:///Archives.db'
} 

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'rizviproject2022@gmail.com'
app.config['MAIL_PASSWORD'] = 'dsplvghnthzxybio'
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
        return redirect("/")
    query = query.lower()
    try:
        if 'delete entry' in query:
            query = query.replace("delete entry ", "")
            paymentNumber = w2n.word_to_num(query)
            print("hi")
            paymentquery = Payments.query.filter_by(paymentNumber=paymentNumber).first()
            print("hi")
            db.session.delete(paymentquery)
            print("hi")
            db.session.commit()
            os.remove('recording.wav')
            return redirect('/')
    except Exception as a:
        print(a)
        print("no")
        os.remove('recording.wav')
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
    scheduleTime = request.form.get('scheduleTime')
    print(scheduleTime)
    if request.method =='POST':
        paymentEmail = request.form['paymentEmail']
        msg = Message('Reminder', sender = 'rizviproject2022@gmail.com',recipients=[paymentEmail])
        msg.body = 'This is a reminder for your Payment'
        mail.send(msg)
        return redirect("/")
    paymentquery =  Payments.query.filter_by(paymentNumber=paymentNumber).first()
    return render_template('requests.html', paymentquery = paymentquery)




with app.app_context():
    db.create_all()
    
if __name__ == "__main__":
    app.run(debug=True, port = 10000)