# -*- coding: utf-8 -*-
"""
Created on Sat Feb 24 10:48:37 2018

@author: marti
"""

#To Do: same ind_adj_std for all adjudicators

import numpy as np
import sys
import matplotlib as mpl
mpl.use('pgf')

def figsize(scale):
    fig_width_pt = 469.755                          # Get this from LaTeX using \the\textwidth
    inches_per_pt = 1.0/72.27                       # Convert pt to inch
    golden_mean = (np.sqrt(5.0)-1.0)/2.0            # Aesthetic ratio (you could change this)
    fig_width = fig_width_pt*inches_per_pt*scale    # width in inches
    fig_height = fig_width*golden_mean              # height in inches
    fig_size = [fig_width,fig_height]
    return fig_size

pgf_with_latex = {                      # setup matplotlib to use latex for output
    "pgf.texsystem": "pdflatex",        # change this if using xetex or lautex
    "text.usetex": True,                # use LaTeX to write all text
    "font.family": "serif",
    "font.serif": [],                   # blank entries should cause plots to inherit fonts from the document
    "font.sans-serif": [],
    "font.monospace": [],
    "axes.labelsize": 10,               # LaTeX default is 10pt font.
    "font.size": 10,
    "legend.fontsize": 8,               # Make the legend/label fonts a little smaller
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.figsize": figsize(0.9),     # default fig size of 0.9 textwidth
    "pgf.preamble": [
        r"\usepackage[utf8x]{inputenc}",    # use utf8 fonts becasue your computer can handle it :)
        r"\usepackage[T1]{fontenc}",        # plots will be generated using this preamble
        ]
    }
mpl.rcParams.update(pgf_with_latex)



import matplotlib.pyplot as plt

# I make my own newfig and savefig functions
def newfig(width):
    plt.clf()
    fig = plt.figure(figsize=figsize(width))
    ax = fig.add_subplot(111)
    return fig, ax

def savefig(filename):
    plt.savefig('{}.pgf'.format(filename), bbox_inches='tight')
    plt.savefig('{}.pdf'.format(filename), bbox_inches='tight')


# Since we are only considering one speaker, define globally
true_speaker_points_glob   = 50

# Variance of the distribution of many adjudicators centered around the 
# true speaker points. 
all_adj_std_glob   = 2

# Not to be confused with the variance of the single 
# adjudicator when awarding points
ind_adj_std_glob = 2

# Number of adjudicators in panel 
N_adj_glob = 5

# Number of finals to be simulated (should be large for stat. significance)
N_fin_glob = 50000

class adjudicator:
    # By default assign global values assigned at the top
    # Can be specified differently when initializing (or not)    
    def __init__(self, all_adj_std = all_adj_std_glob, ind_adj_std = ind_adj_std_glob, true_speaker_points = true_speaker_points_glob):
        self.all_adj_std  = all_adj_std
        self.ind_adj_std  = ind_adj_std
        self.true_speaker_points = true_speaker_points
        self.__assign_point_level()     

    # 'Hochpunkter oder Tiefpunkter?'. Assign the point level of the adjudicator.
    # So far just one speaker, but will stay constant later for the whole duration
    # of a final with several speakers
    # It is still possible that the point level of an adjudicator is not an integer
    # value
    def assign_point_level(self):
        self.point_level = np.random.normal(loc=self.true_speaker_points, scale=self.all_adj_std)
        
    __assign_point_level = assign_point_level

    # When the adjudicator awards points to the speaker: Each time it will differ. 
    # Distribution centered around the individual point level
    def award_points(self):
        awarded_points = np.random.normal(loc=self.point_level, scale=self.ind_adj_std)
        
        # Only integer values can be awarded
        return int(np.round(awarded_points))
    
class panel:
    # By default assign global values assigned at the top
    # Can be specified differently when initializing (or not)
    def __init__(self, N_adj = N_adj_glob, all_adj_std = all_adj_std_glob, ind_adj_std = ind_adj_std_glob):
        self.N_adj = N_adj
        self.all_adj_std = all_adj_std
        self.ind_adj_std = ind_adj_std
        self.judges = []
        self.__set_panel()
        
    #Assign adjudicators. To avoid confusion, these are called judges    
    def set_panel(self):
        for i in range(self.N_adj):
            adjudicator_tmp = adjudicator(all_adj_std = self.all_adj_std, ind_adj_std = self.ind_adj_std)
            self.judges.append(adjudicator_tmp)
            
    __set_panel = set_panel
    
    # For convenience
    def print_point_levels(self):
        print '#### Point level of panel #### \n'
        for i in range(self.N_adj):
            print 'Adjudicator ', i, ': ', self.judges[i].point_level
        print '\n###### \n'

    # Phase 1: each judge awards the individual points
    def award_speaker_points_all(self):
        points = []
        for i in range(self.N_adj):
            points.append(self.judges[i].award_points())
        return points
    
    # Phase 2a: All points are accounted for, i.e. simple averaging 
    def give_result_all(self):
        points = self.award_speaker_points_all()
        #print points
        return np.round(np.mean(points), decimals=2)

    #Phase 2b: Drop largest and smallest points, then conduct averaging of remaining points
    def give_result_with_dropping(self):
        points          = self.award_speaker_points_all()
        sorted_points   = np.sort(points)
        acc_points      = sorted_points[1:self.N_adj-1]
        return np.round(np.mean(acc_points), decimals=2)

