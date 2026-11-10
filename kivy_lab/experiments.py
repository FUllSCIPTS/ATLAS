"""Kivy front-end laboratory: 11 experiments that each exercise one lesson of
docs/WEB_TECHNOLOGY_2.md, using real Kivy and, where possible, the real ATLAS Go code.

Every lab returns a table of OBSERVED values produced by running Kivy, plus a
chart that shows the lesson's idea. Nothing is estimated or invented.

    python kivy_lab/experiments.py                  # self-tests, then usage
    python kivy_lab/experiments.py --all            # K01-K11 -> kivy_lab/results
    python kivy_lab/experiments.py --experiment 6   # one lab
    python kivy_lab/experiments.py --list

Kivy needs a display. On a desktop just run the commands above. On a headless
Linux machine (a server, CI, a container) wrap them in a virtual display:

    xvfb-run -a python kivy_lab/experiments.py --all

Needs: kivy==2.3.1 (the version ATLAS Go ships) and matplotlib.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "android-app"

# Kivy reads these before it starts: no command-line parsing, plain Python logging,
# app data in a throw-away folder, and a tile URL that fails fast (no network use).
os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_LOG_MODE", "PYTHON")
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")
os.environ.setdefault("ATLAS_DATA_DIR", tempfile.mkdtemp(prefix="atlas-kivy-lab-"))
os.environ.setdefault("ATLAS_TILE_URL", "http://127.0.0.1:9/{z}/{x}/{y}.png")
sys.path.insert(0, str(APP_DIR))

from kivy.base import EventLoop                          # noqa: E402  (after the environment)
from kivy.clock import Clock                             # noqa: E402
from kivy.core.text import Label as CoreLabel            # noqa: E402
from kivy.core.window import Window                      # noqa: E402
from kivy.graphics import Color, Rectangle               # noqa: E402
from kivy.metrics import Metrics, dp, sp                 # noqa: E402
from kivy.tests.common import UnitTestTouch              # noqa: E402
from kivy.uix.boxlayout import BoxLayout                 # noqa: E402
from kivy.uix.button import Button                       # noqa: E402
from kivy.uix.label import Label                         # noqa: E402
from kivy.uix.widget import Widget                       # noqa: E402

TITLES = {
    1: "App lifecycle: the order Kivy calls your methods",
    2: "Widget tree size and rebuild time of real ATLAS Go screens",
    3: "BoxLayout: fixed heights versus size_hint as the parent grows",
    4: "dp and sp: the same 48 dp button on phones of different density",
    5: "Wrapping text: label height with and without the text_size binding",
    6: "Closures in loops: which screen each navigation button opens",
    7: "Canvas instructions: redrawing with and without canvas.clear()",
    8: "Text textures: creating them every time versus caching them",
    9: "Coalescing redraws with Clock.schedule_once",
    10: "Touch: dragging the real LiveMap pans by exactly the finger distance",
    11: "Threads and the UI: handing results to the main loop with Clock",
}


def result(number, title, kind, labels, rows, xlabel, ylabel, notes="", log=False):
    """kind: 'line' (x + series), 'bar' (category + series) or 'heatmap' (row label + cells)."""
    return {"number": number, "title": title, "kind": kind, "labels": list(labels), "rows": rows,
            "xlabel": xlabel, "ylabel": ylabel, "notes": notes, "log": log}


def frame(n=1):
    """Let Kivy run n frames: layouts settle, scheduled callbacks run."""
    for _ in range(n):
        EventLoop.idle()


def mount(widget, size=(440, 940)):
    """Show a widget as the only thing in the window, at a phone-like size."""
    Window.size = size
    for child in list(Window.children):
        Window.remove_widget(child)
    Window.add_widget(widget)
    frame(3)
    return widget


EventLoop.ensure_window()


# ----------------------------------------------------------------------------- K01
LIFECYCLE_PROGRAM = r'''
import os
os.environ["KIVY_NO_ARGS"] = "1"; os.environ["KIVY_LOG_MODE"] = "PYTHON"; os.environ["KIVY_NO_CONSOLELOG"] = "1"
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
calls = []
class Probe(App):
    def build(self):
        calls.append("build"); return Label(text="probe")
    def on_start(self):
        calls.append("on_start")
        Clock.schedule_once(lambda dt: calls.append("first frame"), 0)
        Clock.schedule_once(lambda dt: self.stop(), 0.2)
    def on_stop(self):
        calls.append("on_stop")
calls.append("before run()")
Probe().run()
calls.append("after run()")
print(",".join(calls))
'''


def lab_01():
    """Run a tiny App in a child process and record the order of the calls."""
    with tempfile.TemporaryDirectory() as folder:
        script = Path(folder) / "probe.py"           # App looks for a .kv file next to its source file
        script.write_text(LIFECYCLE_PROGRAM, encoding="utf-8")
        out = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                             timeout=120, env=os.environ.copy())
    if out.returncode:
        raise RuntimeError(out.stderr[-2000:])
    order = out.stdout.strip().splitlines()[-1].split(",")
    assert order[:4] == ["before run()", "build", "on_start", "first frame"], order
    assert order[-1] == "after run()" and set(order[4:-1]) == {"on_stop"}, order
    rows = [[name, step] for step, name in enumerate(order, 1)]
    return result(1, TITLES[1], "bar", ["step"], rows, "call", "step number",
                  "build runs before the window shows anything; on_start after the root widget is attached; "
                  "scheduled callbacks run on later frames; run() only returns after on_stop. In Kivy 2.3.1 an app that "
                  "calls self.stop() receives on_stop twice, so on_stop must be safe to repeat.")


# ----------------------------------------------------------------------------- K02
SIGNED_OUT = ("welcome", "login", "register", "privacy")
GUEST = ("home", "ride", "share", "food", "map", "activity", "profile", "intelligence")


def lab_02(repeats=5):
    """Render each real ATLAS Go screen several times; count widgets and time render()."""
    from atlas_go.app import AtlasGoApp
    app = AtlasGoApp()
    root = mount(app.build())
    Clock.unschedule(app.live_tick)          # keep the 1-second tick out of the timings
    rows = []
    for screens, guest in ((SIGNED_OUT, False), (GUEST, True)):
        if guest:
            app.store.continue_as_guest()
        for screen in screens:
            times = []
            for _ in range(repeats + 1):     # the first render warms caches; it is discarded
                app.screen = screen
                start = time.perf_counter()
                app.render()
                times.append((time.perf_counter() - start) * 1000)
                frame()
            assert app.screen == screen, (screen, app.screen)
            rows.append([screen, sum(1 for _ in root.walk()), round(statistics.median(times[1:]), 2)])
    if app.live_map is not None:
        app.live_map.detach()
    return result(2, TITLES[2], "bar", ["widgets in the tree", "median render() ms"], rows, "screen", "count / ms",
                  "render() throws the whole screen away and builds it again. Cost grows with the number of widgets; "
                  "the Intelligence screen, with its charts and learning lab, is the largest.")


# ----------------------------------------------------------------------------- K03
def lab_03():
    """A 48 dp header, a body with size_hint_y=1 and a footer with size_hint_y=0.25."""
    root = BoxLayout(orientation="vertical")
    header = Widget(size_hint_y=None, height=dp(48))
    body = Widget(size_hint_y=1)
    footer = Widget(size_hint_y=0.25)
    for w in (header, body, footer):
        root.add_widget(w)
    rows = []
    for height in (300, 400, 500, 600, 700, 800, 900):
        mount(root, (440, height))
        rows.append([height, round(header.height), round(body.height), round(footer.height)])
        free = height - dp(48)
        assert abs(header.height - dp(48)) < 1 and abs(body.height - free / 1.25) < 1, rows[-1]
    return result(3, TITLES[3], "line", ["header (fixed)", "body (hint 1)", "footer (hint 0.25)"], rows,
                  "window height (px)", "child height (px)",
                  "A fixed child keeps its height; hinted children share what is left in proportion 1 : 0.25.")


# ----------------------------------------------------------------------------- K04
def lab_04():
    """dp(48) and sp(14) at the density and font scale of real Android buckets."""
    saved = Metrics.density, Metrics.fontscale
    rows = []
    try:
        for name, density in (("mdpi", 1.0), ("hdpi", 1.5), ("xhdpi", 2.0), ("xxhdpi", 3.0), ("xxxhdpi", 4.0)):
            Metrics.density, Metrics.fontscale = density, 1.0
            rows.append([name, 48, round(dp(48), 1), round(sp(14), 1)])
        Metrics.density, Metrics.fontscale = 3.0, 1.3        # "large text" in Android settings
        rows.append(["xxhdpi + large text", 48, round(dp(48), 1), round(sp(14), 1)])
    finally:
        Metrics.density, Metrics.fontscale = saved
    assert rows[3][2] == 144 and rows[5][2] == 144 and rows[5][3] > rows[3][3]
    return result(4, TITLES[4], "bar", ["plain pixels", "dp(48) in pixels", "sp(14) in pixels"], rows,
                  "screen density", "pixels",
                  "A plain 48 would shrink to a quarter of its physical size on an xxxhdpi phone; dp keeps the button the "
                  "same size under the finger. sp also follows the user's font-size setting, dp does not.")


# ----------------------------------------------------------------------------- K05
def wrapped_label(text, bound):
    """The ATLAS Go label recipe (AtlasGoApp.label) with the width binding switched on or off."""
    item = Label(text=text, font_size=sp(15), size_hint_y=None, halign="left", valign="middle")
    if bound:
        item.bind(width=lambda widget, value: setattr(widget, "text_size", (value, None)))
    item.bind(texture_size=lambda widget, value: setattr(widget, "height", value[1] + dp(3)))
    return item


def lab_05():
    sentence = "Rides, shared journeys and local food, with ATLAS intelligence on your phone. "
    rows = []
    for n in (1, 2, 3, 4, 6, 8):
        text = sentence * n
        widths = {}
        for bound in (False, True):
            box = BoxLayout(orientation="vertical", padding=dp(21))
            label = wrapped_label(text.strip(), bound)
            box.add_widget(label)
            box.add_widget(Widget())
            mount(box)
            widths[bound] = (round(label.height), round(label.texture_size[0]))
        rows.append([len(text.strip()), widths[False][0], widths[True][0], widths[False][1]])
    assert all(r[3] > 400 for r in rows) and rows[-1][2] > 4 * rows[0][2]
    return result(5, TITLES[5], "line", ["height, no binding", "height, text_size bound to width",
                                         "text width, no binding"], rows, "characters", "pixels",
                  "Without text_size the text is one long line that runs off the 398 px column (its width grows with "
                  "the text). Binding text_size to the width wraps it, and the height binding makes the label grow.")


# ----------------------------------------------------------------------------- K06
def lab_06():
    keys = ("home", "map", "food", "activity", "profile")
    opened = {"late binding": [], "default argument": []}
    for style in opened:
        row = BoxLayout()
        for key in keys:
            if style == "late binding":
                callback = lambda: opened[style].append(key)                 # noqa: E731  (the bug)
            else:
                callback = lambda key=key: opened[style].append(key)         # noqa: E731  (ATLAS Go's fix)
            button = Button(text=key)
            button.bind(on_release=lambda _w, cb=callback: cb())
            row.add_widget(button)
        mount(row)
        for button in row.children[::-1]:
            button.trigger_action(duration=0)
    rows = [[style] + [keys.index(name) for name in opened[style]] for style in opened]
    assert opened["late binding"] == ["profile"] * 5 and opened["default argument"] == list(keys)
    return result(6, TITLES[6], "heatmap", [f"button {i + 1} ({k})" for i, k in enumerate(keys)], rows,
                  "button pressed", "lambda style",
                  "Cells show the index of the screen that opened (0 home … 4 profile). With late binding every button "
                  "opens the last key of the loop; `lambda key=key:` captures each value when the button is made.")


# ----------------------------------------------------------------------------- K07
def count_instructions(widget):
    return len(widget.canvas.children)


class LeakyRouteMap(Widget):
    """RouteMap's drawing code without the canvas.clear() at the top."""

    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(135), **kwargs)
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        with self.canvas:
            Color(0.9, 0.93, 0.86, 1)
            Rectangle(pos=self.pos, size=self.size)
            for i in range(6):
                Color(0.84, 0.89, 0.78, 1)
                Rectangle(pos=(self.x + i * self.width / 6, self.y), size=(self.width * .09, self.height))


