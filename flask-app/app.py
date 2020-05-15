# app.py
import os
import io
import csv
import sys
import copy
import random
import scipy.stats as stats
import numpy as np
import uuid
from flask import Flask, flash, request, redirect, url_for, make_response, render_template
from werkzeug.utils import secure_filename
import codecs

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'csv'}

loaded_data = []
used_guys = []
fleet = []

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

@app.route('/upload-file', methods=['GET', 'POST'])
def upload_file():
    global loaded_data
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file_object = request.files['file']
        boat_class = request.form["boatClass"]
        starboard_boat_count = int(request.form["boatCount"])
        port_boat_count = int(request.form["boatCount2"])
        file_stream = file_object.stream
        data = []
        stream = codecs.iterdecode(file_object.stream, 'utf-8')
        for row in csv.reader(stream, dialect=csv.excel):
            if row:
                data.append(row)
        # if user does not select file, browser also
        # submit an empty part without filename
        if file_object.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file_object and allowed_file(file_object.filename):
            filename = secure_filename(file_object.filename)
            rowers = {}
            line_count = 0
            for row in data:
                if line_count == 0:
                    line_count += 1
                else:
                    # erg, weight, height, catch, slip, wash, finish, peak_force_location, first, last, side
                    athlete = Rower(int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]),
                            float(row[6]), float(row[7]), str(row[8]), str(row[9]), str(row[10]))
                    new_rower_id = uuid.uuid4()
                    rowers[new_rower_id] = athlete
                    line_count += 1
            loaded_data = rowers
            boatings = make_boatings(boat_class, starboard_boat_count, port_boat_count)
            return render_template("lineups.html", lineups = boatings, data = loaded_data)
    return render_template("inputForm.html")

@app.route('/success')
def good_upload():
    rowers = request.args.get('uploaded')
    return '<h1>File has been uploaded!!! Found: ' + str(len(rowers)) + '</h1>'   

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
        self.delta = 0

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

