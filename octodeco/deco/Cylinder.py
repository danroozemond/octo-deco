# Please see LICENSE.md

from octodeco.deco import Gas;


class Cylinder:
    def __init__(self, name, size_L, max_pressure_bar):
        assert size_L > 0.0;
        assert max_pressure_bar > 0.0;
        self.name = name;
        self.size_L = size_L;
        self.max_pressure_bar = max_pressure_bar;
        self.contains_L = size_L * max_pressure_bar;

    def liters_to_bars(self, liters):
        return liters/self.contains_L;

    def liters_used_to_perc(self, liters):
        return 100.0 * self.liters_to_bars( liters ) / self.max_pressure_bar;

    def __repr__(self):
        return '{}[{}L, {}bar]'.format(self.name, self.size_L, self.max_pressure_bar);

    def __str__(self):
        return self.name;


def Guess(liters_used, gas):
    if gas['fO2'] > 0.82:
        return Cylinder('cf40', 5.55, 200.0);
    if gas['fO2'] > 0.52:
        return Cylinder('Alu7', 7.0, 200.0);
    if gas['fO2'] > 0.42:
        return Cylinder('cf80', 11.1, 200.0);
    if liters_used < 1500:
        return Cylinder('cf80', 11.1, 200.0);
    return Cylinder('D12', 24, 200.0);