def lab_07():
    from atlas_go.app import RouteMap
    real, leaky = RouteMap(), LeakyRouteMap()
    box = BoxLayout(orientation="vertical")
    box.add_widget(real)
    box.add_widget(leaky)
    box.add_widget(Widget())
    rows = []
    for resize in range(0, 11):
        mount(box, (360 + 8 * resize, 780))
        rows.append([resize, count_instructions(real), count_instructions(leaky)])
    assert len({r[1] for r in rows}) == 1 and rows[-1][2] > 5 * rows[0][2]
    return result(7, TITLES[7], "line", ["RouteMap (clears first)", "same drawing, no clear()"], rows,
                  "window resizes", "instructions on the canvas",
                  "Every draw adds instructions. RouteMap starts with canvas.clear(), so the count stays flat; "
                  "without it the canvas keeps every old frame, drawn underneath, and grows on each resize.")


# ----------------------------------------------------------------------------- K08
def lab_08(labels=200):
    from atlas_go import livemap
    names = [f"Driver {i % 25} · online" for i in range(labels)]   # map labels repeat a lot
    start = time.perf_counter()
    for name in names:
        label = CoreLabel(text=name, font_size=sp(10))
        label.refresh()
    fresh = (time.perf_counter() - start) * 1000
    livemap._LABELS.clear()
    start = time.perf_counter()
    for name in names:
        livemap.text_texture(name, 10)
    cached = (time.perf_counter() - start) * 1000
    rows = [["new CoreLabel every time", round(fresh, 2), labels],
            ["livemap.text_texture (cached)", round(cached, 2), len(livemap._LABELS)]]
    assert len(livemap._LABELS) == 25 and cached < fresh
    return result(8, TITLES[8], "bar", ["ms for 200 labels", "textures rendered"], rows, "approach", "ms / count",
                  "Turning text into a texture is the expensive step. The map draws the same labels every frame, so "
                  "text_texture keeps a dict of textures keyed by (text, size, colour, bold) and renders each once.")


