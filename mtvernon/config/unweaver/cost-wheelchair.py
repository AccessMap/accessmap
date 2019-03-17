"""Defines cost function generators for optimal path finding."""
import math

## Default base moving speeds for different modes. All in m/s.
# Slightly lower than average walking speed
WALK_BASE = 1.3
# Rough estimate
WHEELCHAIR_BASE = 0.6
# Roughly 5 mph
POWERED_BASE = 2

# 1 / DIVISOR = speed where cutoff starts to apply, dictates exponential"s k.
DIVISOR = 5

# "fastest" incline. -0.0087 is straight from Tobler"s hiking function
INCLINE_IDEAL = -0.0087


def find_k(g, m, n):
    return math.log(n) / abs(g - m)


def tobler(grade, k=3.5, m=INCLINE_IDEAL, base=WALK_BASE):
    # Modified to be in meters / second rather than km / h
    return base * math.exp(-k * abs(grade - m))

def cost_fun_generator(base_speed=WALK_BASE, downhill=0.1,
                       uphill=0.085):
    """Calculates a cost-to-travel that balances distance vs. steepness vs.
    needing to cross the street.

    :param downhill: Maximum downhill incline indicated by the user, e.g.
                     0.1 for 10% downhill.
    :type downhill: float
    :param uphill: Positive incline (uphill) maximum, as grade.
    :type uphill: float

    """
    k_down = find_k(-downhill, INCLINE_IDEAL, DIVISOR)
    k_up = find_k(uphill, INCLINE_IDEAL, DIVISOR)

    def cost_fun(u, v, d):
        """Cost function that evaluates every edge, returning either a nonnegative cost
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

        """
        time = 0
        speed = base_speed

        length = d["length"]
        subclass = d["subclass"]

        if subclass == "footway":
            if "footway" in d:
                if d["footway"] == "sidewalk":
                    # FIXME: this data should be float to begin with
                    incline = float(d["incline"])
                    # Decrease speed based on incline
                    if length > 3:
                        if incline > uphill:
                            return None
                        if incline < -downhill:
                            return None
                    if incline > INCLINE_IDEAL:
                        speed = tobler(incline, k=k_up, m=INCLINE_IDEAL, base=base_speed)
                    else:
                        speed = tobler(incline, k=k_down, m=INCLINE_IDEAL, base=base_speed)
                else:
                    speed = base_speed

                if d["footway"] == "crossing":
                    # Add delay for crossing street
                    time += 30
        else:
            # Unknown path type
            return None

        # Initial time estimate (in seconds) - based on speed
        time = length / speed

        # Return time estimate - this is currently the cost
        return time

    return cost_fun
