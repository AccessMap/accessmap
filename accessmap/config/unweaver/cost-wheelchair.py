"""Defines cost function generators for optimal path finding."""
import math
import humanized_opening_hours as hoh
import pytz

## Default base moving speeds for different modes. All in m/s.
# Slightly lower than average walking speed
WALK_BASE = 1.3
# Rough estimate
WHEELCHAIR_BASE = 0.6
# Roughly 5 mph
POWERED_BASE = 2

def cost_fun_generator(base_speed=WALK_BASE,
                       downhill=0.1,
                       uphill=0.085,
                       avoidCurbs=True,
                       timestamp=None,
                       tactilePaving=False,
                       landmark=0.2,
                       steps=0.5,
                       crossing=0.8):

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
        landmark_count = d["count_sum"]
        subclass = d["subclass"]

        cost = length

        if subclass == "cycleway":
            return None
        if subclass == "steps":
            if steps == 1:
                return None
            else:
                # when steps is 0, cost is unchanged
                # as steps goes to 1, cost should increase
                cost = (math.e ** (steps * 1.5)) * length
                # speed = 0.8 * base_speed + ((math.e ** (1 - steps)) - 1)
        if length > 3:
            # when landmark is 0, cost is unchanged
            # as landmark goes to 1, cost decreases
            cost = length / (math.e ** (landmark * landmark_count))
            # speed = base_speed + ((math.e ** (landmark * landmark_count)) - 1)
        if "footway" in d:
            if d["footway"] == "crossing":
                if tactilePaving:
                    if "tactile_paving" in d:
                        if not d["tactile_paving"]:
                            return None
                if avoidCurbs:
                    if "curbramps" in d:
                        if not d["curbramps"]:
                            return None
                else:
                    # when crossing is 0, cost is unchanged
                    # as crossing goes to 1, cost of uncontrolled increases and cost of controlled decreases
                    # original cost is x2 to disincentivize crossings as a whole
                    if "traffic_signals" in d:
                        if d["traffic_signals"] == "traffic_lights":
                            cost = (2 * length) / (math.e ** (crossing * 2))
                        elif d["traffic_signals"] == "stop_sign":
                            cost = ((2 + (crossing * 1.5))  * length) / (math.e ** (crossing * 0.7))
                        elif d["traffic_signals"] == "pedestrian_sign":
                            cost = ((2 + (crossing * 2)) * length) / (math.e ** (crossing * 0.3))
                    else:
                        if d["crossing"] == "marked":
                            cost = ((2 + (crossing * 2.5)) * length) / (math.e ** (crossing * 0.1))
                        else:
                            cost = ((2 + (crossing * 3)) * length) / (math.e ** (crossing * 0.05))
        
        return cost

    return cost_fun