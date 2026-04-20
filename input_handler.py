import tkinter as tk


class InputHandler:
    def __init__(self, root):
        self.root = root

        self._scroll_velocity = 0
        self._scroll_job = None
        self.active_widget = None
        self.last_y = 0

        self.bind_global_events()

    # ================= GLOBAL BIND =================
    def bind_global_events(self):
        # 🔥 Use bind_class instead of bind_all (THIS IS THE FIX)
        self.root.bind_class("Text", "<MouseWheel>", self.on_mousewheel, add="+")
        self.root.bind_class("Canvas", "<MouseWheel>", self.on_mousewheel, add="+")
        self.root.bind_class("Listbox", "<MouseWheel>", self.on_mousewheel, add="+")
        self.root.bind_class("Frame", "<MouseWheel>", self.on_mousewheel, add="+")

        # Linux
        for cls in ("Text", "Canvas", "Listbox", "Frame"):
            self.root.bind_class(cls, "<Button-4>", lambda e: self.on_mousewheel_linux(e, -2), add="+")
            self.root.bind_class(cls, "<Button-5>", lambda e: self.on_mousewheel_linux(e, 2), add="+")

        # Touch drag
        self.root.bind_all("<ButtonPress-1>", self.on_touch_start, add="+")
        self.root.bind_all("<B1-Motion>", self.on_touch_move, add="+")

        # Keyboard
        self.root.bind_all("<Return>", self.on_enter, add="+")
        self.root.bind_all("<Control-a>", self.select_all, add="+")
        self.root.bind_all("<Control-c>", self.copy, add="+")
        self.root.bind_all("<Control-v>", self.paste, add="+")

    # ================= FIND SCROLLABLE =================
    def get_scroll_widget(self, widget):
        while widget:
            if isinstance(widget, (tk.Canvas, tk.Text, tk.Listbox)):
                return widget
            widget = widget.master
        return None

    # ================= SCROLL =================
    def on_mousewheel(self, event):
        widget = self.get_scroll_widget(event.widget)

        if not widget:
            return

        self.active_widget = widget

        try:
            delta = -event.delta / 120
            self._scroll_velocity += delta * 2.5
            self.start_momentum()
        except Exception as e:
            print(f"[ERROR] Handling mouse wheel in {event.widget}: {e}")

    def on_mousewheel_linux(self, event, direction):
        widget = self.get_scroll_widget(event.widget)

        if not widget:
            return

        self.active_widget = widget

        try:
            self._scroll_velocity += direction * 2
            self.start_momentum()
        except Exception as e:
            print(f"[ERROR] Handling mouse wheel on Linux in {event.widget}: {e}")

    # ================= TOUCH =================
    def on_touch_start(self, event):
        try:
            self.last_y = event.y
        except Exception as e:
            print(f"[ERROR] Handling touch start in {event.widget}: {e}")
            self.last_y = 0

    def on_touch_move(self, event):
        widget = self.get_scroll_widget(event.widget)

        if not widget:
            return

        self.active_widget = widget

        try:
            delta = self.last_y - event.y
            self._scroll_velocity = delta * 0.6
            self.last_y = event.y
            self.start_momentum()
        except Exception as e:
            print(f"[ERROR] Handling touch move in {event.widget}: {e}")

    # ================= MOMENTUM =================
    def start_momentum(self):
        try:
            if self._scroll_job:
                self.root.after_cancel(self._scroll_job)
        except Exception as e:
            print(f"[ERROR] Canceling scroll job: {e}")

        self._smooth_scroll()

    def _smooth_scroll(self):
        if not self.active_widget:
            return

        if abs(self._scroll_velocity) < 0.2:
            self._scroll_velocity = 0
            return

        try:
            self.active_widget.yview_scroll(int(self._scroll_velocity), "units")
        except Exception as e:
            print(f"[ERROR] Scrolling in {self.active_widget}: {e}")
            return

        self._scroll_velocity *= 0.88
        self._scroll_job = self.root.after(16, self._smooth_scroll)

    # ================= KEYBOARD =================
    def on_enter(self, event):
        widget = event.widget

        if isinstance(widget, tk.Entry):
            try:
                parent = widget.master
                for child in parent.winfo_children():
                    if isinstance(child, tk.Button):
                        if "send" in child.cget("text").lower():
                            child.invoke()
                            return
            except Exception as e:
                print(f"[ERROR] Invoking send button in {event.widget}: {e}")

    def select_all(self, event):
        try:
            event.widget.select_range(0, tk.END)
            event.widget.icursor(tk.END)
            return "break"
        except Exception as e:
            print(f"[ERROR] Selecting all in {event.widget}: {e}")

    def copy(self, event):
        try:
            event.widget.event_generate("<<Copy>>")
        except Exception as e:
            print(f"[ERROR] Copying in {event.widget}: {e}")

    def paste(self, event):
        try:
            event.widget.event_generate("<<Paste>>")
        except Exception as e:
            print(f"[ERROR] Pasting in {event.widget}: {e}")