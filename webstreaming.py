'''
实现从网页打开视频并进行检测
去除了复杂的终端　运行，默认打开本地端口8000
python webstreaming.py
改为使用opencv打开摄像头
'''


from GazeTracking.FindEye import findeye
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import time
import cv2
import matplotlib.pyplot as plt
import os
import datetime


outputFrame = None
lock = threading.Lock()
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = datetime.timedelta(seconds=1)
flag = False
Xrelative = []
Yrelative = []

@app.route("/")
@app.route("/index.html")
def index():
    # return the rendered template
    global flag
    flag = False
    return render_template("index.html")

@app.route("/main.html")
def main():
    # return the rendered template
    global flag
    flag = True
    return render_template("main.html")

@app.route("/result.html")
def result():
    global flag
    flag = False
    basedir = os.path.abspath(os.path.dirname(__file__))
    path = basedir + "/static/images/result.png"
    fig = plt.gcf()
    XX = range(len(Xrelative))
    plt.title(str(datetime.datetime.now()))
    plt.plot(XX, Xrelative)
    plt.plot(XX, Yrelative)
    plt.plot(XX, [max(Xrelative)] * len(Xrelative), '-')
    plt.plot(XX, [min(Xrelative)] * len(Xrelative), '-')
    plt.plot(XX, [max(Yrelative)] * len(Xrelative), '-')
    plt.plot(XX, [min(Yrelative)] * len(Xrelative), '-')

    plt.show()
    fig.savefig(path)
    print("draw Done!")
    return render_template("result.html")

def detect():
    global outputFrame, lock, Xrelative, Yrelative
    cap = cv2.VideoCapture(0)
    Xrelative.clear()
    Yrelative.clear()
    while True:
        if flag == False:
            break
        ret, frame = cap.read()
        if ret:
            frame, xr, yr = findeye(frame)
            if xr is not None:
                Xrelative.append(xr)
                Yrelative.append(yr)

            with lock:
                outputFrame = frame.copy()
        else:
            pass


@app.route("/result.html")
def open():
    global flag
    flag = True
    return render_template("result.html")

@app.route("/result.html")
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


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True,
            threaded=True, use_reloader=False)

