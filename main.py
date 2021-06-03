import tkinter as tk
from tkinter import BooleanVar, Button, Checkbutton, Entry, Frame, Label, LabelFrame, Radiobutton, StringVar, ttk, filedialog, messagebox, Canvas, Scrollbar
from tkinter.constants import END
from abc import ABC, ABCMeta, abstractmethod
import json
import logging
from pprint import pprint

from util import run

class Configure:
    def __init__(self, configs):
        self.program = "/home/cherpin/git/trick/configure" #TODO: use configure in the right directory
        self.configs = configs
    
    def get_command(self):
        sep = " "
        command = self.program
        for config in self.configs:
            value = config.get_value()
            type = config.get_type()
            if value != "" and value != "no":
                command += f"{sep}--{config.get_name()}"
                if type != "flag":
                    command += f"={value}"
        return command

config = { 
    "bindir" : {
        "type" : "dir",
        "value" : "/usr/bin",
        "label" : "Enter your binary directory",
        "name" : "bindir",
        "desc" : "Enter your bin directory"
    },
    "enable-java" : {
        "type" : "bool",
        "value" : "true",
        "name" : "enable-java"
    }
}

class ConfigOption(metaclass=ABCMeta):
    def __init__(self, name:str, config:dict, special_valid_params = [], special_required_params=[]):
        self.config = config
        self.name = name
        self.valid_params = ["type", "value", "label", "desc", "section", "name"] + special_valid_params
        self.required_params = ["name", "type"] + special_required_params
        self.params = []

        for p in self.required_params:
            if p not in config:
                raise RuntimeError(f"Param {p} is required and not found in params")
        
        for key in config:
            if key not in self.valid_params:
                raise RuntimeError(f"Param {key} is not a valid param. Valid params are {self.valid_params}.")
            setattr(self, key, config[key])
            self.params.append(key)
        
        self.value = config.get("value", "") 
        if type(self.value) == str:
            self.value = self.value.lower() #Make sure all strings are lower for comparison
        self.label = config.get("label", self.name)
        self.desc = config.get("desc", "No help given.")
        self.section = config.get("section", "general")
    
    def get_dict(self):
        d = {}
        for attribute in self.params:
            try:
                d[attribute] = getattr(self, f"get_{attribute}")()
            except:
                logging.warning("No getter implementation useing set property!")
                d[attribute] = getattr(self, attribute)
        self.config = d
        return d
    
    #NOTE: Only the attributes that are not shown on the gui have getters here because they do not require special handling because they do not have tkinter widgets.
    def get_name(self):
        return self.name
    
    def get_section(self):
        return self.section
    
    def get_type(self):
        return self.type
    


class ConfigBool(ConfigOption):
    def __init__(self, frame, name: str, config: dict):
        super().__init__(name, config, special_required_params=["value"])
        self.frame = frame
        self.bool = BooleanVar(value=self.value)
        self.check_button = Checkbutton(self.frame, text=self.label, variable=self.bool)
        self.check_button.pack(side="left")
        self.desc = Label(self.frame, text = self.desc) #TODO: Make a pop up
        self.desc.pack(side="left")
    
    def get_value(self):
        return "yes" if self.bool.get() else "no"
        
    def get_desc(self):
        return self.desc.cget("text")
    

class ConfigRadio(ConfigOption):
    def __init__(self, frame, name: str, config: dict):
        super().__init__(name, config, special_valid_params=["options"])
        self.frame = frame
        
        self.label = ttk.Label(self.frame, text=self.label)
        self.label.pack(side="left")

        self.inner_frame = LabelFrame(self.frame)
        self.inner_frame.pack(side="left")
        self.option = StringVar()
        self.options = []
        for o in config["options"]:
            self.options.append(Radiobutton(self.inner_frame, text=o, variable=self.option, value=o))
            self.options[-1].pack(anchor="w")
        self.desc = Label(self.frame, text = self.desc) #TODO: Make a pop up
        self.desc.pack(side="left")
    
    def get_value(self):
        return self.option.get()
    
    def get_options(self):
        r = []
        for x in self.options:
            r.append(x.cget("text"))
        return r
        
        
class ConfigDir(ConfigOption):
    def __init__(self, frame, name: str, config: dict):
        super().__init__(name, config)
        self.frame = frame
        self.label = ttk.Label(self.frame, text=self.label)
        self.label.pack(side="left")
        self.directory_entry = ttk.Entry(self.frame)
        self.directory_entry.insert(0, self.value)
        self.directory_entry.pack(side="left")
        self.browse_button = ttk.Button(self.frame, text="browse", command=self.browse_dir)
        self.browse_button.pack(side="left")
        self.desc = ttk.Label(self.frame, text = self.desc) #TODO: Make a pop up
        self.desc.pack(side="left")
    
    def get_value(self): #TODO: Validate directory
        return self.directory_entry.get()
    
    def get_label(self):
        return self.label.cget("text")
    
    def get_desc(self):
        return self.desc.cget("text")
    
    def browse_dir(self):
        dir = filedialog.askdirectory()
        self.directory_entry.delete(0, END)
        self.directory_entry.insert(0, dir)

class Option:
    def __init__(self, parent=None, config={"label" : "default-label"}):
        if not parent:
            self.parent = Frame()
        else:
            self.parent = parent

        self.frame = LabelFrame(self.parent)
        if config["type"] == "dir": 
            self.config = ConfigDir(self.frame, config["name"], config)
        elif config["type"] == "bool":
            self.config = ConfigBool(self.frame, config["name"], config)
        elif config["type"] == "radio":
            self.config = ConfigRadio(self.frame, config["name"], config)
        elif config["type"] == "flag":
            self.config = ConfigBool(self.frame, config["name"], config)
        else:
            type = config["type"]
            raise RuntimeError(f"Unsupported configuration type {type}")

    
    def get_frame(self):
        return self.frame
    
    def get_configOption(self):
        return self.config

