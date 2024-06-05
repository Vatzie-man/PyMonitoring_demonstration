import tkinter as tk
from tkinter import ttk
import sqlite3


class Model:

    def __init__(self):
        self.connection = sqlite3.connect("_options.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS options (option TEXT PRIMARY KEY, state INTEGER)")

    def update_options_text(self, options):
        for option, state in options.items():

            if isinstance(state, tk.BooleanVar):
                state = state.get()
            self.cursor.execute("INSERT OR REPLACE INTO options VALUES (?, ?)", (option, bool(state)))
        self.connection.commit()

    def update_radio_choice(self, radio_choice):
        if isinstance(radio_choice, tk.StringVar):
            radio_choice = radio_choice.get()
        self.cursor.execute("INSERT OR REPLACE INTO options VALUES (?, ?)", ("display_mode", radio_choice))
        self.connection.commit()

    def update_combo_choice(self, combo_choice):
        if isinstance(combo_choice, tk.StringVar):
            combo_choice = combo_choice.get()
        self.cursor.execute("INSERT OR REPLACE INTO options VALUES (?, ?)", ("time_delay", combo_choice))
        self.connection.commit()

    def get_options(self):
        options = self.cursor.execute("select option, state from options")
        return options


class App(tk.Tk):

    def __init__(self, model: Model):
        super().__init__()
        self.combo_choice = None
        self.radio_choice = None
        self.check_options = None
        self.model = model
        self.title("PyMonitoring")
        self.geometry("240x270")
        self.create_ui()
        self.load_states()

    def load_states(self):

        options = self.model.get_options()

        rows = options.fetchall()

        for row in rows:
            if row[0] == "display_mode":
                self.model.update_radio_choice(row[1])
                self.radio_choice.set(row[1])

            elif row[0] == "time_delay":
                self.model.update_combo_choice(row[1])
                self.combo_choice.set(row[1])
            else:
                self.model.update_options_text({row[0]: row[1]})
                self.check_options[row[0]].set(bool(row[1]))

    def create_ui(self) -> None:
        self.frame = tk.Frame(self, bg="blue")
        self.frame.pack(fill=tk.BOTH, expand=False)

        self.check_options = {}
        self.radio_choice = tk.StringVar()
        self.combo_choice = tk.StringVar(value="1")

        def update_options_text() -> None:
            self.model.update_options_text(self.check_options)

        check_label = tk.Label(self, text="         Options:", fg="blue")
        check_label.pack(anchor="nw")
        check_option_texts = ["notifications", "whatsapp", "check channels"]
        for option_text in check_option_texts:
            var = tk.BooleanVar()
            self.check_options[option_text] = var
            switch = tk.Checkbutton(self, text=option_text, variable=var, command=update_options_text)
            switch.pack(anchor="w")

        def update_radio_choice() -> None:
            self.model.update_radio_choice(self.radio_choice)

        radio_label = tk.Label(self, text="         MM Display:", fg="blue")
        radio_label.pack(anchor="nw")
        radio_option_texts = ["plain mode", "json", "data formatted"]
        for option_text in radio_option_texts:
            radio = tk.Radiobutton(self, text=option_text, variable=self.radio_choice, value=option_text, command=update_radio_choice)
            radio.pack(anchor="nw")

        def update_combo_choice(event=None) -> None:
            self.model.update_combo_choice(self.combo_choice)

        combo_label = tk.Label(self, text="         Wait time(s):", fg="blue")
        combo_label.pack(anchor="nw")
        combo_options = ["1", "2", "3", "4", "5"]
        combo = ttk.Combobox(self, textvariable=self.combo_choice, values=combo_options)
        combo.pack(anchor="center")
        combo.bind("<<ComboboxSelected>>", update_combo_choice)


class Controller:
    def __init__(self, model: Model, view: App) -> None:
        self.model = model
        self.view = view

    def run(self) -> None:
        self.view.mainloop()


def controller_run() -> None:
    model = Model()
    view = App(model)
    controller = Controller(model, view)
    controller.run()


controller_run()
