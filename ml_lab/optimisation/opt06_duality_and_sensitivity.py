#!/usr/bin/env python3
"""OPT 06 - LP duality and sensitivity: what is one more driver, or one more request, worth?

ATLAS link: the driver repositioning LP of OPT 05. Every LP has a dual whose variables are prices:
the marginal value of each zone's drivers and the marginal cost of each place's demand. HiGHS returns
them with the solution; we verify them by re-solving with one unit changed.
Applies to: pricing, capacity investment decisions, economics (shadow prices), column generation.
Exercise: check complementary slackness - a zone with idle drivers left over must have price zero.
"""

from common import note, run, show, table
from opt05_linear_programming_transport import problem, solve
from atlas_go.domain import PLACES


def main():
    zones, supply, demand, D = problem()
    res = solve(supply, demand, D)
    y_supply = res.ineqlin.marginals                 # d(cost)/d(supply_i) <= 0
    y_demand = res.eqlin.marginals                   # d(cost)/d(demand_j)
    dual_value = y_supply @ supply + y_demand @ demand
    show('primal optimum (km)', f'{res.fun:.4f}')
    show('dual optimum (km)', f'{dual_value:.4f}  (strong duality: equal)')
    used = res.x.reshape(D.shape).sum(1)
    rows = []
    for i, z in enumerate(zones):
        s2 = supply.copy()
        s2[i] += 1
        rows.append((z, supply[i], f'{used[i]:.0f}', f'{y_supply[i] + 0.0:+.3f}', f'{solve(s2, demand, D).fun - res.fun:+.3f}'))
    table(['zone', 'idle', 'sent', 'shadow price (km)', 're-solve with +1 driver'], rows)
    rows = []
    for j, p in enumerate(PLACES):
        d2 = demand.copy()
        d2[j] += 1
        rows.append((p, demand[j], f'{y_demand[j]:+.3f}', f'{solve(supply, d2, D).fun - res.fun:+.3f}'))
    table(['place', 'demand', 'marginal cost (km)', 're-solve with +1 request'], rows)
    note('Dual prices answer "what if" questions without re-solving: a negative zone price is how many km')
    note('one more idle driver there would save; zones with drivers left over are worth zero (slack).')
    note('Demand prices say what one more request costs to cover at each place (City Centre is dearest) -')
    note('the basis for surge pricing. Prices hold only for small changes: past a breakpoint the optimal')
    note('plan (the basis) changes and the prices with it.')


if __name__ == '__main__':
    run(main, __doc__)
