#  Greedy approach to boat balancing. This first approach will focus on making even lineups.

import scipy.stats as stats
import numpy as np


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
    for some_rower in all_rowers:
        heights.append(some_rower.height)

    height_scores = stats.zscore(np.array(heights))
    for i in range(len(all_rowers)):
        total_penalty = 1 - (abs(height_scores[i])*0.02)
        height_adjusted_watts = all_rowers[i].weight_adjusted_erg * total_penalty
        new_total_adjust_watts += height_adjusted_watts

    return new_total_adjust_watts


def main():
    first_varsity = Boat(8, 'starboard')
    rower1 = Rower(400, 183, 73, -60, -58, 35, 40, -20, 'Rower1', 'One', 'starboard')
    rower2 = Rower(390, 190, 74, -60, -58, 35, 40, -20, 'Rower2', 'Two', 'port')
    rower3 = Rower(380, 175, 75, -60, -58, 35, 40, -20, 'Rower3', 'Three', 'starboard')
    rower4 = Rower(386, 160, 71, -60, -58, 35, 40, -20, 'Rower4', 'Four', 'port')
    rower5 = Rower(401, 195, 73, -60, -58, 35, 40, -20, 'Rower5', 'Five', 'starboard')
    rower6 = Rower(365, 170, 71, -60, -58, 35, 40, -20, 'Rower6', 'Six', 'port')
    rower7 = Rower(425, 220, 73, -60, -58, 35, 40, -20, 'Rower7', 'Seven', 'starboard')
    rower8 = Rower(392, 200, 73, -60, -58, 35, 40, -20, 'Rower8', 'Eight', 'port')
    rower9 = Rower(392, 200, 73, -60, -58, 35, 40, -20, 'Rower9', 'Nine', 'starboard')

    first_varsity.add_rower(rower1, True)
    first_varsity.add_rower(rower2, True)
    first_varsity.add_rower(rower5)
    first_varsity.add_rower(rower7)
    first_varsity.add_rower(rower3)

    print("with rower 9 predicted: ")
    print(score_boat(rower9, first_varsity))

    print("with rower 4 predicted: ")
    print(score_boat(rower4, first_varsity))

    first_varsity.print_lineup()


if __name__ == '__main__':
    main()