# ----------------------------------------------------------------------------- K09
class Counted(Widget):
    def __init__(self, coalesce, **kwargs):
        super().__init__(**kwargs)
        self.coalesce, self.draws, self._event = coalesce, 0, None

    def request(self, *_):
        if not self.coalesce:
            self.draw()
        elif self._event is None:                       # the LiveMap._schedule pattern
            self._event = Clock.schedule_once(self.draw, 0)

    def draw(self, *_):
        self._event = None
        self.draws += 1


def lab_09():
    rows = []
    for changes in (1, 5, 10, 25, 50, 100):
        counts = []
        for coalesce in (False, True):
            widget = Counted(coalesce)
            for _ in range(changes):                    # e.g. markers, routes, accuracy, zoom all set at once
                widget.request()
            frame(2)
            counts.append(widget.draws)
        rows.append([changes] + counts)
    assert all(r[1] == r[0] and r[2] == 1 for r in rows)
    return result(9, TITLES[9], "line", ["draw on every change", "coalesced (one per frame)"], rows,
                  "changes in one frame", "draws", log=True,
                  notes="LiveMap._schedule books at most one draw for the next frame, however many changes arrive.")


# ----------------------------------------------------------------------------- K10
class _NoTiles:
    """Stands in for TileLoader: no network, every tile 'not loaded yet'."""
    offline = True

    def __init__(self):
        self.listeners = []

    def texture(self, key):
        return None


