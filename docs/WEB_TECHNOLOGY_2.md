# Kivy Front End with ATLAS Go — an illustrated, standalone course

**Level:** beginner to intermediate. **Plan:** 16 lessons in four parts, 6–8 weeks. **Prerequisite:** the Python basics in [Python Programming](PYTHON_PROGRAMMING.md) Lessons 1–12 (functions, classes, inheritance). **Tools:** Python 3.10+, `pip install kivy==2.3.1 matplotlib` (the Kivy version ATLAS Go ships), a text editor. No Android phone is needed until Lesson 15.

[Lab manual](../kivy_lab/README.md) · [Lab source](../kivy_lab/experiments.py) · [ATLAS Go source](../android-app/atlas_go/) · [ATLAS Go architecture and method catalogue](../android-app/docs/ARCHITECTURE.md#complete-source-method-catalog) · [ATLAS Go UML](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go)

> **Why this course exists.** The ATLAS Go Android app has no HTML, CSS or JavaScript. Every screen, button, chart and the live map is **Python**, drawn by the **Kivy** framework, and packaged for Android by **Buildozer / python-for-android**. The [Web Technology](WEB_TECHNOLOGY.md) course teaches the web front end; this course teaches the front end ATLAS Go actually uses. The Python language itself is taught in [Python Programming](PYTHON_PROGRAMMING.md); here we only teach what Kivy adds.

**How every lesson is built:** *idea* (plain-language explanation and a picture) → *worked example* (a complete program; run it and it checks itself) → *common mistakes* → *ATLAS Go* (where the real app does it, with a link to the file) → *lab* (what the experiment measures and what its chart shows) → *exercises*.

**Running the examples.** Every `python` block below is a complete program. Save it as a file (for example `k03.py`) and run `python k03.py`: a window opens, the program checks its own result with `assert`, prints a line and closes itself. Delete the line marked `# auto-close` to keep the window open and play with it. On a Linux machine with no screen (a server or CI), prefix the command with `xvfb-run -a`.

~~~mermaid
flowchart LR
 A["Part I · 1–4<br/>app, widgets,<br/>layouts, units"] --> B["Part II · 5–7<br/>properties, events,<br/>input controls"]
 B --> C["Part III · 8–12<br/>canvas, text, Clock,<br/>touch, threads"]
 C --> D["Part IV · 13–16<br/>screens, Android,<br/>packaging, testing"]
~~~

## Where the front end lives in ATLAS Go

~~~mermaid
flowchart TD
 MAIN["main.py<br/>window size, then AtlasGoApp().run()"] --> APP["app.py — AtlasGoApp(App)<br/>render(), screens, box/label/button/field helpers"]
 APP --> W["app.py widgets<br/>Panel · RouteMap · OutlookChart · Bar · LearningCurve"]
 APP --> MAP["livemap.py — LiveMap(StencilView)<br/>canvas drawing, touch, TileLoader threads"]
 APP --> LOC["location.py — DeviceLocation<br/>pyjnius → Android LocationManager"]
 APP --> STORE["store.py — LocalStore<br/>(not front end: the state the screens show)"]
 SPEC["buildozer.spec"] -. packages .-> APK[("Android .apk / .aab")]
~~~

| Lesson | Topic | ATLAS Go code that uses it | Lab |
|---|---|---|---|
| 1 | How a Kivy app starts | [`main.py`](../android-app/main.py), [`AtlasGoApp.build`, `on_start`, `on_pause`, `on_stop`](../android-app/atlas_go/app.py) | K01 lifecycle order |
| 2 | Widgets and the widget tree | [`AtlasGoApp.render`](../android-app/atlas_go/app.py) | K02 real screens: widgets and render time |
| 3 | Layouts and scrolling | [`AtlasGoApp.box`, `row`, `render`](../android-app/atlas_go/app.py) | K03 size_hint |
| 4 | Units, colour and density | [`dp`, `sp`, the colour constants](../android-app/atlas_go/app.py) | K04 dp across densities |
| 5 | Properties and `bind` | [`AtlasGoApp.label`, `Panel`](../android-app/atlas_go/app.py) | K05 wrapping text |
| 6 | Events, callbacks and the Back key | [`button`, `nav_items`, `on_keyboard`](../android-app/atlas_go/app.py) | K06 closures in loops |
| 7 | Text input, choices and dialogs | [`field`, `select`, `message`, `safe`](../android-app/atlas_go/app.py) | — |
| 8 | Drawing on the canvas | [`Panel`, `RouteMap`, `Bar`](../android-app/atlas_go/app.py) | K07 canvas.clear() |
| 9 | Text as textures; charts by hand | [`OutlookChart`, `_text`](../android-app/atlas_go/app.py), [`text_texture`](../android-app/atlas_go/livemap.py) | K08 texture cache |
| 10 | The Clock and the main loop | [`live_tick`, `lab_step`](../android-app/atlas_go/app.py), [`LiveMap._schedule`](../android-app/atlas_go/livemap.py) | K09 coalescing |
| 11 | Touch input | [`LiveMap.on_touch_down/move/up`](../android-app/atlas_go/livemap.py) | K10 map panning |
| 12 | Threads and the UI thread | [`TileLoader`](../android-app/atlas_go/livemap.py) | K11 thread hand-off |
| 13 | Screens as state | [`render`, `go`, `save_ui`](../android-app/atlas_go/app.py) | — |
| 14 | Talking to Android with pyjnius | [`DeviceLocation`](../android-app/atlas_go/location.py), [`configure_system_bars`](../android-app/atlas_go/app.py) | — |
| 15 | Packaging with Buildozer | [`buildozer.spec`](../android-app/buildozer.spec) | — |
| 16 | Testing a Kivy front end | [`acceptance.py`](../android-app/atlas_go/acceptance.py), [`tests/`](../android-app/tests/) | all labs |

---

# Part I — Building blocks

## Lesson 1 — How a Kivy app starts: `App`, `build` and the lifecycle

**Idea.** A Kivy program is a subclass of `kivy.app.App`. You never call your own methods to start it: you call `run()`, and **Kivy calls you back** at fixed moments. `build()` returns the **root widget** — the thing that fills the window. Then Kivy enters its **main loop**: forever, it reads input (touches, keys), runs scheduled callbacks and redraws the screen, about 60 times a second, until the app stops.

~~~mermaid
sequenceDiagram
 participant You as your code
 participant K as Kivy
 You->>K: MyApp().run()
 K->>You: build() → root widget
 K->>You: on_start()
 loop every frame (~60 per second)
  K->>K: input → callbacks → layout → draw
 end
 Note over K: Android: app goes to background
 K->>You: on_pause() → return True to stay alive
 K->>You: on_resume()
 K->>You: on_stop()
 K-->>You: run() returns
~~~

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label

calls = []

class HelloApp(App):
    title = "Hello ATLAS"

    def build(self):                       # 1. make the root widget and return it
        calls.append("build")
        return Label(text="Your city. One app.", font_size=28)

    def on_start(self):                    # 2. the window is up and the root is attached
        calls.append("on_start")
        Clock.schedule_once(self.check, 0.5)

    def on_stop(self):                     # 3. closing: save anything you need here
        calls.append("on_stop")

    def check(self, _dt):
        assert self.root.text == "Your city. One app."   # self.root is what build() returned
        self.stop()                                       # auto-close

HelloApp().run()
print(calls[:2], "…", calls[-1])           # ['build', 'on_start'] … on_stop
assert calls[:2] == ["build", "on_start"] and calls[-1] == "on_stop"
~~~

**Configure before the window exists.** Settings such as the window size must be set with `kivy.config.Config` **before** anything imports `kivy.core.window`, because importing it creates the window. That is why ATLAS Go's entry point looks like this:

~~~text
android-app/main.py
  from kivy.config import Config
  if platform != 'android':                        # desktop preview only
      width, height = os.environ.get('ATLAS_PREVIEW_SIZE','440x940').split('x')
      Config.set('graphics', 'width', width)
      Config.set('graphics', 'height', height)
  from atlas_go.app import AtlasGoApp              # this import creates the window — so it comes last
  AtlasGoApp().run()
~~~

**Common mistakes.** Calling `build()` yourself (Kivy does it). Doing slow work in `build()` — the user stares at a black screen; do it in `on_start` or later with the Clock (Lesson 10). Forgetting that `on_pause` must **return `True`** on Android, or the system kills the app instead of pausing it. Assuming `on_stop` runs once: in Kivy 2.3.1 an app that calls `self.stop()` receives `on_stop` twice (lab K01), so write it to be safe to repeat.

**ATLAS Go:** [`AtlasGoApp.build`](../android-app/atlas_go/app.py) sets `Window.clearcolor`, opens the `LocalStore` in `user_data_dir` (Android) or `~/.atlas-go` (desktop), restores the last screen, creates the root `BoxLayout`, calls `render()` and starts a one-second `live_tick`. `on_start` adjusts the Android system bars; `on_pause` stops GPS, saves the UI state and returns `True`; `on_stop` does the same two safe-to-repeat steps.

**Lab K01** runs a tiny app in a child process and records each callback in order: `before run()`, `build`, `on_start`, `first frame`, `on_stop`, `on_stop`, `after run()`. The chart is a staircase; the flat repeat at the end is the double `on_stop`.

**Exercises.** (1) Add `on_pause` and `on_resume` to the example; on a desktop they never fire — why? (2) Move the `Label` creation into `on_start` and set `self.root` — what does the user see first? (3) Run `python android-app/main.py` with `ATLAS_PREVIEW_SIZE=360x780` and compare with the default 440×940.

## Lesson 2 — Widgets and the widget tree

**Idea.** Everything you see is a **widget**: `Label`, `Button`, `TextInput`, and containers such as `BoxLayout`. Widgets form a **tree**: `parent.add_widget(child)` hangs a child under a parent; `remove_widget` and `clear_widgets` take them off. Kivy draws the tree from the root down and sends touches from the top down (Lesson 11). Every widget has `parent` and `children`; `widget.walk()` visits the whole subtree.

~~~mermaid
flowchart TD
 R["container (BoxLayout, vertical)"] --> H["header (BoxLayout)"]
 R --> S["scroll (ScrollView)"]
 R --> N["nav bar (BoxLayout)"]
 H --> T["Label 'ATLAS Go'"]
 H --> G["Label 'GUEST'"]
 S --> B["body (BoxLayout)"]
 B --> L1["Label (eyebrow)"]
 B --> L2["Label (heading)"]
 B --> P["Panel (card)"]
 P --> BT["Button"]
 N --> NB["5 × Button"]
~~~

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

class TreeApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")
        root.add_widget(Label(text="ATLAS Go"))
        for name in ("Book a ride", "Order food", "Live map"):
            root.add_widget(Button(text=name))
        return root

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        root = self.root
        names = [w.text for w in reversed(root.children)]     # children are stored newest first!
        assert names == ["ATLAS Go", "Book a ride", "Order food", "Live map"]
        assert all(w.parent is root for w in root.children)
        print(len(list(root.walk())), "widgets:", names)      # 5 widgets: [...]
        root.clear_widgets()                                  # throw the screen away …
        root.add_widget(Label(text="Thanks!"))                # … and build a new one
        assert len(root.children) == 1
        self.stop()                                           # auto-close

TreeApp().run()
~~~

**Common mistakes.** Reading `children` as if it were in the order you added them — it is **reversed** (the newest child is `children[0]`). Adding the same widget to two parents (`WidgetException: Cannot add …, it already has a parent`). Keeping references to widgets after `clear_widgets()` and updating them — they are no longer on screen.

**ATLAS Go:** [`AtlasGoApp.render`](../android-app/atlas_go/app.py) builds every screen from scratch: `self.container.clear_widgets()`, then a header row, a `ScrollView` holding `self.body`, the screen's own content (`screens.get(self.screen, self.home)()`) and the navigation bar. It also resets `self.controls`, the dictionary of named buttons and fields used by the tests (Lesson 16).

**Lab K02** opens the **real** ATLAS Go app in a test window, renders twelve screens five times each and records how many widgets each tree has and the median time of `render()`. On the reference machine the Welcome screen has 20 widgets and rebuilds in about 8 ms; the Intelligence screen, with its charts, has 82 widgets and takes about 45 ms. Rebuilding is cheap enough for a phone, which is why ATLAS Go can afford the simple "throw it away and rebuild" design.

**Exercises.** (1) Print the type names of every widget on the Home screen with `walk()`. (2) Insert a widget at the top of a `BoxLayout` with `add_widget(w, index=len(box.children))`. (3) Which screen in K02 has the most widgets per millisecond — and why might charts be slower than buttons?

## Lesson 3 — Layouts: `BoxLayout`, `size_hint`, padding, spacing and scrolling

**Idea.** A **layout** is a widget that positions and sizes its children. ATLAS Go uses one layout almost everywhere: **`BoxLayout`**, which stacks children in a row (`orientation='horizontal'`, the default) or a column (`'vertical'`). Each child says how big it wants to be:

| Child setting | Meaning |
|---|---|
| `size_hint_y=1` (the default) | take a **share** of the free space |
| `size_hint_y=0.25` | take a quarter as much as a child with hint 1 |
| `size_hint_y=None, height=dp(48)` | fixed height: hints are switched off |

`padding` is space **inside** the layout's edge; `spacing` is the gap **between** children. Kivy's y-axis points **up**: `(0, 0)` is the bottom-left corner.

~~~mermaid
flowchart TB
 subgraph Box["BoxLayout (vertical, padding=21, spacing=12)"]
  direction TB
  A["header · size_hint_y=None, height=dp(48)"]
  B["body · size_hint_y=1 — gets 4/5 of what is left"]
  C["footer · size_hint_y=0.25 — gets 1/5 of what is left"]
 end
~~~

**Content that is taller than the screen** goes in a `ScrollView`. Its single child must have `size_hint_y=None` and a height equal to the height of **its** content. A `BoxLayout` publishes that number as `minimum_height`; binding it to `height` makes the column grow as you add children.

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

class LayoutApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")
        self.header = Widget(size_hint_y=None, height=dp(48))      # fixed
        self.scroll = ScrollView(do_scroll_x=False)                 # hint 1: the rest
        self.footer = Widget(size_hint_y=0.25)                      # a quarter of the scroll's share
        self.body = BoxLayout(orientation="vertical", size_hint_y=None,
                              padding=dp(21), spacing=dp(12))
        self.body.bind(minimum_height=self.body.setter("height"))  # grow with the content
        for i in range(20):
            self.body.add_widget(Button(text=f"Ride {i + 1}", size_hint_y=None, height=dp(48)))
        self.scroll.add_widget(self.body)
        for w in (self.header, self.scroll, self.footer):
            root.add_widget(w)
        return root

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        free = self.root.height - dp(48)
        assert abs(self.header.height - dp(48)) < 1
        assert abs(self.scroll.height - free / 1.25) < 1 and abs(self.footer.height - free / 5) < 1
        expected = 20 * dp(48) + 19 * dp(12) + 2 * dp(21)          # buttons + gaps + padding
        assert abs(self.body.height - expected) < 1
        print("body is", round(self.body.height), "px tall inside a",
              round(self.scroll.height), "px scroll view")
        self.stop()                                                  # auto-close

LayoutApp().run()
~~~

**Common mistakes.** Setting `height=` without `size_hint_y=None` — the hint wins and your height is ignored. Putting a `size_hint_y=1` child inside a `ScrollView` — it is exactly as tall as the view, so nothing scrolls. Forgetting `minimum_height` binding — the column stays 100 px tall and children overlap. Expecting the first child at the top of the *coordinates* — y grows upwards, though a vertical `BoxLayout` still lists children top to bottom.

**ATLAS Go:** every card comes from [`AtlasGoApp.box`](../android-app/atlas_go/app.py) — a vertical `Panel` with `size_hint_y=None` and `box.bind(minimum_height=box.setter('height'))`. [`row`](../android-app/atlas_go/app.py) makes a horizontal `BoxLayout` 48 dp tall. [`render`](../android-app/atlas_go/app.py) builds exactly the three-band layout above: a 58 dp header, a `ScrollView(do_scroll_x=False)` with the body, and a 62 dp navigation bar.

**Lab K03** puts a fixed 48 px header, a hint-1 body and a hint-0.25 footer in a window and grows the window from 300 to 900 px. The header line stays flat at 48; the other two grow in a constant 4 : 1 ratio (202 : 50 at 300 px, 682 : 170 at 900 px).

**Exercises.** (1) Change the footer to `size_hint_y=None, height=dp(62)` — which line in K03's chart would go flat? (2) Make a horizontal row of three buttons where the middle one is twice as wide. (3) Remove the `minimum_height` binding in the example and describe what you see.

## Lesson 4 — Units, colour and screen density: `dp`, `sp` and hex colours

**Idea.** Phones have very different **pixel densities**. A 48-pixel button is a comfortable finger target on an old phone and a tiny sliver on a modern one. Kivy's `kivy.metrics` gives density-independent units:

| Function | Means | Use for |
|---|---|---|
| `dp(48)` | 48 *density-independent pixels* = 48 × screen density | sizes, padding, spacing, line widths |
| `sp(14)` | 14 *scale-independent pixels* = dp × the user's font-size setting | `font_size` only |

Colours in Kivy are **four floats from 0 to 1**: `(red, green, blue, alpha)`. `get_color_from_hex('#075E4A')` converts a web-style hex code.

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import Metrics, dp, sp
from kivy.uix.button import Button
from kivy.utils import get_color_from_hex as color

GREEN = color("#075E4A")
LIME = color("#DFFF73")

class UnitsApp(App):
    def build(self):
        Window.clearcolor = color("#F6F7F2")                   # the window's background
        return Button(text="Book", size_hint=(None, None), size=(dp(160), dp(48)),
                      font_size=sp(14), background_normal="",
                      background_color=GREEN, color=LIME)

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        assert [round(c, 3) for c in GREEN] == [0.027, 0.369, 0.29, 1.0]
        print("density", Metrics.density, "→ dp(48) =", dp(48), "px; sp(14) =", sp(14), "px")
        assert dp(48) == 48 * Metrics.density
        self.stop()                                             # auto-close

UnitsApp().run()
~~~

`background_normal=""` matters: by default a Kivy `Button` draws a grey image and **multiplies** your `background_color` by it, so colours look dull. An empty image gives a flat colour.

**Common mistakes.** Plain numbers for sizes (`height=48`) — fine on the desktop, tiny on a phone. `dp` for fonts — ignores users who need large text. Colours as 0–255 (`(7, 94, 74)`) — every channel above 1 is clipped, so you get white. Forgetting `background_normal=''` and wondering why the button is grey.

**ATLAS Go:** [`app.py`](../android-app/atlas_go/app.py) defines its palette once — `GREEN`, `INK`, `MUTED`, `LIME`, `BG`, `WHITE`, `PALE`, `VIOLET`, `LILAC`, `SURGE` — with `get_color_from_hex`, and writes every size as `dp(...)` and every `font_size` as `sp(...)`. Buttons use `background_normal=''` and `background_down=''` for flat Material-style colours.

**Lab K04** sets Kivy's density to Android's buckets (mdpi 1.0 … xxxhdpi 4.0) and records what `dp(48)` and `sp(14)` become: 48 → 192 px, while plain `48` stays 48. With the font scale at 1.3 ("large text"), `sp(14)` grows from 42 to 54.6 px but `dp(48)` does not move.

**Exercises.** (1) Why is 48 dp the usual minimum touch target? (Look up Android's accessibility guidance.) (2) Add `INK` text on `PALE` and check its contrast ratio with the formula in [Web Technology §9.2](WEB_TECHNOLOGY.md#92-contrast-is-arithmetic). (3) Convert `SURGE = '#D9822B'` to floats by hand.

---

# Part II — Making it interactive

## Lesson 5 — Properties and `bind`: widgets that react

**Idea.** A widget's attributes — `text`, `pos`, `size`, `width`, `height`, `texture_size` … — are **Kivy properties**. Unlike plain Python attributes, a property **announces every change**. `widget.bind(width=callback)` asks Kivy to call `callback(widget, new_value)` whenever `width` changes. Layout itself works this way: a parent changes a child's `size`, and everything bound to it follows.

~~~mermaid
flowchart LR
 W["width changes<br/>(layout, rotation)"] -->|"bind(width=…)"| TS["text_size = (width, None)<br/>→ text wraps"]
 TS --> TX["texture_size changes<br/>(the text was re-rendered)"]
 TX -->|"bind(texture_size=…)"| H["height = text height + 3 dp<br/>→ the layout makes room"]
~~~

The most useful recipe in Kivy is **wrapping text**. A `Label` draws its text on one line unless `text_size` gives it a width to wrap in — and the right width is the label's own width, which is only known after layout. So we bind:

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

TEXT = ("Passengers book rides and order food. Drivers go online and accept trips. "
        "Food sellers list their kitchen and menu.")

def wrapping_label(text):
    item = Label(text=text, font_size=sp(15), color=(0.09, 0.18, 0.15, 1),
                 size_hint_y=None, halign="left", valign="middle")
    item.bind(width=lambda widget, value: setattr(widget, "text_size", (value, None)))
    item.bind(texture_size=lambda widget, value: setattr(widget, "height", value[1] + dp(3)))
    return item

class WrapApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical", padding=dp(21))
        self.label = wrapping_label(TEXT)
        root.add_widget(self.label)
        root.add_widget(Widget())                       # filler takes the rest
        return root

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        lines = self.label.texture_size[1] / self.label.font_size
        assert self.label.texture_size[0] <= self.label.width + 1    # the text fits the column
        assert lines > 1.5                                           # … because it wrapped
        print(f"wrapped into about {lines:.0f} lines, label is {self.label.height:.0f} px tall")
        self.stop()                                                  # auto-close

WrapApp().run()
~~~

Two shortcuts: `widget.setter('height')` returns a ready-made callback that sets `height` (used with `minimum_height` in Lesson 3), and `widget.unbind(...)` removes a binding.

**Common mistakes.** Setting `text_size` once in `__init__` — the width is still the default 100 px then. Binding `size` but changing `text_size=size` — the height part stops the label growing and the text is cut off; use `(value, None)`. Infinite loops: a callback for `height` that changes `height` again.

**ATLAS Go:** [`AtlasGoApp.label`](../android-app/atlas_go/app.py) is exactly the recipe above (with `line_height=1.12`); [`button`](../android-app/atlas_go/app.py) binds `width` to `text_size` so long button captions wrap. [`Panel`](../android-app/atlas_go/app.py) binds `pos` and `size` to `_redraw` so its rounded background follows the card (Lesson 8).

**Lab K05** builds the same paragraph 1 to 8 sentences long with and without the `width` binding, in a 398 px column. Without it the label stays 21 px tall and the text is one line up to 4,170 px wide — far off the screen. With it the height grows from 39 to 201 px as the text wraps.

**Exercises.** (1) Make a `Label` whose `font_size` follows the window width (`Window.bind(width=…)`). (2) Explain why `valign` does nothing until `text_size` has a height. (3) Write your own `Property` on a custom widget with `from kivy.properties import NumericProperty` and bind to it.

## Lesson 6 — Events, callbacks and the Android Back key

**Idea.** Users trigger **events**: a `Button` fires `on_press` when touched and `on_release` when the finger lifts (the usual one to use). You attach a function with `bind(on_release=callback)`; Kivy calls `callback(button)`. Keyboard keys arrive on the **window**: `Window.bind(on_keyboard=handler)`. On Android the **Back** key/gesture arrives as key code **27** (Escape) — return `True` if you handled it, or Kivy closes the app.

**The closure trap.** Buttons are often made in a loop. A `lambda` looks up its variables **when it runs**, not when it is made, so every button in the loop sees the loop variable's **last** value. Capture the current value with a default argument: `lambda key=key: …`.

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

SCREENS = ("home", "map", "food", "profile")

class NavApp(App):
    def build(self):
        self.screen = "home"
        root = BoxLayout(orientation="vertical")
        self.title_label = Label(text="home")
        nav = BoxLayout(size_hint_y=0.2)
        self.buttons = {}
        for key in SCREENS:
            button = Button(text=key.title())
            button.bind(on_release=lambda _button, key=key: self.go(key))   # key=key: capture now
            self.buttons[key] = button
            nav.add_widget(button)
        root.add_widget(self.title_label)
        root.add_widget(nav)
        Window.bind(on_keyboard=self.on_keyboard)
        return root

    def go(self, screen):
        self.screen = screen
        self.title_label.text = screen

    def on_keyboard(self, _window, key, *_args):
        if key == 27 and self.screen != "home":    # Back: go home instead of quitting
            self.go("home")
            return True                            # handled — do not close the app
        return False

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        self.buttons["food"].trigger_action(duration=0)          # press it in code
        assert self.title_label.text == "food"
        Window.dispatch("on_keyboard", 27, 0, None, [])          # the Back key
        assert self.screen == "home"
        print("Food button and Back key both work")
        self.stop()                                              # auto-close

NavApp().run()
~~~

**Common mistakes.** `bind(on_release=self.go("map"))` — this *calls* `go` immediately and binds its return value (`None`). Callbacks that forget the widget argument (`lambda: …` raises `TypeError: <lambda>() takes 0 positional arguments but 1 was given`). The late-binding loop above. Returning nothing from the keyboard handler for key 27 — the app quits on Back.

**ATLAS Go:** [`AtlasGoApp.button`](../android-app/atlas_go/app.py) binds `on_release=lambda _widget: self.safe(callback)` so every button's errors are caught (Lesson 7), and the navigation bar in [`render`](../android-app/atlas_go/app.py) uses `lambda key=key: self.go(key)`. [`on_keyboard`](../android-app/atlas_go/app.py) sends Back from Sign-in/Register to Welcome, from any other screen to the role's home, and lets Android close the app only from the home or welcome screen.

**Lab K06** builds five navigation buttons twice — with the late-binding lambda and with `key=key` — presses each and records which screen opened. The heatmap's first row is all 4 (every button opens *profile*); the second row is 0 1 2 3 4.

**Exercises.** (1) Rewrite the button loop with `functools.partial` instead of a default argument. (2) Add `on_press` that changes the button colour and `on_release` that restores it. (3) Draw the decision table of ATLAS Go's `on_keyboard` for the screens *welcome*, *login*, *home*, *map* × signed in / signed out.

## Lesson 7 — Text input, choices and dialogs: `TextInput`, `Spinner`, `Popup`

**Idea.** Forms in Kivy are made from three widgets:

| Widget | Key settings | Event to bind |
|---|---|---|
| `TextInput` | `multiline=False`, `password=True`, `hint_text`, `input_type='number'/'mail'` (chooses the Android keyboard), `write_tab=False` | `text` (every keystroke) |
| `Spinner` (drop-down) | `text` (current choice), `values` (the choices) | `text` |
| `Popup` (modal dialog) | `title`, `content` (any widget), `size_hint`, `auto_dismiss` | `on_dismiss`; call `open()` / `dismiss()` |

A good form never crashes on bad input. Validate in plain Python (it is testable — see [Python Programming Lesson 13](PYTHON_PROGRAMMING.md#lesson-13--exceptions-and-validation)), raise `ValueError` with a friendly message, and let **one** wrapper turn that into a dialog.

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

def parse_seats(text):
    if not text.strip().isdigit():
        raise ValueError("Seats must be a whole number, for example 2.")
    seats = int(text)
    if not 1 <= seats <= 3:
        raise ValueError("Choose 1 to 3 seats.")
    return seats

class FormApp(App):
    def build(self):
        self.form = {}
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8))
        self.seats = TextInput(hint_text="Seats", multiline=False, input_type="number",
                               size_hint_y=None, height=dp(48))
        self.seats.bind(text=lambda _w, value: self.form.__setitem__("seats", value))
        self.place = Spinner(text="UCC", values=("UCC", "Airport", "Kent Station"),
                             size_hint_y=None, height=dp(48))
        self.place.bind(text=lambda _w, value: self.form.__setitem__("place", value))
        book = Button(text="Book", size_hint_y=None, height=dp(48))
        book.bind(on_release=lambda _w: self.safe(self.book))
        for w in (self.seats, self.place, book):
            root.add_widget(w)
        self.popup = None
        return root

    def safe(self, callback):                       # one place turns errors into dialogs
        try:
            callback()
        except ValueError as error:
            self.message("Check your details", str(error))

    def message(self, title, text):
        self.popup = Popup(title=title, content=Label(text=text), size_hint=(0.9, None), height=dp(200))
        self.popup.open()

    def book(self):
        seats = parse_seats(self.form.get("seats", ""))
        self.message("Booked", f"{seats} seat(s) from {self.form.get('place', 'UCC')}")

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        self.seats.text = "lots"                    # as if typed
        self.safe(self.book)
        assert self.popup.title == "Check your details"
        self.popup.dismiss()
        self.seats.text, self.place.text = "2", "Airport"
        self.safe(self.book)
        assert self.popup.content.text == "2 seat(s) from Airport"
        print("bad input → friendly dialog; good input →", self.popup.content.text)
        self.popup.dismiss()
        self.stop()                                 # auto-close

FormApp().run()
~~~

**Common mistakes.** Reading `TextInput.text` only at submit time from a widget that `render()` has since replaced — keep values in a dictionary as they are typed. `multiline=True` (the default) on a single-line field — Enter inserts a newline instead of moving on. Leaving passwords in memory after sign-in. Letting an exception escape a callback — on Android the app simply closes.

**ATLAS Go:** [`AtlasGoApp.field`](../android-app/atlas_go/app.py) creates every `TextInput` and stores each keystroke in `self.form[key]`, so values survive a `render()`. [`select`](../android-app/atlas_go/app.py) wraps a `Spinner` and reports the chosen **index**. [`message`](../android-app/atlas_go/app.py) builds a `Popup` with OK, or Confirm/Cancel, and an optional password box (used before deleting an account). [`safe`](../android-app/atlas_go/app.py) catches `ValueError` and `OSError` from every button and shows *Check your details*. [`submit_login`](../android-app/atlas_go/app.py) removes the password from `self.form` straight after use.

**Exercises.** (1) Add an e-mail field and validate it with ATLAS Go's [`accounts.clean_email`](../android-app/atlas_go/accounts.py). (2) Make the popup's OK button dismiss it. (3) Why does `field` use `input_type='mail'` when the key contains *email*? Try it on a phone.

---

# Part III — Drawing, time and touch

## Lesson 8 — Drawing on the canvas: instructions, `canvas.before` and redrawing

**Idea.** Kivy draws with **OpenGL**. Each widget owns a **canvas**: a list of **graphics instructions** run every frame. *Context* instructions change the state (`Color`); *vertex* instructions draw with it (`Rectangle`, `RoundedRectangle`, `Ellipse`, `Line`). There are three canvases per widget, drawn in this order: `canvas.before` → `canvas` → children → `canvas.after`. A background therefore goes in `canvas.before`.

~~~mermaid
flowchart LR
 C1["Color(green)"] --> R1["RoundedRectangle(pos, size)"] --> C2["Color(white)"] --> L1["Line(points=[x0,y0,x1,y1])"] --> E1["Ellipse(pos, size)"]
~~~

Instructions remember the numbers you gave them. When the widget moves or resizes, you must **update** them (keep a reference and set `pos`/`size`) or **redraw** (`canvas.clear()` and draw again). Both happen in a callback bound to `pos` and `size`.

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as color

class Card(BoxLayout):
    """Pattern 1: keep the instruction and update it (ATLAS Go's Panel)."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*color("#075E4A"))
            self.background = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
        self.bind(pos=self.follow, size=self.follow)

    def follow(self, *_):
        self.background.pos, self.background.size = self.pos, self.size

class Route(Widget):
    """Pattern 2: clear and redraw everything (ATLAS Go's RouteMap)."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        self.canvas.clear()                           # forget the last frame's drawing
        x, y, w, h = self.x, self.y, self.width, self.height
        with self.canvas:
            Color(*color("#DFFF73"))
            Line(points=[x + w * .2, y + h * .2, x + w * .5, y + h * .3, x + w * .8, y + h * .7], width=dp(3))
            for px, py in ((.2, .2), (.8, .7)):
                Ellipse(pos=(x + w * px - dp(9), y + h * py - dp(9)), size=(dp(18), dp(18)))

class CanvasApp(App):
    def build(self):
        self.card = Card(padding=dp(17))
        self.route = Route()
        self.card.add_widget(self.route)
        return self.card

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        before = len(self.route.canvas.children)
        self.route.draw()
        self.route.draw()
        assert len(self.route.canvas.children) == before            # clear() keeps it constant
        assert list(self.card.background.size) == list(self.card.size)
        print("route canvas holds", before, "instructions after every redraw")
        self.stop()                                                  # auto-close

CanvasApp().run()
~~~

**Common mistakes.** Drawing in `__init__` only — at that moment the widget is 100×100 at (0, 0), and it never updates. Redrawing without `canvas.clear()` — old drawings pile up (lab K07). Drawing a background in `canvas` instead of `canvas.before` — it covers the children. Using `Line(dash_length=…)` on Android — ATLAS Go found it is not rendered there and draws dashes as separate segments ([`dashed`](../android-app/atlas_go/app.py)).

**ATLAS Go:** [`Panel`](../android-app/atlas_go/app.py) (pattern 1) gives every card its rounded background. [`RouteMap`](../android-app/atlas_go/app.py) (pattern 2) draws the welcome screen's street illustration: blocks, a river, roads, a green route and two lime-centred pins. [`Bar`](../android-app/atlas_go/app.py) draws a progress bar as two rounded rectangles.

**Lab K07** mounts ATLAS Go's real `RouteMap` next to a copy of its drawing code without `canvas.clear()`, then resizes the window ten times. The real widget keeps 44 instructions; the copy grows 42 → 252, drawing every old frame underneath the new one.

**Exercises.** (1) Add a `canvas.after` border to `Card`. (2) Draw a 5-star rating with `Line(points=…, close=True)`. (3) Read [`Bar.draw`](../android-app/atlas_go/app.py) and explain why it uses `max(dp(6), …)` for the filled width.

## Lesson 9 — Text as textures, and charts drawn by hand

**Idea.** On the canvas there is no "text" instruction. Text is first rendered into a **texture** (an image in GPU memory) by `kivy.core.text.Label` (usually imported as `CoreLabel`), then drawn with a `Rectangle(texture=…)`. Rendering text is the expensive part, so code that draws the same words many times should **cache** the textures.

With rectangles, lines and textures you can draw any chart. The recipe is always: **map data to pixels**, then draw.

~~~mermaid
flowchart LR
 D["data value<br/>(expected requests)"] --> S["scale: value / max × chart height"] --> P["pixel rectangle<br/>(x, base_y, width, height)"]
 T["axis text '06:00'"] --> CL["CoreLabel(...).refresh()"] --> TX["texture"] --> RT["Rectangle(texture=…)"]
~~~

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget

HOURS = [3, 2, 1, 1, 2, 5, 9, 14, 12, 8, 7, 8, 10, 9, 8, 9, 12, 15, 13, 10, 8, 7, 5, 4]
_cache = {}

def text_texture(text, size=9):
    if text not in _cache:                         # render each distinct text once
        label = CoreLabel(text=text, font_size=sp(size), color=(0.36, 0.43, 0.39, 1))
        label.refresh()
        _cache[text] = label.texture
    return _cache[text]

class Chart(Widget):
    def __init__(self, values, **kwargs):
        super().__init__(**kwargs)
        self.values = values
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        base, top, slot = y + dp(20), max(self.values), w / len(self.values)
        self.bars = []
        with self.canvas:
            for hour, value in enumerate(self.values):
                Color(*((0.85, 0.51, 0.17, 1) if value >= 12 else (0.03, 0.37, 0.29, 1)))   # surge in orange
                height = (h - dp(28)) * value / top
                self.bars.append(Rectangle(pos=(x + hour * slot + slot * .15, base), size=(slot * .7, height)))
            for hour in (0, 6, 12, 18):
                tex = text_texture(f"{hour:02d}:00")
                Color(1, 1, 1, 1)                  # white = draw the texture in its own colours
                Rectangle(texture=tex, pos=(x + hour * slot, y), size=tex.size)

class ChartApp(App):
    def build(self):
        return Chart(HOURS)

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        tallest = max(self.root.bars, key=lambda r: r.size[1])
        assert self.root.bars.index(tallest) == HOURS.index(max(HOURS))     # 17:00 is the peak
        assert len(_cache) == 4                                            # four axis labels, rendered once
        print("peak bar at hour", self.root.bars.index(tallest), "·", len(_cache), "cached labels")
        self.stop()                                                        # auto-close

ChartApp().run()
~~~

**Common mistakes.** Forgetting `label.refresh()` — the texture is `None`. Drawing a texture after a coloured `Color` — the text is tinted; set `Color(1, 1, 1, 1)` first. Creating a new `CoreLabel` per frame for every marker on a map — the frame rate drops. Dividing by a maximum of 0 when all values are zero — ATLAS Go uses `max(..., 1)`.

**ATLAS Go:** [`OutlookChart`](../android-app/atlas_go/app.py) draws the home screen's 24-hour demand forecast this way — orange bars for surge hours, a grey tick for an ordinary day, violet marks where the supply agent adds drivers, and a dashed "now" line. [`LearningCurve`](../android-app/atlas_go/app.py) plots training progress on a logarithmic x-axis. On the map, [`livemap.text_texture`](../android-app/atlas_go/livemap.py) caches label textures keyed by *(text, size, colour, bold)* and caps the cache at 300 entries.

**Lab K08** draws 200 map labels that repeat 25 names. Creating a new `CoreLabel` each time renders 200 textures (≈ 9 ms on the reference machine); ATLAS Go's `text_texture` renders 25 and takes ≈ 1 ms.

**Exercises.** (1) Add y-axis labels to the chart. (2) Turn the bars into a line chart with one `Line(points=…)`. (3) Why does an unbounded cache become a memory leak on a map where labels include changing ETAs?

## Lesson 10 — The Clock and the main loop

**Idea.** Kivy runs **one main loop on one thread**. If your code takes 2 seconds, the screen freezes for 2 seconds. Never `time.sleep()` or loop forever in a callback; ask the **Clock** to call you later instead:

| Call | Runs `callback(dt)` | Stop it by |
|---|---|---|
| `Clock.schedule_once(cb, 0)` | once, on the next frame | `event.cancel()` |
| `Clock.schedule_once(cb, 1.5)` | once, after 1.5 s | `event.cancel()` |
| `Clock.schedule_interval(cb, 1.0)` | every second | returning `False`, or `event.cancel()` |
| `Clock.schedule_interval(cb, 0)` | every frame | the same |

`dt` is the real time since the last call. Long work can be **sliced**: do a little per frame, so the UI stays responsive.

**Coalescing.** When many things change at once (markers, routes, zoom), redrawing after each change wastes work. Book **one** redraw for the next frame and ignore further requests until it has run.

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label

class ClockApp(App):
    def build(self):
        self.ticks, self.done, self.draws, self._pending = 0, 0, 0, None
        return Label(text="0")

    def on_start(self):
        Clock.schedule_interval(self.tick, 0.1)       # like ATLAS Go's live_tick (every 1 s)
        Clock.schedule_interval(self.train, 0)        # like lab_step: a slice of work per frame
        for _ in range(50):                           # 50 changes in one frame …
            self.request_draw()
        Clock.schedule_once(self.check, 1.0)

    def tick(self, _dt):
        self.ticks += 1
        self.root.text = str(self.ticks)

    def train(self, _dt):
        self.done += 100                              # pretend to train 100 episodes
        if self.done >= 1000:
            return False                              # finished: stop calling me

    def request_draw(self):                           # … but only one draw
        if self._pending is None:
            self._pending = Clock.schedule_once(self.draw, 0)

    def draw(self, _dt):
        self._pending = None
        self.draws += 1

    def check(self, _dt):
        assert 3 <= self.ticks <= 12 and self.done == 1000 and self.draws == 1   # about 9 ticks in 1 s
        print(f"{self.ticks} ticks, training finished at {self.done}, {self.draws} draw for 50 changes")
        self.stop()                                   # auto-close

ClockApp().run()
~~~

**Common mistakes.** `time.sleep()` in a callback (the whole app freezes). Scheduling an interval every time a screen opens and never cancelling it — after ten visits the callback runs ten times per second. Assuming `schedule_interval(cb, 1.0)` is exact — use `dt` or `time.time()` for real time. Scheduling a callback on a widget that has since been removed.

**ATLAS Go:** [`build`](../android-app/atlas_go/app.py) starts `Clock.schedule_interval(self.live_tick, 1.0)`; [`live_tick`](../android-app/atlas_go/app.py) advances simulated journeys and either re-renders or only refreshes the map and ETA label. [`lab_train`](../android-app/atlas_go/app.py) schedules `lab_step` every frame; each step trains 1,500 rides and returns `False` when the learning lab is done, so the progress chart animates while the app stays responsive. [`LiveMap._schedule`](../android-app/atlas_go/livemap.py) coalesces redraws exactly as in the example; [`LiveMap.fit`](../android-app/atlas_go/livemap.py) retries on the next frame if its size is not known yet.

**Lab K09** makes 1 to 100 property changes in one frame and counts the draws. Drawing on every change gives 1 to 100 draws; the coalesced widget draws once every time — a flat line on the log chart.

**Exercises.** (1) Make the training slice adaptive: measure `time.perf_counter()` and do as much as fits in 8 ms. (2) What happens in ATLAS Go if `live_tick` takes longer than a second? (3) Cancel the 0.1 s tick when the label is tapped.

## Lesson 11 — Touch input: `on_touch_down`, `move`, `up`, grabbing and clipping

**Idea.** Every finger (or mouse click) is a **touch** object. Kivy offers it to widgets **from the top of the tree down**: the root's `on_touch_down` is called, which by default asks each child in turn. A widget that wants the touch returns `True`, and the search stops. **Important:** every widget is offered every touch, even ones outside it — check `self.collide_point(*touch.pos)` yourself.

To follow a drag, **grab** the touch in `on_touch_down`; then `on_touch_move` and `on_touch_up` come to you with `touch.grab_current is self`, even if the finger leaves the widget. Release it with `touch.ungrab(self)`. `touch.is_double_tap` detects double taps. A `StencilView` clips its drawing to its own rectangle — essential for a map that must not paint over the rest of the screen.

~~~mermaid
sequenceDiagram
 participant F as finger
 participant M as Map (StencilView)
 F->>M: on_touch_down (inside? → grab, remember pos)
 F->>M: on_touch_move (grab_current is me → pan by dx, dy)
 F->>M: on_touch_move …
 F->>M: on_touch_up (ungrab)
~~~

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.tests.common import UnitTestTouch
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stencilview import StencilView
from kivy.uix.widget import Widget

class Pan(StencilView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.offset, self._last = [0, 0], None

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)       # not mine: let others have it
        touch.grab(self)
        self._last = touch.pos
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        self.offset[0] += touch.x - self._last[0]
        self.offset[1] += touch.y - self._last[1]
        self._last = touch.pos
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)

class TouchApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")
        self.pan = Pan()
        root.add_widget(self.pan)                     # top half
        root.add_widget(Widget())                     # bottom half
        return root

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        x, y = self.pan.center
        touch = UnitTestTouch(x, y)                   # a simulated finger
        touch.touch_down()
        for step in range(1, 11):
            touch.touch_move(x + 10 * step, y - 4 * step)
        touch.touch_move(x + 100, 5)                  # leave the widget: still ours (grabbed)
        touch.touch_up()
        assert self.pan.offset == [100, 5 - y]
        outside = UnitTestTouch(x, 5)                 # starts in the bottom half: ignored
        outside.touch_down(); outside.touch_move(x + 50, 5); outside.touch_up()
        assert self.pan.offset == [100, 5 - y]
        print("panned by", [round(v) for v in self.pan.offset])
        self.stop()                                   # auto-close

TouchApp().run()
~~~

**Common mistakes.** Not checking `collide_point` — the map pans when you scroll the list below it. Not calling `super()` for touches you do not want — buttons inside your widget stop working. Not grabbing — the drag stops as soon as the finger leaves the widget. Forgetting y points up when converting screen movement to map movement.

**ATLAS Go:** [`LiveMap`](../android-app/atlas_go/livemap.py) is a `StencilView`. Its `on_touch_down` ignores touches outside it, gives its children (the zoom buttons) the first chance, then either zooms on a double tap or grabs the touch. `on_touch_move` converts the finger's movement into a new map centre with Web-Mercator maths (`geo.world_px` / `geo.from_world_px`), and `on_touch_up` releases the grab. Non-interactive previews (`interactive=False`) let the touch fall through so the page can scroll.

**Lab K10** drags the **real** `LiveMap` 100 px right and 60 px down at zoom levels 12 to 16, then measures where the old centre is drawn. It moves by exactly (100, −60) px every time, while the distance on the ground halves at each level: 3,516 m at zoom 12, 220 m at zoom 16.

**Exercises.** (1) Add a pinch-to-zoom: track two grabbed touches and compare their distance. (2) Why does `LiveMap.on_touch_down` call `super().on_touch_down(touch)` *before* checking `interactive`? (3) Make a long press (touch held 0.6 s without moving) drop a pin, using `Clock.schedule_once` and `cancel`.

## Lesson 12 — Threads and the UI thread

**Idea.** Some work cannot be sliced: a network download blocks until the server answers. That work belongs in a **background thread** (`threading.Thread`). But Kivy's widgets and OpenGL textures belong to the **main thread** — touching them from another thread can crash the app or corrupt the screen. The rule: **workers fetch bytes; the main thread builds widgets and textures.** `Clock.schedule_once` is thread-safe, so a worker hands its result over by scheduling a callback.

~~~mermaid
sequenceDiagram
 participant UI as main thread (Kivy)
 participant Q as queue
 participant W as worker thread
 UI->>Q: put(tile key)
 W->>Q: get()
 W->>W: download bytes (blocking, slow)
 W->>UI: Clock.schedule_once(deliver(key, bytes))
 UI->>UI: bytes → texture → redraw map
~~~

~~~python
import queue
import threading
import time
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label

class Loader:
    def __init__(self, on_result, workers=2):
        self.jobs, self.on_result = queue.Queue(), on_result
        for _ in range(workers):
            threading.Thread(target=self.work, daemon=True).start()

    def work(self):                                    # runs on a worker thread
        while True:
            key = self.jobs.get()
            time.sleep(0.05)                           # pretend to download a map tile
            data = f"tile {key}".encode()
            Clock.schedule_once(lambda _dt, key=key, data=data: self.on_result(key, data), 0)

class ThreadApp(App):
    def build(self):
        self.main = threading.get_ident()
        self.results = {}
        self.loader = Loader(self.deliver)
        return Label(text="loading…")

    def deliver(self, key, data):                     # runs on the main thread
        assert threading.get_ident() == self.main
        self.results[key] = data
        self.root.text = f"{len(self.results)} tiles"

    def on_start(self):
        for key in range(8):
            self.loader.jobs.put(key)
        Clock.schedule_once(self.check, 1.0)

    def check(self, _dt):
        assert len(self.results) == 8 and self.root.text == "8 tiles"
        print("8 tiles downloaded in the background and delivered on the main thread")
        self.stop()                                    # auto-close

ThreadApp().run()
~~~

**Common mistakes.** Setting `label.text` or creating a texture inside the worker. Non-daemon threads that keep the app alive after it closes. Sharing a `set` or `dict` between threads without a `Lock`. Hammering a server that is down — back off after repeated failures.

**ATLAS Go:** [`TileLoader`](../android-app/atlas_go/livemap.py) starts two daemon worker threads that take tile keys from a `LifoQueue` (the newest request first, because that is what the user is looking at now). A worker reads the tile from the disk cache or downloads it with `requests`, writes it atomically, and hands the bytes to `_deliver` with `Clock.schedule_once`. On the main thread, `_deliver` makes the texture with `CoreImage`, keeps at most 160 textures in an `OrderedDict` (least recently used first out) and tells listening maps to redraw. A `Lock` protects the set of pending keys; after three failures the loader goes offline for 45 s and the map draws its schematic layer.

**Lab K11** sends 40 jobs to worker threads twice: once calling the result function directly from the worker, once through `Clock.schedule_once`. The bar chart shows 40/0 deliveries on a worker thread for the direct version and 0/40 for the Clock version — every result reaches the UI thread.

**Exercises.** (1) Replace `queue.Queue` with `queue.LifoQueue` and observe the delivery order. (2) Add a `Lock` around `self.results`; is it needed in this example? Why not? (3) Read `TileLoader._fetch` and list every way a download can fail.

---

# Part IV — A whole app on a real phone

## Lesson 13 — Screens as state: one `render()` instead of many screens

**Idea.** An app has many screens. Kivy offers two styles:

| Style | How it works | Good for |
|---|---|---|
| **Retained screens** (`ScreenManager`, often written in the **KV language**) | build every screen once, switch between them, update their widgets when data changes | rich animations between screens; designers who prefer markup |
| **State → render** (ATLAS Go) | keep the state in Python variables (`self.screen`, `self.pickup`, the store); on every change, throw the screen away and build it from the state | simple, predictable code; screens can never show stale data |

ATLAS Go chooses **state → render**: a dictionary maps the screen name to a method, `go(screen)` changes the state and calls `render()`, and `save_ui()` writes the state to disk so the app reopens where the user left it.

~~~mermaid
stateDiagram-v2
 [*] --> welcome
 welcome --> login
 welcome --> register
 welcome --> home: guest
 login --> home: passenger
 login --> driver: driver
 login --> seller: food seller
 home --> ride
 home --> food
 food --> menu --> cart --> active_order
 ride --> active_ride
 home --> map
 home --> profile
~~~

~~~python
import json
import tempfile
from pathlib import Path
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

STATE = Path(tempfile.mkdtemp()) / "ui.json"

class MiniAtlas(App):
    def build(self):
        saved = json.loads(STATE.read_text()) if STATE.exists() else {}
        self.screen = saved.get("screen", "home")        # reopen where the user left
        self.basket = saved.get("basket", 0)
        self.container = BoxLayout(orientation="vertical")
        self.render()
        return self.container

    def go(self, screen):
        self.screen = screen
        STATE.write_text(json.dumps({"screen": self.screen, "basket": self.basket}))
        self.render()

    def render(self):
        self.container.clear_widgets()
        {"home": self.home, "food": self.food}.get(self.screen, self.home)()
        nav = BoxLayout(size_hint_y=0.2)
        for key in ("home", "food"):
            button = Button(text=key.title())
            button.bind(on_release=lambda _w, key=key: self.go(key))
            nav.add_widget(button)
        self.container.add_widget(nav)

    def home(self):
        self.container.add_widget(Label(text="Your city. One app."))

    def food(self):
        self.container.add_widget(Label(text=f"Basket: {self.basket} dishes"))
        add = Button(text="Add a dish")
        add.bind(on_release=lambda _w: self.add_dish())
        self.container.add_widget(add)

    def add_dish(self):
        self.basket += 1
        self.go("food")                                  # state changed → render again

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        self.go("food")
        self.add_dish(); self.add_dish()
        shown = [w.text for w in self.container.walk() if isinstance(w, Label) and "Basket" in w.text]
        assert shown == ["Basket: 2 dishes"]             # the screen always matches the state
        assert json.loads(STATE.read_text()) == {"screen": "food", "basket": 2}
        print(shown[0], "· saved", STATE.read_text())
        self.stop()                                      # auto-close

MiniAtlas().run()
~~~

**The KV language (not used by ATLAS Go).** Many Kivy tutorials describe widgets in `.kv` files, a small declarative language with Python expressions. You will meet it elsewhere, so here is the same nav bar in KV, loaded from Python:

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder

KV = """
BoxLayout:
    orientation: "vertical"
    Label:
        id: title
        text: "home"
    BoxLayout:
        size_hint_y: 0.2
        Button:
            text: "Home"
            on_release: title.text = "home"
        Button:
            text: "Food"
            on_release: title.text = "food"
"""

class KvApp(App):
    def build(self):
        return Builder.load_string(KV)

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        food = [b for b in self.root.walk() if getattr(b, "text", "") == "Food"][0]
        food.trigger_action(duration=0)
        assert self.root.ids.title.text == "food"
        print("KV rule bound on_release to", self.root.ids.title.text)
        self.stop()                                      # auto-close

KvApp().run()
~~~

KV is convenient for static layouts and automatic property bindings, but it splits a screen between two files and two languages. ATLAS Go builds everything in plain Python so that each screen is one readable method, every control is reachable from tests through `self.controls`, and the whole front end is covered by the Python tooling (linters, coverage) that the [Python course](PYTHON_PROGRAMMING.md) teaches.

**Common mistakes.** Mixing the styles — updating one widget by hand *and* re-rendering, so the two disagree. Forgetting to clean up before `clear_widgets()` (ATLAS Go detaches the old `LiveMap` from the tile loader in `render`). Saving state that cannot be restored (a widget object in JSON). Allowing a screen the current role must not see — always re-check the role in `render`.

**ATLAS Go:** [`render`](../android-app/atlas_go/app.py) clamps the screen to what the signed-in role may see (drivers and sellers have their own allowed sets), builds header, body and role-specific navigation (`nav_items`), and highlights the current tab in lime. [`go`](../android-app/atlas_go/app.py) = set screen → `save_ui()` → `render()`. [`save_ui`](../android-app/atlas_go/app.py) stores nine UI fields (`screen`, `pickup`, `destination`, `party`, `comfort`, `restaurant`, `address`, `outlook_day`, `reg_role`) in the store; `build` restores them. [`refresh_live`](../android-app/atlas_go/app.py) is the one deliberate exception: once a second it updates only the map layers and ETA text, because rebuilding the map every second would reset the user's pan.

**Exercises.** (1) Add a *profile* screen to `MiniAtlas` that only appears when `self.user` is set. (2) Rewrite `MiniAtlas` with `ScreenManager` and compare the code size. (3) In the KV example, add a third button and a `Label` whose text is bound to `title.text`.

## Lesson 14 — Talking to Android with pyjnius

**Idea.** Kivy runs on Android inside a Java activity. When you need something only Android provides — GPS, permissions, the status-bar size — **pyjnius** lets Python call Java directly:

| pyjnius | What it does | ATLAS Go example |
|---|---|---|
| `autoclass('android.content.Context')` | loads a Java class as a Python class | `Context`, `Looper`, `Build$VERSION` (an inner class uses `$`) |
| `autoclass('org.kivy.android.PythonActivity').mActivity` | the running app's Activity | the starting point for every Android call |
| `class L(PythonJavaClass)` with `__javainterfaces__` | implements a Java interface in Python | `LocationListener` |
| `@java_method('(Landroid/location/Location;)V')` | declares the Java signature of a method | `onLocationChanged(Location) → void` |
| `@run_on_ui_thread` (`android.runnable`) | runs a function on Android's UI thread | reading window insets |

Java signatures use **JNI type descriptors**: `V` void, `I` int, `Z` boolean, `F` float, `J` long, `Ljava/lang/String;` a class (note the `L … ;`). `(Ljava/lang/String;ILandroid/os/Bundle;)V` means *takes String, int, Bundle; returns void*.

Two Android rules shape the code: **dangerous permissions** (location) must be **requested at run time** and the user may say no; and Java callbacks arrive on **Java threads**, so results go back to Kivy with `Clock.schedule_once` (Lesson 12).

~~~mermaid
sequenceDiagram
 participant App as AtlasGoApp (Kivy)
 participant DL as DeviceLocation
 participant AND as Android
 App->>DL: start()
 DL->>AND: request_permissions([FINE, COARSE])
 AND-->>DL: answered(grants) (Java thread)
 DL->>DL: Clock.schedule_once(_android_listen)
 DL->>AND: LocationManager.requestLocationUpdates(gps/network, 3 s, 5 m, listener)
 AND-->>DL: listener.onLocationChanged(location) (Java thread)
 DL->>App: Clock.schedule_once → on_fix(point, accuracy)
~~~

Every Android call must have a **desktop path**, or the app cannot be developed and tested on a computer. This example runs everywhere: on Android it reads the real SDK version; elsewhere it uses a fallback, like ATLAS Go's `ATLAS_FAKE_GPS`.

~~~python
import os
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.utils import platform

def android_sdk():
    """Android's API level via pyjnius; None on a desktop."""
    if platform != "android":
        return None
    from jnius import autoclass                     # only importable on Android
    return int(autoclass("android.os.Build$VERSION").SDK_INT)

def location():
    """A real fix needs Android; a desktop can fake one (ATLAS_FAKE_GPS='51.8935,-8.4921')."""
    fake = os.environ.get("ATLAS_FAKE_GPS")
    if platform == "android" or not fake:
        return None
    lat, lon = (float(v) for v in fake.split(","))
    return lat, lon

class AndroidApp(App):
    def build(self):
        return Label(text=f"platform: {platform}")

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        sdk = android_sdk()
        os.environ["ATLAS_FAKE_GPS"] = "51.8935,-8.4921"
        point = location()
        if platform == "android":
            assert sdk >= 26                         # ATLAS Go's android.minapi
        else:
            assert sdk is None and point == (51.8935, -8.4921)
        print("platform", platform, "· SDK", sdk, "· location", point)
        self.stop()                                  # auto-close

AndroidApp().run()
~~~

**Common mistakes.** Importing `jnius` or `android` at the top of a module — the app cannot even start on a desktop; import inside the Android branch. Wrong JNI signatures — the callback is never called, with no error. Updating Kivy widgets from a Java callback thread. Assuming permission was granted. Calling Android View methods off Android's UI thread (use `run_on_ui_thread`). Forgetting to remove listeners in `on_pause` (battery drain).

**ATLAS Go:** [`DeviceLocation`](../android-app/atlas_go/location.py) checks `android.permissions`, requests `ACCESS_FINE_LOCATION`/`ACCESS_COARSE_LOCATION` if needed, implements `android/location/LocationListener` with four `@java_method`s, registers it with `LocationManager.requestLocationUpdates(provider, 3000, 5.0, listener, Looper.getMainLooper())` for the *gps* and *network* providers, and passes every fix back with `Clock.schedule_once`. On a desktop it uses `ATLAS_FAKE_GPS` or reports that location needs the phone. [`configure_system_bars`](../android-app/atlas_go/app.py) uses `@run_on_ui_thread` to read the status- and gesture-bar insets (`WindowInsets$Type` on Android 11+), then `apply_system_insets` pads the root layout so content is not hidden under the bars on Android 15's edge-to-edge screens. `on_pause` calls `gps.stop()`, which removes the listener.

**Exercises.** (1) Decode the signature `(Ljava/lang/String;)V`. (2) Write a pyjnius call that reads the device model (`android.os.Build.MODEL`) guarded for the desktop. (3) Why does `DeviceLocation.stop` catch exceptions while removing the listener?

## Lesson 15 — Packaging for Android with Buildozer

**Idea.** A phone cannot run `python main.py`. **python-for-android** (p4a) compiles Python, Kivy and your dependencies for ARM processors and wraps them in a Java activity; **Buildozer** drives p4a, the Android SDK and NDK from one settings file, `buildozer.spec` (INI format: `key = value` lines in sections).

~~~mermaid
flowchart LR
 SRC["main.py + atlas_go/<br/>+ assets"] --> BZ["buildozer android debug / release"]
 SPEC["buildozer.spec"] --> BZ
 BZ --> P4A["python-for-android<br/>(recipes: python3, kivy, requests, certifi)"]
 P4A --> NDK["Android NDK<br/>compile for arm64-v8a, x86_64"]
 P4A --> GRADLE["Gradle + Android SDK (API 36)"]
 GRADLE --> APK[(".apk (debug)")]
 GRADLE --> AAB[(".aab (release, for Google Play)")]
~~~

The settings that matter most in ATLAS Go's [`buildozer.spec`](../android-app/buildozer.spec):

~~~ini
[app]
title = ATLAS Go
package.name = mobility
package.domain = org.atlas                       # the app id becomes org.atlas.mobility
source.include_exts = py,png,kv,ttf,json         # which files are packed
source.exclude_dirs = tests,docs,releases,scripts,training,...   # keep the APK small
version = 1.2.0
android.numeric_version = 3                      # must grow with every Play upload
requirements = python3,kivy==2.3.1,requests,certifi   # pinned: the same Kivy as on the desktop
orientation = portrait
android.api = 36                                 # target SDK
android.minapi = 26                              # oldest Android supported (8.0)
android.archs = arm64-v8a, x86_64                # real phones + the emulator
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION
android.allow_backup = False                     # accounts stay on this phone only
android.release_artifact = aab
android.debug_artifact = apk
p4a.commit = 1c9a4b4f...                         # pinned toolchain: reproducible builds
~~~

Typical commands (on Linux or macOS, not inside this course's labs):

~~~bash
cd android-app
buildozer android debug             # build bin/*.apk
buildozer android debug deploy run  # install on a USB-connected phone and start it
buildozer android logcat            # read Python errors from the phone
~~~

**Common mistakes.** A dependency missing from `requirements` — the app starts on the desktop and crashes on the phone with `ModuleNotFoundError`. Pure-Python packages are fine; packages with C code need a p4a **recipe**. Forgetting a permission in the spec — the runtime request in Lesson 14 then always fails. Leaving `tests/` and training data in the package. Not raising `android.numeric_version` — Google Play rejects the upload. Floating versions (`kivy` without `==`) — two builds of the same code behave differently.

**ATLAS Go:** besides the spec, [`android-app/scripts/`](../android-app/scripts/) checks the generated manifest (`check-manifest.py`), the 16 KB page alignment of the native libraries that Android 15+ requires (`check-native-alignment.py`), and signs the release; [`docs/GOOGLE_PLAY.md`](../android-app/docs/GOOGLE_PLAY.md) is the full build and store-upload guide.

**Exercises.** (1) Which `requirements` entry provides HTTPS certificates for `requests`, and why is it needed on Android? (2) What would `android.minapi = 21` break in `configure_system_bars`? (3) Build the debug APK and find `ATLAS:` lines with `buildozer android logcat | grep ATLAS`.

## Lesson 16 — Testing a Kivy front end

**Idea.** UI code is hard to test, so **keep as little logic in it as possible**. ATLAS Go's layering makes that possible:

| Layer | Tested how | Needs a window? |
|---|---|---|
| Rules: fares, validation, dispatch, storage (`domain.py`, `accounts.py`, `store.py`, `intelligence.py`, `geo.py`) | ordinary `pytest` unit tests | no |
| Widgets and screens (`app.py`, `livemap.py`) | drive real controls: `trigger_action`, simulated touches, then check the state and take screenshots | yes (a real or virtual display) |
| The packaged app on a phone | the same acceptance run inside a debug APK on an emulator | an emulator |

Three tools make widget tests possible: **named controls** (a dictionary from a stable key to each button and field, so tests do not hunt for text), `button.trigger_action(duration=0)` (press it in code), and `Window.screenshot()` (save what the user sees). On a server, `xvfb-run` provides a virtual display.

~~~python
import os
import tempfile
from pathlib import Path
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

class Screen(App):
    def build(self):
        self.controls, self.signed_in = {}, False
        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(10))
        email = TextInput(hint_text="Email", multiline=False, size_hint_y=None, height=dp(48))
        submit = Button(text="Sign in", size_hint_y=None, height=dp(48))
        submit.bind(on_release=lambda _w: self.sign_in())
        self.controls.update(login_email=email, login_submit=submit)    # stable keys for tests
        root.add_widget(email); root.add_widget(submit)
        return root

    def sign_in(self):
        self.signed_in = "@" in self.controls["login_email"].text

    def on_start(self):
        Clock.schedule_once(self.acceptance, 0.5)

    def acceptance(self, _dt):                      # an end-to-end check, like acceptance.py
        checks = 0
        def check(condition, message):
            nonlocal checks
            assert condition, message
            checks += 1
        check(all(w.width >= dp(40) and w.height >= dp(44) for w in self.controls.values()),
              "controls are big enough to touch")
        self.controls["login_email"].text = "ana@example.ie"
        self.controls["login_submit"].trigger_action(duration=0)
        check(self.signed_in, "signed in after pressing the button")
        shot = Path(tempfile.mkdtemp()) / "login.png"
        Path(Window.screenshot(name=str(shot))).replace(shot)       # Kivy adds a number; rename it
        check(shot.exists() and shot.stat().st_size > 0, "screenshot saved")
        print(checks, "checks passed; screenshot", shot.name)
        self.stop()                                 # auto-close

Screen().run()
~~~

**Common mistakes.** Testing rules through the UI when a unit test would do. Finding buttons by their visible text — it changes with wording or language. Comparing screenshots pixel by pixel across machines (fonts differ); use them for people to review. Leaving test hooks switched on in a release build.

**ATLAS Go:** [`tests/`](../android-app/tests/) holds the window-free unit tests (`pytest android-app/tests`). [`acceptance.py`](../android-app/atlas_go/acceptance.py) is the UI test: it clicks the real controls through `self.app.controls[key].trigger_action(duration=0)`, fills fields, checks the store after each step and that every control is at least 40 × 44 px, and saves a screenshot of each screen (on Android it asks the host for an OS screenshot instead). It only runs on the desktop with `ATLAS_UI_TEST=1`, or on Android in a **debuggable** build launched with the `atlas_acceptance` extra — the signed release ignores it. The screenshots in [`docs/screenshots/`](../android-app/docs/screenshots/) come from these runs, at 440×940 and 360×780 (`ATLAS_PREVIEW_SIZE`).

**Lab (all).** The 11 Kivy labs are themselves tests: each one asserts what it measured, and `python kivy_lab/experiments.py` (with no arguments) runs them all as a self-test.

**Exercises.** (1) Run the real acceptance test as described in [`android-app/docs/TESTING.md`](../android-app/docs/TESTING.md): `cd android-app && ATLAS_UI_TEST=1 ATLAS_DATA_DIR="$PWD/local-data" python main.py` (add `xvfb-run -a` on a server), then `python scripts/verify-acceptance.py local-data/test-output`, and open the screenshots in `local-data/test-output/`. (2) Add a check to the example that the password field, if any, has `password=True`. (3) Write a `pytest` test for `parse_seats` from Lesson 7 without starting Kivy at all.

---

# Practice

## Running the lab

~~~bash
python -m pip install kivy==2.3.1 matplotlib
python kivy_lab/experiments.py                 # runs all 11 labs as a self-test, then usage
python kivy_lab/experiments.py --list
python kivy_lab/experiments.py --all           # K01-K11 -> kivy_lab/results (csv, json, png)
python kivy_lab/experiments.py --experiment 10
xvfb-run -a python kivy_lab/experiments.py --all   # on a Linux server with no display
~~~

See the [lab manual](../kivy_lab/README.md) for the register of experiments, what each chart shows and the reference results.

## Six-week teaching plan

| Week | Lessons | Lab | Build |
|---|---|---|---|
| 1 | 1–2 | K01, K02 | a one-screen app with a header and three buttons |
| 2 | 3–4 | K03, K04 | a scrolling list of 20 ride cards that looks right at 360 and 440 dp wide |
| 3 | 5–7 | K05, K06 | a booking form with validation and a confirmation dialog |
| 4 | 8–9 | K07, K08 | a 24-hour demand chart drawn on the canvas |
| 5 | 10–12 | K09–K11 | a pannable map of tiles loaded by a background thread |
| 6 | 13–16 | all | the capstone, packaged as a debug APK and tested with an acceptance script |

## Capstone

Build **"ATLAS Go Lite"**: three screens (*Home*, *Food*, *Map*) using the state → render pattern; a basket stored with an atomic JSON write; a canvas-drawn bar chart; a pannable map widget (a grid is enough — no network); a Back-key handler; an acceptance script that presses every named control and saves a screenshot of each screen. Assessment: correctness of the acceptance run (40 %), code structure — rules outside widgets, no blocking calls on the main thread (30 %), visual quality at two window sizes (20 %), a short note on what you would change to package it with Buildozer (10 %).

## Quick reference

| Task | Kivy |
|---|---|
| start an app | `class MyApp(App): def build(self): return root` → `MyApp().run()` |
| stack widgets | `BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))` |
| fixed height | `size_hint_y=None, height=dp(48)` |
| grow with content | `box.bind(minimum_height=box.setter('height'))` |
| wrap text | `label.bind(width=lambda w, v: setattr(w, 'text_size', (v, None)))` |
| click | `button.bind(on_release=lambda _w, key=key: go(key))` |
| Back key | `Window.bind(on_keyboard=…)`; key `27`; return `True` if handled |
| background | `with self.canvas.before: Color(...); self.rect = RoundedRectangle(...)` + bind `pos`, `size` |
| redraw | `self.canvas.clear()` then `with self.canvas: …` |
| text on canvas | `CoreLabel(text=…).refresh()` → `Rectangle(texture=label.texture)` |
| later / repeat | `Clock.schedule_once(cb, t)`, `Clock.schedule_interval(cb, t)`; return `False` to stop |
| from a thread | `Clock.schedule_once(lambda dt: deliver(result), 0)` |
| drag | `touch.grab(self)` in down; `touch.grab_current is self` in move/up |
| clip drawing | subclass `StencilView` |
| Android class | `from jnius import autoclass` inside `if platform == 'android':` |
| press in a test | `button.trigger_action(duration=0)` |

## Self-check questions

1. In what order does Kivy call `build`, `on_start` and `on_stop`? *(build → on_start → … → on_stop; run() returns last.)*
2. A child has `height=dp(48)` but is 300 px tall. Why? *(It still has `size_hint_y=1`; set `size_hint_y=None`.)*
3. Why `sp` for fonts but `dp` for padding? *(sp follows the user's font-size setting.)*
4. Why does every navigation button open the last screen? *(Late-binding closure; use `lambda key=key:`.)*
5. Why is a drawing doubled after rotating the phone? *(The redraw did not call `canvas.clear()`.)*
6. Why must text be cached on a live map? *(Rendering a texture is expensive and labels repeat every frame.)*
7. The app freezes while loading tiles. What is wrong? *(The download runs on the main thread — move it to a worker and deliver with the Clock.)*
8. A map pans when you scroll the list beneath it. What is missing? *(A `collide_point` check in `on_touch_down`.)*
9. What does `(Ljava/lang/String;I)V` mean? *(A Java method taking a String and an int, returning void.)*
10. The app works on the desktop but crashes at once on the phone with `ModuleNotFoundError`. *(The package is missing from `requirements` in `buildozer.spec`.)*
