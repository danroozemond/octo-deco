# Please see LICENSE.md
from collections import namedtuple

ZHL16Constants = namedtuple('ZHL16Constants', [
    'N_TISSUES',
    'N2_HALFTIMES', 'N2_A_VALUES', 'N2_B_VALUES',
    'HE_HALFTIMES', 'HE_A_VALUES', 'HE_B_VALUES'
]);

# ZHL_16A (Source: wikipedia)
ZHL_16A = ZHL16Constants(
    N_TISSUES = 16,
    N2_HALFTIMES = [ 4, 8, 12.5, 18.5, 27, 38.3, 54.3, 77, 109, 146, 187, 239, 305, 390, 498, 635 ],
    N2_A_VALUES = [ 1.2599, 1, 0.8618, 0.7562, 0.6667, 0.5933, 0.5282, 0.4701, 0.4187, 0.3798, 0.3497, 0.3223, 0.2971,
                    0.2737, 0.2523, 0.2327 ],
    N2_B_VALUES = [ 0.505, 0.6514, 0.7222, 0.7725, 0.8125, 0.8434, 0.8693, 0.891, 0.9092, 0.9222, 0.9319, 0.9403,
                    0.9477, 0.9544, 0.9602, 0.9653 ],
    HE_HALFTIMES = [ 1.5, 3, 4.7, 7, 10.2, 14.5, 20.5, 29.1, 41.1, 55.1, 70.6, 90.2, 115.1, 147.2, 187.9, 239.6 ],
    HE_A_VALUES = [ 1.7435, 1.3838, 1.1925, 1.0465, 0.9226, 0.8211, 0.7309, 0.6506, 0.5794, 0.5256, 0.484, 0.446,
                    0.4112, 0.3788, 0.3492, 0.322 ],
    HE_B_VALUES = [ 0.1911, 0.4295, 0.5446, 0.6265, 0.6917, 0.742, 0.7841, 0.8195, 0.8491, 0.8703, 0.886, 0.8997,
                    0.9118, 0.9226, 0.9321, 0.9404 ]
);

# ZHL_16C, variant 1b
ZHL_16C_1b = ZHL16Constants(
    N_TISSUES = 16,
    N2_HALFTIMES = [ 5.0, 8.0, 12.5, 18.5,
                     27.0, 38.3, 54.3, 77.0,
                     109.0, 146.0, 187.0, 239.0,
                     305.0, 390.0, 498.0, 635.0 ],
    N2_A_VALUES = [ 1.1696, 1.0, 0.8618, 0.7562,
                    0.62, 0.5043, 0.441, 0.4,
                    0.375, 0.35, 0.3295, 0.3065,
                    0.2835, 0.261, 0.248, 0.2327 ],
    N2_B_VALUES = [ 0.5578, 0.6514, 0.7222, 0.7825,
                    0.8126, 0.8434, 0.8693, 0.8910,
                    0.9092, 0.9222, 0.9319, 0.9403,
                    0.9477, 0.9544, 0.9602, 0.9653 ],
    HE_HALFTIMES = [ 1.88, 3.02, 4.72, 6.99,
                     10.21, 14.48, 20.53, 29.11,
                     41.20, 55.19, 70.69, 90.34,
                     115.29, 147.42, 188.24, 240.03 ],
    HE_A_VALUES = [ 1.6189, 1.383, 1.1919, 1.0458,
                    0.922, 0.8205, 0.7305, 0.6502,
                    0.595, 0.5545, 0.5333, 0.5189,
                    0.5181, 0.5176, 0.5172, 0.5119 ],
    HE_B_VALUES = [ 0.4770, 0.5747, 0.6527, 0.7223,
                    0.7582, 0.7957, 0.8279, 0.8553,
                    0.8757, 0.8903, 0.8997, 0.9073,
                    0.9122, 0.9171, 0.9217, 0.9267 ]
);

# ZHL_16C (source: Buhlmann Tauchmedizin, 2002; via OSTC2)
ZHL_16C_1a = ZHL16Constants(
    N_TISSUES = 16,
    N2_HALFTIMES = [4.0,8.0,12.5,18.5,27.0,38.3,54.3,77.0,109.0,146.0,187.0,239.0,305.0,390.0,498.0,635.0],
    N2_A_VALUES = [1.2599,1.0000,0.8618,0.7562,0.6200,0.5043,0.4410,0.4000,0.3750,0.3500,0.3295,0.3065,0.2835,0.2610,0.2480,0.2327],
    N2_B_VALUES = [0.5050,0.6514,0.7222,0.7825,0.8126,0.8434,0.8693,0.8910,0.9092,0.9222,0.9319,0.9403,0.9477,0.9544,0.9602,0.9653],
    HE_HALFTIMES = [1.51,3.02,4.72,6.99,10.21,14.48,20.53,29.11,41.20,55.19,70.69,90.34,115.29,147.42,188.24,240.03] ,
    HE_A_VALUES = [1.7424,1.3830,1.1919,1.0458,0.9220,0.8205,0.7305,0.6502,0.5950,0.5545,0.5333,0.5189,0.5181,0.5176,0.5172,0.5119],
    HE_B_VALUES = [0.4245,0.5747,0.6527,0.7223,0.7582,0.7957,0.8279,0.8553,0.8757,0.8903,0.8997,0.9073,0.9122,0.9171,0.9217,0.9267]
);





