#!flask/bin/python
from flask_cors import CORS, cross_origin
from flask import Flask, request, send_file, send_from_directory
from flask_restful import Api
from flask_socketio import SocketIO, emit, join_room, send, disconnect
from celery import Celery
from io import BytesIO
import json
import glob
import os
import io
import matlab.engine
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
import base64
from flask_jwt import JWT, current_identity
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required


'''
    MOLTO - MISSION DESIGNER - API

    Authors: Brandon Israel Escamilla Estrada
             brandon.escamilla@outlook.com
             
             David Morante Gonzaléz             
             dmorante@ing.uc3m.es
'''

'''
    Google Cloud Configuration
    In this section, we configure google account in order to get spreadsheet files from drive. 
    MOLTO-a34bb73396ba.json is created by Google in the Google Cloud Console.
'''
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
# creds = ServiceAccountCredentials.from_json_keyfile_name("MOLTO-a34bb73396ba.json", scope)
# client = gspread.authorize(creds)


'''
    Flask App Configuration
    In this section, the celery service is configured using redis as the main broker. 
    The CORS is also configured to receive request from another servers.
'''
app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
api = Api(app)
'''
    Database Configuration
'''
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'molto'
db = SQLAlchemy(app)

'''
    Celery Configuration
'''
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
CORS(app, resources={r"/foo": {"origins": "http://localhost:port"}})

'''
    JWT Configuration
'''
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'
jwt = JWTManager(app)
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

'''
    Matlab and SocketIO Configuration
    In this section, the Matlab engine is started and the SocketIO port is configured.
'''
eng = matlab.engine.start_matlab()
eng.addpath(eng.genpath('~mrd/Documents/MOLTO-IT-API-MATLAB'))  # Directory from server
eng.addpath(eng.genpath('~mrd/Documents/MOLTO-IT-MATLAB'))
socket = SocketIO(app)

'''
    Global Variables
'''
static_file_dir = os.path.expanduser('~mrd/tmp/Ceres')  # Directory from static file Generations pareto front
static_home_dir = os.path.expanduser('~mrd/Documents/MOLTO-IT-MATLAB')
gettime = time.time()

'''
    Sockets 
'''


@socket.on('connect')
def on_connect():
    print('Client connected!')


@socket.on('on_connect_data')
def on_connect_data(data):
    send_temporal_files(data['generations'], data['problem_name'])


@socket.on('disconnect')
def on_disconnect():
    print('Client disconnected')
    disconnect()


@socket.on('get latest')
def send_temporal_files(maxGen, missionName):
    list_of_files = glob.glob(
        os.path.expanduser('~mrd/tmp/' + missionName + '/*'))  # * means all if need specific format then *.csv

    if list_of_files:

        list_of_files.remove('~mrd/tmp/' + missionName + '/Results_extended.txt')

        matchers = ['Trajectory', 'Accel']

        matching = [s for s in list_of_files if any(xs in s for xs in matchers)]

        res = [i for i in list_of_files if i not in matching]

        sorted_files = sorted(res, key=lambda x: int(x.split('/')[-1].split('.')[0][3:]))

        latest_file = max(sorted_files, key=os.path.getctime)

        data = open(latest_file, 'r')
        print(data)
        print('Sending file...')
        data_ = data.readlines()
        dataDict = {}
        count = -1
        for list in data_:
            count += 1
            x = list.split()
            dataDict[count] = x

        dataDict[len(dataDict)] = latest_file.split('/')[-1].split('.')[0][3:]

        if maxGen == int(dataDict[len(dataDict) - 1]):
            emit('tmp', dataDict)
            print('Thats all!')
            time.sleep(10)
            on_disconnect()
        else:
            emit('tmp', dataDict)
    else:
        print('No files.')
        emit('tmp', {'isAnyFile': False})


'''
    Import login routes
'''
# from resources import UserRegistration, UserLogin, UserLogoutAccess, \
#     UserLogoutRefresh, TokenRefresh, AllUsers, SecretResource
#
# api.add_resource(UserRegistration, '/registration')
# api.add_resource(UserLogin, '/login')
# api.add_resource(UserLogoutAccess, '/logout/access')
# api.add_resource(UserLogoutRefresh, '/logout/refresh')
# api.add_resource(TokenRefresh, '/token/refresh')
# api.add_resource(AllUsers, '/users')
# api.add_resource(SecretResource, '/secret')

'''
    API Routes
'''


# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()


# Check if user is in blacklist
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    from models import RevokedTokenModel as rtm
    return rtm.is_jti_blacklisted(jti)


print("The server is up and running.")


@app.route('/', methods=['GET', 'POST'])
# @jwt_required()
def index():
    if request.method == 'POST':
        return "MOLTO - MISSION DESIGNER - API"
    elif request.method == 'GET':
        return "MOLTO - MISSION DESIGNER - API"


@app.route('/optimization/mission/json', methods=['GET', 'POST'])
# @jwt_required()
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def optimization_mission_json():
    global eng
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        # maxGen = data['maxGen']
        task = callGeneticAlgorithm.apply_async(args=[data], countdown=5)
        if data['plot'] > 0:
            static_file_dir = os.path.expanduser('~mrd/tmp/' + data['problem_name'] + '/Trajectory' + str(
                data['plot']) + '.png')  # Directory from static file Generations pareto front
            return get_file(static_file_dir)
        else:
            return "finish"
    elif request.method == 'GET':
        eng = matlab.engine.start_matlab()
        return "Motor Inicializado."


@app.route('/get_file/<path:located>/', methods=['GET', 'POST'])
def get_file(located):
    if request.method == 'POST':
        time.sleep(10)
        # First, encode our image with base64
        with open(located, "rb") as imageFile:
            img = base64.b64encode(imageFile.read())
        return img


@PendingDeprecationWarning
@app.route('/collaborators', methods=['GET'])
# @jwt_required()
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def get_collaborators():
    global gettime
    if request.method == 'GET':
        if (time.time() - gettime > 60 * 59):
            # client.login()
            gettime = time.time()
        time.sleep(1)
        # sheet = client.open("colaboradores").sheet1  # Open the spreadhseet
        # data = sheet.get_all_records()  # Get a list of all records
        return json.dumps({})


@PendingDeprecationWarning
@app.route('/sliders', methods=['GET'])
# @jwt_required()
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_sliders():
    global gettime
    if request.method == 'GET':
        if (time.time() - gettime > 60 * 59):
            # client.login()
            gettime = time.time()
        time.sleep(2)
        # sheet = client.open('Slider').sheet1
        # data = sheet.get_all_records()
        return json.dumps({})


@celery.task
def callGeneticAlgorithm(data):
    with open('example.json', 'w') as json_file:
        json.dump(data, json_file)
    print(data)
    name = open('example.json', 'r').read()
    eng.molto_it_json(name, nargout=0)
    eng.quit()
    return send_from_directory(static_file_dir, 'Results_extended.txt')


if __name__ == '__main__':
    socket.run(app, host="0.0.0.0")