def drag(widget, start, delta, steps=10):
    touch = UnitTestTouch(*start)
    touch.touch_down()
    for i in range(1, steps + 1):
        touch.touch_move(start[0] + delta[0] * i / steps, start[1] + delta[1] * i / steps)
    touch.touch_up()


def lab_10():
    from atlas_go import geo, livemap
    rows = []
    for zoom in (12, 13, 14, 15, 16):
        live = livemap.LiveMap(zoom=zoom, interactive=True, tile_loader=_NoTiles())
        mount(live, (440, 700))
        start = live.to_screen(live.center_point)
        before = live.center_point
        drag(live, (220, 350), (100, -60))
        frame()
        after_x, after_y = live.to_screen(before)        # where the old centre is drawn now
        rows.append([zoom, round(after_x - start[0], 2), round(after_y - start[1], 2),
                     round(geo.haversine_km(before, live.center_point) * 1000)])
        live.detach()
    assert all(abs(r[1] - 100) < .5 and abs(r[2] + 60) < .5 for r in rows)
    assert rows[0][3] > 8 * rows[-1][3]
    return result(10, TITLES[10], "line", ["map moved x (px)", "map moved y (px)", "ground distance (m)"], rows,
                  "zoom level", "pixels / metres", log=True,
                  notes="The same 100 px right, 60 px down drag moves the map by exactly that on screen at every zoom, "
                        "but the distance on the ground halves with each zoom level (Web Mercator).")


