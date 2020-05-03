# app.py
import os
import io
import csv
import sys
import copy
import random
from flask import Flask, flash, request, redirect, url_for, make_response
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'csv'}



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def hello_world():
 return '<h1>Yeah, that is Zappa! Zappa! Zap! Zap!</h1>'

@app.route('/test')
def form():
    return """
        <html>
            <body>
                <h1>Transform a file demo</h1>

                <form action="/transform" method="post" enctype="multipart/form-data">
                    <input type="file" name="data_file" />
                    <input type="submit" />
                </form>
            </body>
        </html>
    """

@app.route('/transform', methods=["POST"])
def transform_view():
    f = request.files['data_file']
    if not f:
        return "No file"

    stream = io.StringIO(f.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    #print("file contents: ", file_contents)
    #print(type(file_contents))
    print(csv_input)
    for row in csv_input:
        print(row)

    stream.seek(0)
    result = transform(stream.read())

    response = make_response(result)
    response.headers["Content-Disposition"] = "attachment; filename=result.csv"
    return response

@app.route('/upload-file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            rowers = []
            with open(file) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                line_count = 0
                for row in csv_reader:
                    if line_count == 0:
                        line_count += 1
                    else:
                        # erg, weight, height, catch, slip, wash, finish, peak_force_location, first, last, side
                        athlete = Rower(int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]),
                                float(row[6]), float(row[7]), str(row[8]), str(row[9]), str(row[10]))
                        rowers.append(athlete)
                        line_count += 1
                print(len(rowers), file=sys.stderr)
                return redirect('/')
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    ''' 

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Rower:
    def __init__(self, erg, weight, height, catch, slip, wash, finish, peak_force_location, first, last, side):
        self.first = first
        self.last = last
        self.side = side
        self.raw_erg = erg
        self.weight_adjusted_erg = weight_adjust(erg, weight)
        self.height = height
        self.weight = weight
        self.catch = catch
        self.slip = slip
        self.wash = wash
        self.finish = finish
        self.peak_force_location = peak_force_location

    def is_same(self, rower):
        if self.first == rower.first and self.last == rower.last:
            return True
        else:
            return False

def weight_adjust(watts, weight):
    pace = (2.80/watts)**(1/3)
    weight_factor = (weight/270) ** 0.222
    adjusted_pace = pace * weight_factor
    adjusted_watts = 2.80/(adjusted_pace**3)
    return adjusted_watts

def transform(text_file_contents):
    return text_file_contents.replace("=", ",")

# We only need this for local development.
if __name__ == '__main__':
 app.run()