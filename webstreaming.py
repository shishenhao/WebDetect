'''
实现从网页打开视频并进行检测
python webstreaming.py --ip 0.0.0.0 --port000
'''


from GazeTracking.FindEye import findeye
from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import time
import cv2


outputFrame = None
lock = threading.Lock()

app = Flask(__name__)


@app.route("/")
@app.route("/index.html")
def index():
    # return the rendered template
    return render_template("index.html")

@app.route("/result.html")
def result():
    # return the rendered template
    return render_template("result.html")


def detect():
    vs = VideoStream(src=0).start()
    time.sleep(2.0)

    global outputFrame, lock
    while True:
        frame = vs.read()
        frame = findeye(frame)
        with lock:
            outputFrame = frame.copy()
    vs.stop()

def generate():

    global outputFrame, lock
    while True:
        with lock:
            if outputFrame is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            if not flag:
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
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=True, default='0.0.0.0',
        help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=True, default=8000,
        help="ephemeral port number of the server (1024 to 65535)")
    args = vars(ap.parse_args())

    # start a thread that will perform detection
    t = threading.Thread(target=detect)
    t.daemon = True
    t.start()

    app.run(host=args["ip"], port=args["port"], debug=True,
            threaded=True, use_reloader=False)

