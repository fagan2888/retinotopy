from __future__ import division
import json
import itertools

import numpy as np

from psychopy import event
from visigoth import flexible_values
from visigoth.stimuli import Point, RandomDotMotion


class DotBar(object):

    def __init__(self, exp):

        self.exp = exp

        self.dot_params = dict(elliptical=False,
                               size=exp.p.dot_size,
                               color=exp.p.dot_color,
                               density=exp.p.dot_density,
                               speed=exp.p.dot_speed,
                               interval=exp.p.dot_interval)

        # Note that this code is written flexibly w.r.t number of segments but
        # it is being hardcoded at 3 here and not exposed in the params

        self.n_segments = n = 3
        segment_length = exp.p.field_size / n
        self.segment_length = segment_length - exp.p.bar_segment_gap
        self.segment_width = exp.p.bar_width
        offsets = np.linspace(-1, 1, n + 1) * (exp.p.field_size / 2)
        offsets = offsets[:-1] + (segment_length / 2)
        self.segment_offsets = offsets

    def set_position(self, ori, rel_pos):

        self.stims = []

        for i in range(self.n_segments):

            if ori == "v":
                posx = rel_pos * self.exp.p.field_size / 2
                posy = self.segment_offsets[i]
                pos = posx, posy
                aperture = self.segment_width, self.segment_length
            elif ori == "h":
                posx = self.segment_offsets[i]
                posy = rel_pos * self.exp.p.field_size / 2
                pos = posx, posy
                aperture = self.segment_length, self.segment_width

            stim = RandomDotMotion(self.exp.win,
                                   pos=pos,
                                   aperture=aperture,
                                   **self.dot_params)

            self.stims.append(stim)

    def reset(self):

        for stim in self.stims:
            stim.reset()

    def update(self, dirs, coh):

        for dir, stim in zip(dirs, self.stims):
            stim.update(dir, coh)

    def draw(self):

        for stim in self.stims:
            stim.draw()


def create_stimuli(exp):
    """Define stimulus objects."""
    # Fixation point
    fix = Point(exp.win,
                exp.p.fix_pos,
                exp.p.fix_radius,
                exp.p.fix_color)

    # Ensemble of random dot stimuli
    dots = DotBar(exp)

    return locals()


def define_cmdline_params(self, parser):
    """Choose the traversal schedule at runtime on command line."""
    parser.add_argument("--schedule", required=True)


def generate_trials(exp):

    # Load a file to determine the order of bar traversals
    # This lets us externally optimize/balance and repeat runs
    with open("schedules.json") as fid:
        schedules = json.load(fid)
        schedule = schedules[exp.p.schedule]

    # Define the permutations of motion directions within the segments
    # Note that 3 bar segments is hardcoded here
    mot_choices = list(itertools.permutations([1, 0, 0]))

    # Define valid motion angles for each bar orientation
    ori_to_dir_map = dict(h=[0, 180], v=[90, 270])

    # Outer iteration loop is over bar traversals
    for ori, dir in schedule:

        # Define the step positions
        if dir == "p":
            positions = np.linspace(-1, 1, exp.p.traversal_steps)
        elif dir == "n":
            positions = np.linspace(1, -1, exp.p.traversal_steps)

        # Inner iteration loop is over steps within the traversal
        for step, pos in enumerate(positions, 1):

            # Determine the angular direction of motion across the bar
            mot_idx = flexible_values(mot_choices)
            trial_dirs = np.random.permutation(ori_to_dir_map[ori]) 
            dot_dirs = trial_dirs[np.array(mot_idx)]

            # Determine whether there is an odd segment (used for the task)
            odd_segment = mot_idx.index(1)

            info = exp.trial_info(

                bar_ori=ori,
                bar_dir=dir,
                bar_step=step,
                bar_pos=pos,

                dot_dirs=dot_dirs,
                odd_segment=odd_segment,

            )

            yield info


def run_trial(exp, info):

    exp.s.dots.set_position(info.bar_ori, info.bar_pos)
    exp.s.dots.reset()

    trial_dur = exp.p.traversal_duration / exp.p.traversal_steps
    for i in exp.frame_range(seconds=trial_dur):

        exp.s.dots.update(info.dot_dirs, .5)
        exp.draw(["dots", "fix"])

    return info
