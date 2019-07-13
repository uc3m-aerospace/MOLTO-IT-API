#!flask/bin/python
from flask_cors import CORS, cross_origin
from flask import Flask, request, send_file, send_from_directory
import json
import os
import matlab.engine
from time import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint



scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("MOLTO-6c458acbb69f.json", scope)
client = gspread.authorize(creds)


app = Flask(__name__)
eng = matlab.engine.start_matlab()
cors = CORS(app, resources={r"/foo": {"origins": "http://localhost:port"}})

eng.addpath(eng.genpath('~/MOLTO-IT-API')) #Directory from server
eng.addpath(eng.genpath('~/MOLTO-IT'))
static_file_dir = os.path.expanduser('~/tmp/Ceres') #Directory from static file Generations pareto front

print("Initialized Matlab in server!")
@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        
        
        return "Hello, World!"
    elif request.method == 'GET':
        print("a")
        return static_file_dir

@app.route('/init', methods=['GET','POST'])
def init():
    if request.method == 'POST':
        return "Hello, World!"
    elif request.method == 'GET':
        eng = matlab.engine.start_matlab()
        return "Motor Inicializado!!!"

@app.route('/sum/', methods=['GET','POST'])
def sum():
    if request.method == 'POST':
        tiempo_inicial = time() 
        data = request.get_json()
        number1 = data["number1"]
        number2 = data["number2"]
        sum = number1 + number2
        tiempo_final = time() 
        string = str(sum)
        tiempo_ejecucion = tiempo_final - tiempo_inicial
        print("El tiempo de ejecucion fue:", tiempo_ejecucion)

        return string
    elif request.method == 'GET':
        eng = matlab.engine.start_matlab()
        return "Motor Inicializado!!!"
        
@app.route('/sum/matlab', methods=['GET','POST'])
def sum_matlab():
    global eng
    if request.method == 'POST':
        tiempo_inicial = time() 
        data = request.get_json()
        number1 = data["number1"]
        number2 = data["number2"]
        a = eng.sum_custom(number1, number2)
        tiempo_final = time() 
        string = str(a)
        tiempo_ejecucion = tiempo_final - tiempo_inicial
        print("El tiempo de ejecucion fue:", tiempo_ejecucion)
        return string
    elif request.method == 'GET':
        eng = matlab.engine.start_matlab()
        return "Motor Inicializado!!!"
        
@app.route('/optimization/mission', methods=['GET', 'POST'])
def optimization_mission():
    global eng
    if request.method == 'POST':
        tiempo_inicial = time() 
        data = request.get_json()
        print(data)
       	departureBody = data["departureBody"]
        arrivalBody = data["arrivalBody"]
        missionType = data["missionType"]
        launchWindow = data["launchWindow"]
        flybyNumbers = data["flybyNumbers"]
        flybyBodies = data["flybyBodies"]
        minFlyByRadius = data["minFlyByRadius"]
        timeFlight = data["timeFlight"] 
        eng.Examples(nargout=0)
        tiempo_final = time() 
        eng.quit()
        tiempo_ejecucion = tiempo_final - tiempo_inicial
        print("El tiempo de ejecucion fue:", tiempo_ejecucion)
        return get_file('Ceres.txt')

    elif request.method == 'GET':
        eng = matlab.engine.start_matlab()
        return "Motor Inicializado."

@app.route('/optimization/mission/json', methods=['GET', 'POST'])
def optimization_mission_json():
    global eng
    if request.method == 'POST':
        tiempo_inicial = time()
        data = request.get_json()
        print(data)
        with open('example.json', 'w') as json_file:
            json.dump(data, json_file)

        name = open('example.json', 'r').read()
        eng.molto_it_json(name, nargout=0)
        tiempo_final = time()
        eng.quit()
        tiempo_ejecucion = tiempo_final - tiempo_inicial
        print("El tiempo de ejecucion fue:", tiempo_ejecucion)
        return send_from_directory(static_file_dir, 'Results_extended.txt')

    elif request.method == 'GET':
        eng = matlab.engine.start_matlab()
        return "Motor Inicializado."

@app.route('/test', methods=['GET'])
def test():
    global eng
    return eng.figure(nargout=0)

@app.route('/get_file/<path:file_name>/', methods=['GET', 'POST'])
def get_file(file_name):
    if request.method == 'POST':
       print(static_file_dir)
       print(file_name)
       data = request.get_json()
       for file_name in static_file_dir: 
            print(file_name)
            return send_from_directory(static_file_dir, file_name)
        
    elif request.method == 'GET':
        return send_file(file_name, attachment_filename=file_name)

@app.route('/collaborators', methods=['GET'])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def get_collaborators():
    if request.method == 'GET':
       time.sleep(2)
       sheet = client.open("colaboradores").sheet1  # Open the spreadhseet
       data = sheet.get_all_records()  # Get a list of all records
       return json.dumps(data)


@app.route('/sliders', methods=['GET'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_sliders():
    if request.method == 'GET':
      time.sleep(2)
      sheet = client.open('Slider').sheet1
      data = sheet.get_all_records()
      return json.dumps(data)


if __name__ == '__main__':

     app.run(host="0.0.0.0")
