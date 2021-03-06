'''
实现从网页打开视频并进行检测
去除了复杂的终端　运行，默认打开本地端口8000
python webstreaming.py
改为使用opencv打开摄像头
'''

from GazeTracking.FindEye import findeye
from flask import Response
from flask import Flask, request, redirect, url_for
from flask import render_template
from werkzeug.utils import secure_filename
import threading
import argparse
import time
import cv2
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os
import datetime
# import tensorflow as tf

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = '/home/hichens/Datasets/xieshi/'
SAVE_FOLDER = os.path.join(basedir,  'static/video/')
ALLOWED_EXTENSIONS = set(['mp4', 'flv'])

sns.set()
warnings.filterwarnings("ignore")



outputFrame = None
lock = threading.Lock()
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = datetime.timedelta(seconds=0)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

flag = False # control the camera
filename = ''

# 统计变量
Xrelative = []
Yrelative = []
cosValue = []

# video="http://admin:admin@192.168.43.1:8081/"   #此处@后的ipv4 地址需要修改为自己的地址
video = 0 #"http://admin:admin@192.168.43.1:8081/" #
# "/home/hichens/Datasets/xieshi/lj.mp4"


#@app.route("/index")
@app.route("/")
def index():
    # return the rendered template
    global flag
    flag = False
    return render_template("index.html")

@app.route("/main")
def main():
    # return the rendered template
    global flag
    flag = True
    return render_template("main.html")

@app.route("/result")
def result():
    global flag
    flag = False
    basedir = os.path.abspath(os.path.dirname(__file__))
    path = basedir + "/static/images/result.png"
    fig = plt.gcf()
    fig.set_size_inches(11.5, 6.5) # output size

    '''figure 1 show the x relative position, incluce min, max, avg '''
    plt.subplot(221)
    plt.title('figure 1')
    N = len(Xrelative)
    XX = range(N)
    max_Xrelative, min_Xrelative, avg_Xrelative = max(Xrelative), min(Xrelative), np.mean(Xrelative)
    max_Yrelative, min_Yrelative, avg_Yrelative = max(Yrelative), min(Yrelative), np.mean(Yrelative)
    plt.plot(XX, Xrelative, label='X')
    plt.plot(XX, [avg_Xrelative] * N, '-')
    plt.plot(XX, [max_Xrelative] * N, '--')
    plt.plot(XX, [min_Xrelative] * N, '--')

    '''figure 2 show the y relative position, incluce min, max, avg '''
    plt.subplot(222)
    plt.title('figure 2')
    plt.plot(XX, Yrelative, label='Y')
    plt.plot(XX, [max_Yrelative] * N, '--')
    plt.plot(XX, [min_Yrelative] * N, '--')
    plt.plot(XX, [avg_Yrelative] * N, '-')
    plt.legend()

    '''figure 3 show the S value'''
    plt.subplot(223)
    plt.title('figure 3')
    S_x = np.sqrt(sum([x ** 2 for x in Xrelative]) / (N - 1))
    S_y = np.sqrt(sum([y ** 2 for y in Yrelative]) / (N - 1))
    S_xy = np.sqrt(sum([x ** 2 + y ** 2 for x, y in zip(Xrelative, Yrelative)]) / (N - 1))
    S = [S_x, S_y, S_xy]
    plt.bar(range(len(S)), S)
    plt.xticks(range(len(S)), ['S_x', 'S-y', 'S_xy'])

    '''figure 4 show the cosine relative value '''
    plt.subplot(224)
    plt.title('figure 4')
    plt.plot(range(len(cosValue)), cosValue, '-o', label='cos')
    plt.legend()

    plt.show()
    fig.savefig(path,  dpi=100)
    data = {
        '水平相对移动最大移动值': round(max(Xrelative), 2),
        '水平相对移动最小移动值': round(min(Yrelative), 2),
        '水平相对移动平均移动值': round(np.mean(Yrelative), 2),
        '竖直相对移动最大移动值': round(max(Yrelative), 2),
        '竖直相对移动最小移动值': round(min(Yrelative), 2),
        '竖直相对移动平均移动值': round(np.mean(Yrelative), 2),

        '水平相对移动方差值': round(S_x, 4),
        '竖直相对移动方差值': round(S_y, 4),
        '综合相对移动方差值': round(S_xy, 4)
    }
    return render_template("result.html", data=data)

def detect():
    global outputFrame, lock, Xrelative, Yrelative
    cap = cv2.VideoCapture(video)
    Xrelative.clear()
    Yrelative.clear()
    cosValue.clear()
    while True:
        if flag == False:
            break
        ret, frame = cap.read()
        if ret:
            frame, xr, yr, cosXY = findeye(frame)
            if xr and yr and cosXY:
                Xrelative.append(xr)
                Yrelative.append(yr)
                cosValue.append(cosXY)

            with lock:
                scale_percent = 700  # percent of original size
                width = scale_percent
                height = scale_percent * frame.shape[0] // frame.shape[1]
                frame = cv2.resize(frame, (width, height))
                outputFrame = frame.copy()
        else:
            pass


@app.route("/result")
def open():
    global flag
    flag = True
    return render_template("result.html")

@app.route("/result")
def close():
    global flag
    flag = False
    return render_template("result.html")

def generate():

    global outputFrame, lock
    # time.sleep(1.0)

    t = threading.Thread(target=detect)
    t.daemon = True
    t.start()
    while True:

        with lock:
            if outputFrame is None:
                continue
            (temp, encodedImage) = cv2.imencode(".jpg", outputFrame)
            if not temp:
                continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
            bytearray(encodedImage) + b'\r\n')


@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")

# @app.route("/upload")
# def uploadpage():
#     # return the index of process the video which is from the local or the online caught
#     #type
#     global video, flag
#     flag = False
#     video = 0
#     return render_template("/#2.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/videoprocess', methods=['GET', 'POST'])
def upload_file():
    global filename, video

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print(filename)
            file.save(SAVE_FOLDER+filename)
            video = SAVE_FOLDER+filename
            return redirect(url_for('main'))
        else:
            return redirect(url_for('index')+"#2")

        #return redirect(url_for('uploadpage'))

@app.route('/cameraprocess', methods=['GET', 'POST'])
def camerapage():
    global video
    if request.method == 'POST':
        video = 0
        return redirect(url_for('main'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False,
            threaded=True, use_reloader=False)