# Set a new panel of adjudicators for each final
# Award points for the speaker and save in array
def simulate_finals(N_fin = N_fin_glob, drop_points = True, all_adj_std = all_adj_std_glob, ind_adj_std = ind_adj_std_glob):
    point_list = []
    for i in range(N_fin):
        panel_tmp  = panel(all_adj_std = all_adj_std, ind_adj_std = ind_adj_std)
        if drop_points: points_tmp = panel_tmp.give_result_with_dropping()
        else: points_tmp = panel_tmp.give_result_all()
        point_list.append(points_tmp)
    return point_list


# Criteria: get the mean of the squared deviation of the awarded speaker points in each
# final compared to the true speaker points
def get_acc_criteria(point_list, true_speaker_points = true_speaker_points_glob):
    var_list = []
    for i in range(len(point_list)):
        var_list.append( (point_list[i] - true_speaker_points)**2 )
    # Return the mean and the standard deviation of the mean 
    # (i.e. std of the distribution divided by the sqrt(N), which is the number of finals)
    return np.mean(var_list), np.std(var_list)/np.sqrt(len(var_list))

def show_progress(i, N):
    if N > 10 and ((i * 100) % N == 0):
        sys.stdout.write("\r" + str( int(i * 100 /N)) + '%') 


# Sorry, Stilsache
def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

Red = rgb_to_hex((180, 90, 100)) #180 90 100
Blue = rgb_to_hex((0, 130, 150)) #0 130 150

def plot_result(par_arr, criteria_all, criteria_drop, title, img_fname):
    fig = plt.figure(dpi = 300)
    ax1 = fig.add_subplot(111)


    ax1.errorbar(par_arr, criteria_all[:,0],  yerr= criteria_all[:,1],  label = 'Use all points', color=Blue, linewidth = 3.5) 
    ax1.errorbar(par_arr, criteria_drop[:,0], yerr= criteria_drop[:,1], label = 'Dropping points', color=Red, linewidth = 3.5) 


    for axis in ['top','bottom','left','right']:
        ax1.spines[axis].set_linewidth(1.3)
    ax1.tick_params(axis='both', which='major', labelsize=14, width=3)
    ax1.set_xlabel('$\sigma_n$', fontsize=16)
    #\bar{x} - \mu_{true}
    ax1.set_ylabel('$<(\overline{x} -\mu_{true})^2>$', fontsize=16)
    ax1.legend(loc='best', fontsize=13, frameon=1)
    #title = 'Optimum for ' + str(N) + ' intermediate steps \n all shifted to zero'
    #title = metric
    ax1.set_title(title, fontsize = 16)
    plt.gcf().subplots_adjust(bottom=0.15)
    plt.gcf().subplots_adjust(left=0.18)

    #ax1.tight_layout()
    plt.show()
    fig.savefig(img_fname) 



################# Program ##################

# Change the individual variance of each adjudicator
all_adj_std_arr = np.arange(0., 3., 0.1)
# first column: mean, second column: std of mean
criteria_all    = np.zeros((len(all_adj_std_arr),2))
criteria_drop   = np.zeros((len(all_adj_std_arr),2))

i = 0
for all_adj_std in all_adj_std_arr:
    
    # Show progress of calculation
    show_progress(i, len(all_adj_std_arr))
    
    # Simulate finals
    point_list_finals_all  = simulate_finals(drop_points = True,  all_adj_std = all_adj_std)
    point_list_finals_drop = simulate_finals(drop_points = False, all_adj_std = all_adj_std)

    # Get criteria
    mean_all,  std_all  = get_acc_criteria(point_list_finals_all)
    mean_drop, std_drop = get_acc_criteria(point_list_finals_drop)   
    
    criteria_all[i, 0],  criteria_all[i, 1]  = mean_all,  std_all
    criteria_drop[i, 0], criteria_drop[i, 1] = mean_drop,  std_drop
    
    i += 1

title = 'Influence of Ind. Adj. Variance, $\sigma_n$=2'
img_fname = 'single_speaker_var_sigma_s_sigma_n_2.png'
plot_result(all_adj_std_arr, criteria_all, criteria_drop, title, img_fname)a
