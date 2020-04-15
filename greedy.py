#  Greedy approach to boat balancing. This first approach will focus on making even lineups.

import scipy.stats as stats
import numpy as np
import csv


class Boat:
    def __init__(self, size, rig):
        self.rig = rig
        self.size = size
        self.port = []
        self.starboard = []
        self.total_adjusted_watts = 0.0

        for i in range(size // 2):
            self.port.append('open')
            self.starboard.append('open')

    def add_rower(self, rower, forced_placement=False):
        if rower.side == 'starboard':
            self.starboard.append(rower)
            self.starboard = self.starboard[1:]
        else:
            self.port.append(rower)
            self.port = self.port[1:]
        if not forced_placement:
            self.total_adjusted_watts = score_boat(rower, self, True)

    def print_lineup(self):
        lineup = []
        if self.rig == 'starboard':
            for i in range(len(self.starboard)):
                if self.starboard[i] is not 'open':
                    lineup.append(self.starboard[i].first)
                else:
                    lineup.append('open')
                if self.port[i] is not 'open':
                    lineup.append(self.port[i].first)
                else:
                    lineup.append('open')
        else:
            for i in range(len(self.port)):
                if self.port[i] is not 'open':
                    lineup.append(self.port[i].first)
                else:
                    lineup.append('open')
                if self.starboard[i] is not 'open':
                    lineup.append(self.starboard[i].first)
                else:
                    lineup.append('open')
        print(lineup)
        print("Has total adjusted watts: " + str(self.total_adjusted_watts))


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


def weight_adjust(watts, weight):
    pace = (2.80/watts)**(1/3)
    weight_factor = (weight/270) ** 0.222
    adjusted_pace = pace * weight_factor
    adjusted_watts = 2.80/(adjusted_pace**3)
    return adjusted_watts


def score_boat(rower, boat, rescore=False):
    if not rescore:
        if rower.side == 'port':
            if 'open' not in boat.port:
                return boat.total_adjusted_watts
        if rower.side == 'starboard':
            if 'open' not in boat.starboard:
                return boat.total_adjusted_watts

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
        heights.append(some_rower.height)
        catches.append(some_rower.catch)
        slips.append(some_rower.slip)
        washes.append(some_rower.wash)
        finishes.append(some_rower.finish)
        peak_force_locations.append(some_rower.peak_force_location)

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
        new_total_adjust_watts += all_rowers[i].weight_adjusted_erg * accumulated_penalties[i]

    return new_total_adjust_watts


def load_data():
    rowers = []
    with open('rowdata.csv') as csv_file:
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
    return rowers


def find_very_avg_guys(num, pool):
    averages = []
    metrics = ['raw_erg', 'weight', 'height', 'catch',
               'slip', 'wash', 'finish', 'peak_force_location']
    for metric in metrics:
        values = []
        for rower in pool:
            values.append(getattr(rower, metric))
        averages.append(np.mean(values))
    average_rower = Rower(averages[0], averages[1], averages[2], averages[3], averages[4], averages[5], averages[6],
                          averages[7], 'Average', 'Guy', 'None')

    rowers_with_deltas = []
    for rower in pool:
        diffs = []
        for metric in metrics:
            this_guy = getattr(rower, metric)
            avg_guy = getattr(average_rower, metric)
            diffs.append(abs(this_guy - avg_guy))
        total_delta = sum(diffs)
        rowers_with_deltas.append((total_delta, rower))

    data_type = [('delta', float), ('athlete', Rower)]
    temp = np.array(rowers_with_deltas, dtype=data_type)
    temp = np.sort(temp, order='delta')

    most_average = []
    for i in range(num):
        most_average.append(temp[i][1])

    return most_average


def main():
    even_one = Boat(8, 'starboard')
    even_two = Boat(8, 'starboard')
    even_three = Boat(8, 'starboard')
    fleet = [even_one, even_two, even_three]

    pool = load_data()
    starter_guys = find_very_avg_guys(3, pool)

    for i in range(len(fleet)):
        fleet[i].add_rower(starter_guys[i], True)
        pool.remove(starter_guys[i])

    print(len(pool))


if __name__ == '__main__':
    main()
