#!flask/bin/python
from flask_cors import CORS
from flask import Flask, request, send_file
import json
import matlab.engine
from time import time 

app = Flask(__name__)
eng = matlab.engine.start_matlab()

eng.addpath(eng.genpath('~/MOLTO-IT-API')) #Directory from server
eng.addpath(eng.genpath('~/MOLTO-IT'))

print("Initialized Matlab in server!")
@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        return "Hello, World!"
    elif request.method == 'GET':
        return "Matlab is Running"

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
        print("El tiempo de ejecución fue:", tiempo_ejecucion)
        
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
        return get_file(Ceres.txt)

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
        eng.molto_it_json(name)
        tiempo_final = time()
        eng.quit()
        tiempo_ejecucion = tiempo_final - tiempo_inicial
        print("El tiempo de ejecucion fue:", tiempo_ejecucion)
        return get_file('~/tmp/Ceres/Results_extended.txt')

    elif request.method == 'GET':
        eng = matlab.engine.start_matlab()
        return "Motor Inicializado."

@app.route('/test', methods=['GET'])
def test():
    global eng
    return eng.figure(nargout=0)

@app.route('/get_file/<file_name>', methods=['GET', 'POST'])
def get_file(file_name):
    if request.method == 'POST':
       data = request.get_json()
       return send_file(data[path], attachment_filename=file_name)
    elif request.method == 'GET':
        return send_file(file_name, attachment_filename=file_name)

if __name__ == '__main__':

     app.run(host="0.0.0.0")
