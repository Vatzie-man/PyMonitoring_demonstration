import tkinter as tk
from tkinter import ttk
from db_items import (
    get_options,
    update_item,
)


class Model:

    def __init__(self):
        self.get_options = get_options
        self.update_item = update_item

    def update_options_text(self, options):
        for option, state in options.items():
            if isinstance(state, tk.BooleanVar):
                state = bool(state.get())
            self.update_item(option, state)

    def update_radio_choice(self, radio_choice):
        if isinstance(radio_choice, tk.StringVar):
            self.update_item("display_mode", radio_choice.get())

    def update_combo_choice(self, combo_choice):
        if isinstance(combo_choice, tk.StringVar):
            self.update_item("time_delay", combo_choice.get())

    def get_options(self):
        options = self.get_options()
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

        options_list: list = list()
        for x in range(len(options)):
            options_list.append((options[x].option, options[x].state))

        for row in options_list:
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
