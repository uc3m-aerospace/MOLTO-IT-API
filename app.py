#!flask/bin/python
from flask_cors import CORS, cross_origin
from flask import Flask, request, send_file, send_from_directory
from flask_socketio import SocketIO, emit, join_room, send, disconnect
from celery import Celery
import json
import glob
import os
import matlab.engine
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint



scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("MOLTO-a34bb73396ba.json", scope)
client = gspread.authorize(creds)


app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

eng = matlab.engine.start_matlab()
socket = SocketIO(app, async_mode="eventlet")
CORS(app, resources={r"/foo": {"origins": "http://localhost:port"}})


eng.addpath(eng.genpath('~/MOLTO-IT-API')) #Directory from server
eng.addpath(eng.genpath('~/MOLTO-IT'))
static_file_dir = os.path.expanduser('~/tmp/Ceres') #Directory from static file Generations pareto front
static_home_dir = os.path.expanduser('~/MOLTO-IT-API')


print("Initialized Matlab in server!")
@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':      
        return "Hello, World!"
    elif request.method == 'GET':
        return 'Hola Mundo!'

@socket.on('connect')
def on_connect():
    print('Client connected!')

@socket.on('on_connect_data')    
def on_connect_data(data):
    print("Entro aqui!!")
    print(data)
    send_temporal_files(20, data)

@socket.on('disconnect')
def on_disconnect():
    print('Client disconnected')
    disconnect()

@socket.on('my event')
def handle_my_custom_event(json):
    print("Entro aqui")
    print('received json: ' + str(json))

@socket.on('get latest')
def send_temporal_files(maxGen, missionName):
    list_of_files = glob.glob( os.path.expanduser('~/tmp/' + missionName + '/*')) # * means all if need specific format then *.csv
    print(list_of_files)
    if list_of_files:
        list_of_files.remove('/home/brandon/tmp/' + missionName + '/Results_extended.txt')
        sorted_files = sorted(list_of_files, key=lambda x: int(x.split('/')[-1].split('.')[0][3:]))    
        latest_file = max(sorted_files, key=os.path.getctime)
        #print(latest_file)
        data = open(latest_file, 'r')
        print('Sending file...')
        data_ = data.readlines()
        dataDict = {}
        count = -1
        for list in data_:
            count += 1
            x =  list.split()
            #x.pop()
            dataDict[count] = x
        dataDict[len(dataDict)] = latest_file.split('/')[-1].split('.')[0][3:]
        print(dataDict[len(dataDict)-1])
        print(maxGen)
        if maxGen == int(dataDict[len(dataDict)-1]):
            emit('tmp', dataDict)
            print('Thats all!')
            time.sleep(10)
            on_disconnect()
        else:
            emit('tmp', dataDict)
    else:
        print('No files.')
        emit('tmp', {'isAnyFile': False})

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
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def optimization_mission_json():
    global eng
    if request.method == 'POST':
        data = request.get_json()
        #maxGen = data['maxGen']
        task = callGeneticAlgorithm.apply_async(args=[data], countdown=5)
        print(task)
        return "finish"
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
       return socket.emit('ping event', {'data': 42}, namespace='/chat')

       #for file_name in os.listdir(static_file_dir):
       #     print(file_name)
       #     return send_from_directory(static_file_dir, file_name)
        
    elif request.method == 'GET':
        return send_file(file_name, attachment_filename=file_name)

@app.route('/collaborators', methods=['GET'])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def get_collaborators():
    if request.method == 'GET':
       time.sleep(1)
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

@celery.task
def callGeneticAlgorithm(data):
    with open('example.json', 'w') as json_file: 
        json.dump(data, json_file)
    name = open('example.json', 'r').read()
    eng.molto_it_json(name, nargout=0) 
    eng.quit()
    return send_from_directory(static_file_dir, 'Results_extended.txt')

if __name__ == '__main__':
    socket.run(app, host="0.0.0.0", threaded=True)