class App:
    def __init__(self):
        self.filename = "config.json"
        self.root = tk.Tk()
        self.root.geometry("500x500")

        self.done_button = Button(self.root, text="Done", command=self.done)
        self.done_button.pack(side="bottom", anchor="e")

        self.root = self.get_scrollable_frame(self.root, "y")

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=1, pady=15)

        self.components = {}
        self.frames = {}
        
        self.read_config()
        
        self.root.mainloop()
    
    

    def write_config(self):
        d = self.get_config_dict()
        with open(self.filename, "w") as f:
            f.write(json.dumps(d, indent=4))

    def read_config(self):
        with open(self.filename, "r") as f:
            options = json.load(f) #TODO: Implement nested dictinary in config.json parse here
        if type(options) == list: #TODO: Either update or depcricate list option
            for c in options:
                c = Option(config=c).get_configOption() #Create an object here so we can compare with existing objects
                make = True
                if self.components.get(c.get_name()):
                    if self.components[c.get_name()].get_configOption().get_dict() != c.get_dict():
                        self.components[c.get_name()].get_frame().destroy()
                    else:
                        make = False
                else:
                    if not self.frames.get(c.get_section()):
                        self.frames[c.get_section()] = Frame(self.notebook)
                        self.frames[c.get_section()] = Frame(self.notebook)
                        self.frames[c.get_section()].pack(fill = "both", expand=1)
                        self.notebook.add(self.frames[c.get_section()], text=c.get_section())
                if make:
                    self.components[c.get_name()] = Option(parent=self.frames[c.get_section()], config=c.get_dict())
                    self.components[c.get_name()].get_frame().pack(fill="x")
        elif type(options) == dict:
            for section in options:
                if not self.frames.get(section):
                    self.frames[section] = Frame(self.notebook)
                    self.frames[section] = Frame(self.notebook)
                    self.frames[section].pack(fill = "both", expand=1)
                    self.notebook.add(self.frames[section], text=section)
                for c in options[section]:
                    c = Option(config=c).get_configOption() #Create an object here so we can compare with existing objects
                    make = True
                    if self.components.get(c.get_name()):
                        if self.components[c.get_name()].get_configOption().get_dict() != c.get_dict():
                            self.components[c.get_name()].get_frame().destroy()
                        else:
                            make = False
                    if make:
                        self.components[c.get_name()] = Option(parent=self.frames[section], config=c.get_dict())
                        self.components[c.get_name()].get_configOption().section = section
                        self.components[c.get_name()].get_frame().pack(fill="x")
    
    def get_config_objects(self):
        config = []
        for key in self.components:
            option = self.components[key].get_configOption()
            config.append(option)
        return config

    def get_config_dict(self):
        config_dict = {}
        for section in self.frames: #TODO: Fix this n**2 solution by makeing self.frames a dictinary containing arrays
            config_dict[section] = []
            for key in self.components:
                if self.components[key].get_configOption().get_section() == section:
                    option = self.components[key].get_configOption()
                    config_dict[section].append(option.get_dict())
        return config_dict

    def done(self):
        self.write_config()
        self.read_config()
        configs = self.get_config_objects()
        cmd = Configure(configs).get_command()
        p = run(cmd)
        pprint(p.stdout.decode())
        if len(p.stderr) > 0:
            print("stderr:", p.stderr)
            messagebox.showerror("Configure error", p.stderr.decode())

    def get_scroll_bar(self, main_frame, my_canvas, axis):
    #Add a scrollbar to canvas
        if axis == "x" or axis == "both":
            raise RuntimeError("x scrollbar not implemented yet.")
            my_scrollbar = Scrollbar(main_frame, orient="horizontal", command=my_canvas.xview)
            my_scrollbar.pack(side="bottom", fill="x")
            # my_scrollbar.grid(row=100, column=0, sticky="ns", fill="x")
            my_canvas.configure(xscrollcommand=my_scrollbar.set)
            my_canvas.bind("<Configure>", lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))
            def _on_mouse_wheel(event):
                my_canvas.xview_scroll(-1 * int((event.delta / 120)), "units")

            my_canvas.bind_all("<MouseWheel>", _on_mouse_wheel)
        if axis == "y" or axis == "both":
            #Add a scrollbar to canvas
            my_scrollbar = Scrollbar(main_frame, orient="vertical", command=my_canvas.yview)
            my_scrollbar.pack(side="right", fill="y")
            # my_scrollbar.grid(row=0, column=100, fill = "y")
            my_canvas.configure(yscrollcommand=my_scrollbar.set)
            my_canvas.bind("<Configure>", lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))
            def _on_mouse_wheel(event):
                my_canvas.yview_scroll(-1 * int((event.delta / 120)), "units")

            my_canvas.bind_all("<MouseWheel>", _on_mouse_wheel)
        #TODO: put error here if of the options above

        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
            
    def get_scrollable_frame(self, parent, axis):
    #Create a Main Frame
        main_frame = Frame(parent)
        main_frame.pack(fill="both", expand=True)

        #Create  Canvas
        my_canvas = Canvas(main_frame)
        my_canvas.pack(fill="both", expand=True, side="left")
        # my_canvas.grid(row=0, column=0, sticky="nsew")

        self.get_scroll_bar(main_frame, my_canvas, axis)

        #Create another frame inside the canvas
        second_frame = Frame(my_canvas)

        #Add new frame to window in canvas
        my_canvas.create_window((0,0), window=second_frame, anchor="nw")
        return second_frame
        
    

if __name__ == "__main__":
    App()