# ----------------------------------------------------------------------------- K11
def lab_11(jobs=40):
    main = threading.get_ident()
    seen = {"direct": [], "clock": []}

    def deliver(kind, job):
        seen[kind].append((job, threading.get_ident() == main))

    def worker(kind, job):
        time.sleep(0.001 * (job % 5))                    # pretend to download a tile
        if kind == "direct":
            deliver(kind, job)                           # WRONG: touches UI state from the worker thread
        else:
            Clock.schedule_once(lambda _dt: deliver(kind, job), 0)   # TileLoader._work does this

    for kind in seen:
        threads = [threading.Thread(target=worker, args=(kind, j)) for j in range(jobs)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        frame(3)
    rows = [[kind, sum(on_main for _, on_main in seen[kind]), sum(not on_main for _, on_main in seen[kind])]
            for kind in seen]
    assert rows == [["direct", 0, jobs], ["clock", jobs, 0]]
    return result(11, TITLES[11], "bar", ["ran on the main (UI) thread", "ran on a worker thread"], rows,
                  "how the result is delivered", "deliveries",
                  "Kivy widgets and OpenGL textures must only be touched from the main thread. "
                  "Clock.schedule_once moves each result there; the worker threads only fetch bytes.")


LABS = {n: globals()[f"lab_{n:02}"] for n in TITLES}


def experiment(number):
    res = LABS[number]()
    assert res["rows"] and all(len(r) == len(res["labels"]) + 1 for r in res["rows"]), number
    return res


def save_experiment(res, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    ident = f"lab_{res['number']:02}"
    with open(out / f"{ident}.csv", "w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([res["xlabel"]] + res["labels"])
        writer.writerows(res["rows"])
    (out / f"{ident}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    xs = [str(r[0]) for r in res["rows"]]
    if res["kind"] == "line":
        for i, name in enumerate(res["labels"]):
            ax.plot([r[0] for r in res["rows"]], [r[i + 1] for r in res["rows"]], marker="o", label=name)
        ax.legend()
    elif res["kind"] == "bar":
        width = 0.8 / len(res["labels"])
        for i, name in enumerate(res["labels"]):
            ax.bar([j + i * width for j in range(len(xs))], [r[i + 1] for r in res["rows"]], width, label=name)
        ax.set_xticks([j + width * (len(res["labels"]) - 1) / 2 for j in range(len(xs))], xs, rotation=20)
        ax.legend()
    else:
        grid = [r[1:] for r in res["rows"]]
        im = ax.imshow(grid, cmap="viridis", aspect="auto")
        ax.set_yticks(range(len(xs)), xs)
        ax.set_xticks(range(len(res["labels"])), res["labels"], rotation=20)
        for i, row in enumerate(grid):
            for j, v in enumerate(row):
                ax.text(j, i, v, ha="center", va="center", color="white" if v < 2 else "black")
        fig.colorbar(im, ax=ax)
    if res["log"]:
        ax.set_yscale("log")
    ax.set_title(f"K{res['number']:02} - {res['title']}", fontsize=10)
    ax.set_xlabel(res["xlabel"])
    ax.set_ylabel(res["ylabel"])
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(out / f"{ident}.png", dpi=150)
    plt.close(fig)
    return out / f"{ident}.png"


def self_test():
    assert len(LABS) == 11
    for n in LABS:
        experiment(n)
    print("All 11 Kivy labs ran and their internal assertions passed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--experiment", type=int, choices=sorted(LABS))
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--output", default="kivy_lab/results")
    args = parser.parse_args()
    if args.list:
        for n, t in TITLES.items():
            print(f"K{n:02}  {t}")
        return
    targets = list(LABS) if args.all else [args.experiment] if args.experiment else []
    if not targets:
        self_test()
        parser.print_help()
        return
    for n in targets:
        res = experiment(n)
        save_experiment(res, args.output)
        print(f"K{n:02}: {res['title']} -> {args.output}")
        for row in res["rows"]:
            print("     ", row)


if __name__ == "__main__":
    main()
