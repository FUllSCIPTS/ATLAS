#!/usr/bin/env python3
"""ML 13 - Density-based clustering (DBSCAN) on a map: where do ride requests bunch up in Cork?

ATLAS link: Cork geography from ATLAS Go (atlas_go/geo.py: the four saved places and the driver zones).
We simulate a day of pickup requests around them, then let DBSCAN find hotspots with the haversine
(great-circle) distance - no number of clusters given, and stray requests labelled as noise.
Applies to: crime and accident hotspots, GPS trajectory stops, fraud rings, any clusters of odd shape.
Exercise: set eps to 50 m and to 1 km and explain what changes.
"""
import numpy as np
from sklearn.cluster import DBSCAN, KMeans

from common import note, run, show, table
from atlas_go.domain import PLACES
from atlas_go.geo import PLACE_COORDS, ZONE_COORDS, haversine_km

EARTH_KM = 6371.0


def main():
    rng = np.random.default_rng(13)
    centres = list(PLACE_COORDS) + [ZONE_COORDS['Douglas'], ZONE_COORDS['Blackpool']]
    names = list(PLACES) + ['Douglas', 'Blackpool']
    sizes = [220, 300, 160, 120, 60, 40]
    spread_km = [0.15, 0.2, 0.15, 0.15, 0.25, 0.25]
    pts, truth = [], []
    for k, ((lat, lon), n, s) in enumerate(zip(centres, sizes, spread_km)):
        d = rng.normal(0, s, (n, 2)) / 111.0
        pts.append(np.c_[lat + d[:, 0], lon + d[:, 1] / np.cos(np.radians(lat))])
        truth += [k] * n
    lat0, lon0 = 51.896, -8.47
    noise = np.c_[rng.uniform(lat0 - 0.06, lat0 + 0.03, 80), rng.uniform(lon0 - 0.06, lon0 + 0.05, 80)]
    P = np.vstack(pts + [noise])
    truth = np.array(truth + [-1] * 80)

    eps_km = 0.2
    db = DBSCAN(eps=eps_km / EARTH_KM, min_samples=12, metric='haversine', algorithm='ball_tree').fit(np.radians(P))
    labels = db.labels_
    show('DBSCAN (eps 200 m, 12 requests)', f'{labels.max() + 1} hotspots, {(labels == -1).sum()} requests marked noise '
         f'({(truth == -1).sum()} were scattered)')
    rows = []
    for j in range(labels.max() + 1):
        m = P[labels == j]
        c = m.mean(0)
        nearest = min(range(len(centres)), key=lambda k: haversine_km(c, centres[k]))
        rows.append((j, len(m), f'{c[0]:.4f}, {c[1]:.4f}', names[nearest], f'{haversine_km(c, centres[nearest]) * 1000:.0f} m'))
    table(['hotspot', 'requests', 'centre (lat, lon)', 'nearest landmark', 'offset'], rows)
    km = KMeans(6, n_init=5, random_state=0).fit(P)
    show('k-means with k=6 on the same points', f'every stray request forced into a cluster; sizes '
         f'{sorted(np.bincount(km.labels_).tolist(), reverse=True)}')
    show('haversine check UCC -> Kent Station', f'{haversine_km(PLACE_COORDS[0], PLACE_COORDS[2]):.2f} km')
    note('DBSCAN grows clusters from dense cores, so it needs a distance scale (eps) and a minimum crowd,')
    note('not a cluster count, and it can say "noise". It also chains: the City Centre and Kent Station')
    note(f'crowds ({haversine_km(PLACE_COORDS[1], PLACE_COORDS[2]):.1f} km apart) merge through a bridge of requests. Latitude/longitude are angles:')
    note('use haversine or project to metres - a degree of longitude in Cork is ~69 km, of latitude ~111 km.')

if __name__ == '__main__':
    run(main, __doc__)