# Below here is boat filling algorithm
class Boat:
    def __init__(self, size, rig, name):
        self.rig = rig
        self.size = size
        self.port = []
        self.starboard = []
        self.total_adjusted_watts = 0.0
        self.name = name

        for i in range(size // 2):
            self.port.append('open')
            self.starboard.append('open')

    def full(self):
        if 'open' not in (self.port + self.starboard):
            return True
        else:
            return False

    def add_rower(self, rower, forced_placement=False):
        if loaded_data[rower].side == 'starboard':
            if 'open' in self.starboard:
                self.starboard.append(rower)
                self.starboard.remove('open')
        else:
            if 'open' in self.port:
                self.port.append(rower)
                self.port.remove('open')

        self.total_adjusted_watts = round(score_boat(rower, self, True),2)

    def remove_rower(self, rower):
        if rower in self.starboard:
            self.starboard.remove(rower)
            self.starboard.append('open')
        if rower in self.port:
            self.port.remove(rower)
            self.port.append('open')

    def print_lineup(self):
        lineup = []
        if self.rig == 'starboard':
            for i in range(len(self.starboard)):
                if self.starboard[i] is not 'open':
                    lineup.append(loaded_data[self.starboard[i]].first + " " + loaded_data[self.starboard[i]].last)
                else:
                    lineup.append('open')
                if self.port[i] is not 'open':
                    lineup.append(loaded_data[self.port[i]].first + " " + loaded_data[self.port[i]].last)
                else:
                    lineup.append('open')
        else:
            for i in range(len(self.port)):
                if self.port[i] is not 'open':
                    lineup.append(loaded_data[self.port[i]].first + " " + loaded_data[self.port[i]].last)
                else:
                    lineup.append('open')
                if self.starboard[i] is not 'open':
                    lineup.append(loaded_data[self.starboard[i]].first + " " + loaded_data[self.starboard[i]].last)
                else:
                    lineup.append('open')
        print(lineup)
        print("Has total adjusted watts: " + str(self.total_adjusted_watts))


def score_boat(rower, boat, rescore=False):
    if not rescore:
        if loaded_data[rower].side == 'port':
            if 'open' not in boat.port:
                return float("-inf")
        if loaded_data[rower].side == 'starboard':
            if 'open' not in boat.starboard:
                return float("-inf")

    # what happens if we add this guy

    new_total_adjust_watts = 0.0
    if rescore:
        all_rowers = []
    else:
        all_rowers = [rower]
    for some_rower in (boat.port + boat.starboard):
        if some_rower is not 'open':
            all_rowers.append(some_rower)

    heights = []
    catches = []
    slips = []
    washes = []
    finishes = []
    peak_force_locations = []
    for some_rower in all_rowers:
        heights.append(loaded_data[some_rower].height)
        catches.append(loaded_data[some_rower].catch)
        slips.append(loaded_data[some_rower].slip)
        washes.append(loaded_data[some_rower].wash)
        finishes.append(loaded_data[some_rower].finish)
        peak_force_locations.append(loaded_data[some_rower].peak_force_location)

    accumulated_penalties = []
    for i in range(len(all_rowers)):
        accumulated_penalties.append(1)

    metrics = [heights, catches, slips, washes, finishes, peak_force_locations]
    for METRIC in metrics:
        # By default, 2% penalty in each category, can be adjusted with conditional
        penalty = 0.02
        if len(np.unique(np.array(METRIC))) > 1:
            scores = stats.zscore(np.array(METRIC))
            for i in range(len(all_rowers)):
                accumulated_penalties[i] = accumulated_penalties[i] - (abs(scores[i]) * penalty)
        else:
            for i in range(len(all_rowers)):
                accumulated_penalties[i] = accumulated_penalties[i]

    # Apply calculated penalties
    for i in range(len(all_rowers)):
        new_total_adjust_watts += loaded_data[all_rowers[i]].weight_adjusted_erg * accumulated_penalties[i]

    return new_total_adjust_watts


def load_data():
    global loaded_data
    return loaded_data


def find_very_avg_guys(num):
    averages = []
    metrics = ['raw_erg', 'weight', 'height', 'catch',
               'slip', 'wash', 'finish', 'peak_force_location']
    for metric in metrics:
        values = []
        for rower in loaded_data.keys():
            values.append(getattr(loaded_data[rower], metric))
        averages.append(np.mean(values))
    average_rower = Rower(averages[0], averages[1], averages[2], averages[3], averages[4], averages[5], averages[6],
                          averages[7], 'Average', 'Guy', 'None')

    rowers_with_deltas = []
    for rower in loaded_data.keys():
        diffs = []
        for metric in metrics:
            this_guy = getattr(loaded_data[rower], metric)
            avg_guy = getattr(average_rower, metric)
            diffs.append(abs(this_guy - avg_guy))
        total_delta = sum(diffs)
        loaded_data[rower].delta = total_delta
        rowers_with_deltas.append(rower)

    # data_type = [('delta', float), ('athlete', Rower)]
    # temp = np.array(rowers_with_deltas, dtype=data_type)
    # temp = np.sort(temp, order='delta')
    rowers_with_deltas.sort(key=lambda x: loaded_data[x].delta)

    most_average = []
    for i in range(num):
        most_average.append(rowers_with_deltas[i])

    return most_average


def boat_difference(fleet):
    total_power = 0
    for boat in fleet:
        total_power += boat.total_adjusted_watts
    avg_power = total_power / len(fleet)
    total_diff_from_avg = 0
    for boat in fleet:
        total_diff_from_avg += abs(boat.total_adjusted_watts - avg_power)

    return total_diff_from_avg


def get_key(item):
    return item[0]


def fleet_full(fleet, count=False):
    open_count = 0
    for boat in fleet:
        athletes = boat.starboard + boat.port
        for athlete in athletes:
            if athlete == 'open':
                open_count += 1
    if count:
        return open_count
    else:
        if open_count > 0:
            return False
        else:
            return True


def refresh_rower_pool(fleet):
    used = []
    for boat in fleet:
        for rower in boat.starboard + boat.port:
            if rower is not 'open':
                used.append(rower)
    global used_guys
    used_guys = used

def make_boatings(boat_class, starboard_boat_count, port_boat_count):
    global fleet
    global used_guys
    size = 0
    if boat_class == "Eight":
        size = 8
    elif boat_class == "Four":
        size = 4
    else:
        size = 2
    fleet = []
    for i in range(starboard_boat_count):
        boat_name = "Starboard " + str(i + 1)
        this_boat = Boat(size, 'starboard', boat_name)
        fleet.append(this_boat)
    for i in range(port_boat_count):
        boat_name = "Port " + str(i + 1)
        this_boat = Boat(size, 'port', boat_name)
        fleet.append(this_boat)

    starter_guys = find_very_avg_guys(len(fleet))

    for i in range(len(fleet)):
        fleet[i].add_rower(starter_guys[i], True)
        used_guys.append(starter_guys[i])

    while not fleet_full(fleet):
        for i in range(len(fleet)):
             # Create an option resulting from adding each rowing to the boat
            options = [(0, fleet)]
            for rower in loaded_data.keys():
                if rower not in used_guys:
                    fleet_full(fleet, True)
                    side = loaded_data[rower].side
                    first = loaded_data[rower].first
                    if side == 'starboard':
                        if 'open' in fleet[i].starboard:
                            new_fleet = copy.deepcopy(fleet)
                            new_fleet[i].add_rower(rower) 
                            options.append((boat_difference(new_fleet), new_fleet))
                    if side == 'port':
                        if 'open' in fleet[i].port:
                            new_fleet = copy.deepcopy(fleet)
                            new_fleet[i].add_rower(rower) 
                            options.append((boat_difference(new_fleet), new_fleet))
            prev_count = fleet_full(fleet, True)
            if len(options) > 1:
                selected = options[2][1]
            else:
                selected = options[0][1]
            fleet[i] = selected[i]
            new_count = fleet_full(fleet, True)

            refresh_rower_pool(fleet)
    return fleet