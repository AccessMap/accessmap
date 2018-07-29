'''Defines cost function generators for optimal path finding.'''
from datetime import datetime
import math
import humanized_opening_hours as hoh
import pytz

# Default base moving speeds for different modes. All in m/s.
WALK_BASE = 1.3  # Slightly lower than average walking speed
WHEELCHAIR_BASE = 0.6  # Rough estimate
POWERED_BASE = 2  # Roughly 5 mph

# 1 / DIVISOR = speed where cutoff starts to apply, dictates exponential's k.
DIVISOR = 5

# 'fastest' incline. -0.0087 is straight from Tobler's hiking function
INCLINE_IDEAL = -0.0087


def find_k(g, m, n):
    return math.log(n) / abs(g - m)


def tobler(grade, k=3.5, m=INCLINE_IDEAL, base=WALK_BASE):
    # Modified to be in meters / second rather than km / h
    return base * math.exp(-k * abs(grade - m))


def cost_fun_generator(base_speed=WALK_BASE, incline_min=-0.1,
                       incline_max=0.085, avoid_curbs=True, timestamp=None):
    '''Calculates a cost-to-travel that balances distance vs. steepness vs.
    needing to cross the street.

    :param incline_min: Maximum downhill incline indicated by the user, e.g.
                        -0.1 for 10% downhill.
    :type incline_min: float
    :param incline_max: Positive incline (uphill) maximum, as grade.
    :type incline_max: float
    :param avoid_curbs: Whether curb ramps should be avoided.
    :type avoid_curbs: bool

    '''
    k_up = find_k(incline_max, INCLINE_IDEAL, DIVISOR)
    k_down = find_k(incline_min, INCLINE_IDEAL, DIVISOR)

    if timestamp is None:
        date = datetime.now(pytz.timezone('US/Pacific'))
    else:
        date = datetime.fromtimestamp(timestamp, pytz.timezone('US/Pacific'))

    def cost_fun(u, v, d):
        '''Cost function that evaluates every edge, returning either a nonnegative cost
        or None. Returning a value of None implies an infinite cost, i.e. that edge
        will be excluded from any paths.

        :param u: incoming node ID
        :type u: int
        :param v: ougoing node ID
        :type v: int
        :param d: The edge to evaluate.
        :type d: dict
        :returns: Cost of traversing the edge
        :rtype: float or None

        '''
        # MultiDigraph may have multiple edges. Right now, we ignore this
        # and just pick the first edge. A simple DiGraph may be more
        # appropriate?

        # Set up initial costs - these should start at 0, and be max of 1 or
        # None.

        # Note: returning a 'None' cost implies an impassible edge, i.e. infinite cost
        time = 0

        way = d['way']

        # Initial speed based on incline
        # NOTE: Inclines were initially multiplied by 1000 to save on filesize
        if way == 'sidewalk':
            incline = d['incline'] / 1000.
        else:
            # Assume all other paths are flat (due to lack of info)
            # TODO: instead, just do a check on whether there is an incline key
            incline = 0

        if 'opening_hours' in d:
            # There might be a time restriction
            # TODO: this should be validated during graph creation/update
            try:
                oh = hoh.OHParser(d['opening_hours'])
                if not oh.is_open(date):
                    return None
            except:
                # Failed to parse or something: don't use this path
                return None

        if incline > incline_max:
            return None
        if incline < incline_min:
            return None

        # Speed based on incline
        if not incline:
            speed = base_speed
        elif incline > INCLINE_IDEAL:
            speed = tobler(incline, k=k_up, m=INCLINE_IDEAL, base=base_speed)
        else:
            speed = tobler(incline, k=k_down, m=INCLINE_IDEAL, base=base_speed)

        # Initial time estimate (in seconds) - based on speed
        time = d['length'] / speed

        if way == 'crossing':
            # Crossings imply a delay. Would be good to make this driven by
            # data, but can guess for now
            time += 30
        elif way == 'elevator_path':
            # Include a delay for using the elevator - takes time to enter/exit
            # a building and wait for + use the elevator
            time += 45

        # Curb cost
        if avoid_curbs:
            if (way == 'crossing') and d['curbramps'] == 0:
                # A hard barrier - exit early with infinite cost
                return None

        # Return time estimate - this is currently the cost
        return time

    return cost_fun
