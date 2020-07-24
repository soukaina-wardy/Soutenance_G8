from flask import Flask, request, render_template, jsonify, session, redirect, make_response
import requests
import socket
import time
from datetime import datetime
from feature_format import feature_engineering
import json
import pickle
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

client = MongoClient()
db = client['fraud_case_study']
coll = db['new']

app = Flask(__name__)
DATA = []
TIMESTAMP = []
CLF_FILE_NAME = "C:/Users/ASUS ROG STRIX G/Desktop/pro3-dani/pro3-dani/app/classifier.pkl"
LINK = 'http://galvanize-case-study-on-fraud.herokuapp.com/data_point'

with open(CLF_FILE_NAME, "rb") as clf_infile:
    MODEL = pickle.load(clf_infile)


def scrape():
    response = requests.get(LINK)
    return response.json()


@app.route('/')
@app.route('/main.html')
def main():
    return render_template('main.html')

@app.route('/login.html')
def login():
    passwordhash = generate_password_hash('test2')
    print(passwordhash)
    return render_template('login.html')


@app.route('/submit', methods=['POST'])
def login_submit():
     return render_template('index.html')


# My word counter app
@app.route('/index.html')
@app.route('/index')
def make_prediction():
    new_data = scrape()
    DATA.append(new_data)
    X, feature_names = feature_engineering(DATA, [])
    proba = MODEL.predict_proba(X[-1].reshape(1,X.shape[1]))[:,1][0]
    probability = "{:.2%}".format(proba)
    if proba < 0.2:
        fraud_text = "Pas de Fraude!"
    else:
        fraud_text = "Fraude!"
    return render_template('index.html', prediction=fraud_text,
                            proba=probability, event_data=new_data)


@app.route('/logout')
def logout():
    if 'email' in session:
        session.pop('email', None)
    return redirect('/')


# ======================================================================== Part of Yassine Boukhla : Loan for professionals ( companies )
@app.route('/loan_comp.html')
def loan_comp():
    return render_template('loan_comp.html')


model_loan_comp = pickle.load(open('C:/Users/ASUS ROG STRIX G/Desktop/pro3-dani/pro3-dani/app/dt_model.pkl', 'rb'))


@app.route('/predict', methods=['POST'])
def predict():
    current_loan_amount = request.form['current_loan_amount']
    loan_term = request.form['loan_term']
    credit_score = request.form['credit_score']
    annual_income = request.form['annual_income']
    years_in_industry = request.form['years_in_industry']
    past_credit_problems = request.form['past_credit_problems']
    had_bankruptcy = request.form['had_bankruptcy']
    new_record = [[current_loan_amount, loan_term, credit_score,
                   annual_income, years_in_industry,
                   past_credit_problems, had_bankruptcy]]
    prediction = model_loan_comp.predict(new_record)
    if prediction == 1:
        result = 'Accepted'
    else:
        result = 'Declined'
    return render_template('loan_comp.html',
                           prediction_text='Your loan is going to be: {}'.format(result))

# ======================================================================================================= End of Loan For Professionals


# ======================================================================== Part of Anouar El Marnissy : Loan for Individuals ( individuals ): zid lcode dialk hna
@app.route('/loanindiv.html')
def loan_indiv():
    return render_template('loanindiv.html')


model_loan_indiv = pickle.load(open('C:/Users/ASUS ROG STRIX G/Desktop/pro3-dani/pro3-dani/app/knn.pkl', 'rb'))


@app.route('/predictindiv', methods=['POST'])
def predictindiv():
    dependents = request.form['dependents']
    applicantincome = request.form['applicantincome']
    loanamount = request.form['loanamount']
    loanamountterm = request.form['loanamountterm']
    credithistory = request.form['credithistory']
    gender = request.form['Gender']
    if gender == "male":
        gender_male = 1
        gender_female = 0
    else:
        gender_male = 0
        gender_female = 1

    education = request.form['graduation']
    if education == "Graduated":
        education_graduate = 1
        education_not_graduate = 0
    else:
        education_graduate = 0
        education_not_graduate = 1

    employment = request.form['employment']
    if employment == "SelfEmployed":
        self_employed_no = 1
        self_employed_yes = 0
    else:
        self_employed_no = 0
        self_employed_yes = 1

    area = request.form['area']
    if area == "rural":
        property_area_rural = 1
        property_area_semiurban = 0
        property_area_urban = 0
    elif area == "semiurban":
        property_area_rural = 0
        property_area_semiurban = 1
        property_area_urban = 0
    else:
        property_area_rural = 0
        property_area_semiurban = 0
        property_area_urban = 1
    new_record_indiv = [[dependents, applicantincome, loanamount, loanamountterm, credithistory, gender_female, gender_male, education_graduate, education_not_graduate, self_employed_no, self_employed_yes, property_area_rural, property_area_semiurban, property_area_urban]]
    prediction_indiv = model_loan_indiv.predict(new_record_indiv)
    if prediction_indiv == 1:
        result_indiv = 'Accepted'
    else:
        result_indiv = 'Declined'
    return render_template('loanindiv.html', prediction_text='Your loan is going to be: {}'.format(result_indiv))
# ======================================================================================================= End of Loan For Individuals


def make_predictions():
    new_data = scrape()
    DATA.append(new_data)
    X, feature_names = feature_engineering(DATA, [])
    proba = MODEL.predict_proba(X[-1].reshape(1,X.shape[1]))[:,1][0]
    probability = "{:.2%}".format(proba)
    if proba < 0.2:
        fraud_text = "Pas de Fraude!"
    else:
        fraud_text = "Fraude !"
    document = {"_id":new_data['object_id'],
                "response":new_data,
                "prediction":fraud_text,
                "probability":proba}
    try:
        coll.insert_one(document)
    except:
        pass
    return fraud_text, probability, new_data


@app.route('/_refresh')
def refresh():
    fraud_text, probability, new_data = make_predictions()
    result = {"fraud_text": fraud_text,
                "probability": probability,
                "new_data": new_data}
    return jsonify(result)


@app.route('/check')
def check():
    line1 = "Number of data points: {0}".format(len(DATA))
    if DATA and TIMESTAMP:
        dt = datetime.fromtimestamp(TIMESTAMP[-1])
        data_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        line2 = "Latest datapoint received at: {0}".format(data_time)
        line3 = DATA[-1]
        output = "{0}\n\n{1}\n\n{2}".format(line1, line2, line3)
    else:
        output = line1
    return output, 200, {'Content-Type': 'text/css; charset=utf-8'}


if __name__ == '__main__':
    # Start Flask app
    app.run(host='localhost', port=8080, debug=True)
