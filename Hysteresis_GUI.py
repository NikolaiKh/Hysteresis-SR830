import tkinter as tk
from tkinter import filedialog, messagebox
import os
import random
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from pymeasure.instruments.srs import SR830
import pyvisa
import re

class GraphApp:
    def __init__(self, master):
        self.master = master
        master.title("Hysteresis App")
       # master.columnconfigure(1, weight=1)

        self.gpib_adres_label = tk.Label(master, text="GPIB adres of LIA:")
        self.gpib_adres_entry = tk.Entry(master)
        self.filename_label = tk.Label(master, text="File Name:")
        self.filename_entry = tk.Entry(master)
        self.select_folder_button = tk.Button(master, text="Select Folder", command=self.select_folder)
        self.folder_path_label = tk.Label(master, text="Selected Folder Path: ")

        self.min_label = tk.Label(master, text="Min Field:")
        self.min_entry = tk.Entry(master)
        self.max_label = tk.Label(master, text="Max Field:")
        self.max_entry = tk.Entry(master)
        self.step_label = tk.Label(master, text="Step Field:")
        self.step_entry = tk.Entry(master)
        self.wait_label = tk.Label(master, text="Wait Time (msec):")
        self.wait_entry = tk.Entry(master)

        self.num_averages_label = tk.Label(master, text="Num of Averages:")
        self.num_averages_entry = tk.Entry(master)

        self.save_checkbox_value = tk.BooleanVar(value=True)
        self.save_checkbox = tk.Checkbutton(master, text="Save?", variable=self.save_checkbox_value)
        self.demag_checkbox_value = tk.BooleanVar(value=False)
        self.demag_checkbox = tk.Checkbutton(master, text="Make demagnetisation?", variable=self.demag_checkbox_value)
        self.save_button = tk.Button(master, text="Save", command=self.save)
        self.start_button = tk.Button(master, text="Start", command=self.start)
        self.stop_button = tk.Button(master, text="Stop", command=self.stop)
        self.demagnetization_button = tk.Button(master, text="Demagnetization", command=self.demagnetization)

        self.demagnetization_label = tk.Label(master, text="")

        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)

        # file name and save path
        self.select_folder_button.grid(row=0, column=0, sticky="e", padx=10, pady=5)
        self.folder_path_label.grid(row=0, column=1, columnspan=2, sticky="w", padx=10, pady=5)
        self.filename_label.grid(row=1, column=0, sticky="e", padx=10, pady=5)
        self.filename_entry.grid(row=1, column=1, columnspan=2, sticky="w", padx=10, pady=5)
        # magnetic filed changes
        self.min_label.grid(row=2, column=0, sticky="e", padx=10, pady=5)
        self.min_entry.grid(row=2, column=1, columnspan=2, sticky="w", padx=10, pady=5)
        self.max_label.grid(row=3, column=0, sticky="e", padx=10, pady=5)
        self.max_entry.grid(row=3, column=1, columnspan=2, sticky="w", padx=10, pady=5)
        self.step_label.grid(row=4, column=0,  sticky="e", padx=10, pady=5)
        self.step_entry.grid(row=4, column=1, columnspan=2, sticky="w",padx=10, pady=5)
        # time waiting constant
        self.wait_label.grid(row=5, column=0, sticky="e", padx=10, pady=5)
        self.wait_entry.grid(row=5, column=1, columnspan=2, sticky="w", padx=10, pady=5)
        # number of averages
        self.num_averages_label.grid(row=6, column=0, sticky="e", padx=10, pady=5)
        self.num_averages_entry.grid(row=6, column=1, columnspan=2, sticky="w", padx=10, pady=5)

        self.save_checkbox.grid(row=7, column=0, sticky="e", padx=10, pady=5)
        self.demag_checkbox.grid(row=7, column=1, columnspan=2, sticky="w", padx=10, pady=5)
        self.save_button.grid(row=8, column=0, sticky="e", padx=10, pady=5)
        self.demagnetization_button.grid(row=8, column=1,  sticky="w", padx=10, pady=5)
        self.start_button.grid(row=9, column=0, padx=10, pady=5)
        self.stop_button.grid(row=9, column=1, padx=10, pady=5)

        self.gpib_adres_label.grid(row=10, column=0, sticky="e", padx=10, pady=5)
        self.gpib_adres_entry.grid(row=10, column=1, columnspan=2, sticky="w", padx=10, pady=5)
        self.demagnetization_label.grid(row=10, column=3, sticky="e", padx=10, pady=5)

        self.canvas.get_tk_widget().grid(row=11, columnspan=2, padx=10, pady=5)

        self.filename_entry.insert(0, "test")
        self.min_entry.insert(0, "-1")
        self.max_entry.insert(0, "1")
        self.step_entry.insert(0, "0.2")
        self.wait_entry.insert(0, "200")
        self.num_averages_entry.insert(0, "1")
        self.gpib_adres_entry.insert(0, "8")

        self.all_field_volts_values = []
        self.all_sigX_values = []
        self.all_sigY_values = []
        self.is_running = False

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        self.folder_path_label.config(text="Selected Folder Path: " + folder_path)

    def get_folder_path(self):
        return self.folder_path_label.cget("text").replace("Selected Folder Path: ", "")

    def save(self):
        # save the file with average values
        filename = self.filename_entry.get()
        folder_path = self.get_folder_path()

        if not filename:
            messagebox.showerror("Error", "Please enter a file name.")
            return

        file_path = os.path.join(folder_path, filename + ".dat")

        if os.path.isfile(file_path):
            overwrite = messagebox.askyesno("File Exists", "The file already exists. Do you want to overwrite it?")
            if not overwrite:
                return

        field_volts = self.all_field_volts_values[0]
        avg_sigX_values = [sum(sigX_values) / len(sigX_values) for sigX_values in zip(*self.all_sigX_values)]
        avg_sigY_values = [sum(sigY_values) / len(sigY_values) for sigY_values in zip(*self.all_sigY_values)]

        with open(file_path, "w") as file:
            for volts, sig_x, sig_y in zip(field_volts, avg_sigX_values, avg_sigY_values):
                file.write(f"{volts}\t{sig_x}\t{sig_y}\n")

        messagebox.showinfo("Save", "File saved successfully.")

    def start(self):

        if self.is_running:
            return

        if not hasattr(self, 'lockin'):
            self.lia_init()

        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        # filename = self.filename_entry.get()
        min_field = float(self.min_entry.get())
        max_field = float(self.max_entry.get())
        step_field = float(self.step_entry.get())
        wait_time = int(self.wait_entry.get())
        num_averages = int(self.num_averages_entry.get())
        # folder_path = self.get_folder_path()
        self.ax.clear()
        self.ax.set_xlabel("Magnetic field (V)")
        self.ax.set_ylabel("Lock-in signal (V)")
        self.fig.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()

        self.all_field_volts_values = []
        self.all_sigX_values = []
        self.all_sigY_values = []

        for iteration in range(num_averages):
            field_volts_values = []
            sigX_values = []
            sigY_values = []
            self.demagnetization_label.config(text=str("Current iteration " + str(iteration+1)))
            self.master.update()
            if self.demag_checkbox_value.get():
                self.demagnetization()

            field = min_field
            direction = 1
            self.lia_getXY()
            while min_field <= field <= max_field:
                if not self.is_running:
                    return
                # go in positive direction
                field_volts_values.append(field)
                self.lia_set_aux_out_1(field)
                time.sleep(wait_time / 1000)
                sigX, sigY = self.lia_getXY()
                sigX_values.append(sigX)
                sigY_values.append(sigY)

                self.ax.set_xlim(min_field - step_field, max_field + step_field)
                self.ax.plot(field_volts_values, sigX_values, color='red', label='X channel')
                # self.ax.plot(field_volts_values, sigY_values, color='blue', label='Y channel')

                self.ax.set_xlabel("Magnetic field (V)")
                self.ax.set_ylabel("Lock-in signal (V)")
                self.fig.tight_layout()
                self.canvas.draw()
                self.canvas.flush_events()
                field += step_field * direction

            direction *= -1  # change the direction
            field += step_field * direction

            while min_field <= field <= max_field:
                if not self.is_running:
                    return
                # go in positive direction
                field_volts_values.append(field)
                self.lia_set_aux_out_1(field)
                time.sleep(wait_time / 1000)
                sigX, sigY = self.lia_getXY()
                sigX_values.append(sigX)
                sigY_values.append(sigY)

                self.ax.set_xlim(min_field - step_field, max_field + step_field)
                self.ax.plot(field_volts_values, sigX_values, color='red', label='X channel')
                # self.ax.plot(field_volts_values, sigY_values, color='blue', label='Y channel')

                self.ax.set_xlabel("Magnetic field (V)")
                self.ax.set_ylabel("Lock-in signal (V)")
                self.fig.tight_layout()
                self.canvas.draw()
                self.canvas.flush_events()
                field += step_field * direction

            self.all_field_volts_values.append(field_volts_values)
            self.all_sigX_values.append(sigX_values)
            self.all_sigY_values.append(sigY_values)
            for field_volts_values, y_values in zip(self.all_field_volts_values, self.all_sigX_values):
                self.ax.plot(field_volts_values, y_values, color='lightgray')
            # for field_volts_values, y_values in zip(self.all_field_volts_values, self.all_sigY_values):
            #     self.ax.plot(field_volts_values, y_values, color='lightgray')

        self.lia_set_aux_out_1(0)
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.is_running = False

        if self.save_checkbox_value.get():
            self.save()

    def stop(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def demagnetization(self):
        if not hasattr(self, 'lockin'):
            self.lia_init()

        values = [-7, 6.5, -6, -5.5, 5, -4.5, 4, -3.5, 3, -2.5, 2, -1.5, 1, -0.5, 0.25, -0.125, 0]
        for value in values:
            self.lia_set_aux_out_1(value)
            self.demagnetization_label.config(text=str(value))
            self.master.update()
            time.sleep(0.5)

    def lia_getXY(self):
        # get X Y signals from SR844
        out_out_signal = self.lockin.query("SNAP? 1,2")
        signal = out_out_signal.split(",")
        sigX = float(signal[0])
        sigY = float(signal[1])
        return sigX, sigY

    def lia_set_aux_out_1(self, voltage):
        if self.lockin_model == 844: # check the model number
            # set aux_out_1 voltage to SR844
            self.lockin.write("AUXO 1, " + str(voltage))  # !!!! SR844 command. SR830 has another string
        elif self.lockin_model == 830:  # check the model number
            self.lockin.write("AUXV 1, " + str(voltage))  #SR830

    def lia_init(self):
        #  connect to SR lock-in
        rm = pyvisa.ResourceManager()
        adr = self.gpib_adres_entry.get()
        self.lockin = rm.open_resource(f'GPIB0::{adr}::INSTR')
        # get SR name and model (830 / 844). It is important for aux_out !!!!
        self.lockinname = self.lockin.query("*IDN?")
        match = re.search(r"SR(\d{3})", self.lockinname)
        self.lockin_model = int(match.group(1))
        print(self.lockinname)
        self.demagnetization_label.config(text=str(self.lockinname))
        self.master.update()


root = tk.Tk()
app = GraphApp(root)
root.mainloop()
