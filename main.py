import tkinter as tk
from tkinter import BooleanVar, Button, Checkbutton, Entry, Frame, Label, LabelFrame, ttk, filedialog
from tkinter.constants import END
from abc import ABC

class Configure:
    def __init__(self, configs):
        self.program = "configure"
        self.configs = configs
    
    def get_command(self):
        sep = " "
        command = self.program
        for config in self.configs:
            command += f"{sep}--{config.get_name()}={config.get_value()}"
        return command

config = {  #TODO: This should get put into an object to error check
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

class ConfigOption(ABC):
    def __init__(self, name:str, config:dict):
        self.name = name
        self.type = config["type"]
        self.value = config.get("value", "") 
        if type(self.value) == str:
            self.value = self.value.lower() #Make sure all strings are lower for comparison
        self.label = config.get("label", self.name)
        self.desc = config.get("desc", "No help given.")
    
    def get_value(self):
        return self.value

    def get_type(self):
        return self.type

    def get_label(self):
        return self.label

    def get_name(self):
        return self.name

class ConfigBool(ConfigOption):
    def __init__(self, frame, name: str, config: dict):
        super().__init__(name, config)
        self.frame = frame
        self.bool = BooleanVar(value=True if self.value == "true" else False)
        self.check_button = Checkbutton(self.frame, text=self.label, variable=self.bool)
        self.check_button.pack(side="left")
        self.help = Label(self.frame, text = self.desc) #TODO: Make a pop up
        self.help.pack(side="left")
    
    def get_value(self):
        return self.bool.get()
        
class ConfigDir(ConfigOption):
    def __init__(self, frame, name: str, config: dict):
        super().__init__(name, config)
        self.frame = frame
        self.label = Label(self.frame, text=self.label)
        self.label.pack(side="left")
        self.directory_entry = Entry(self.frame)
        self.directory_entry.insert(0, self.value)
        self.directory_entry.pack(side="left")
        self.browse_button = Button(self.frame, text="browse", command=self.browse_dir)
        self.browse_button.pack(side="left")
        self.help = Label(self.frame, text = self.desc) #TODO: Make a pop up
        self.help.pack(side="left")
    
    def get_value(self): #TODO: Validate directory
        return self.directory_entry.get()
    
    def browse_dir(self):
        dir = filedialog.askdirectory()
        self.directory_entry.delete(0, END)
        self.directory_entry.insert(0, dir)

class Option:
    def __init__(self, parent=None, config={"label" : "default-label"}):
        if not parent:
            self.parent = tk.Tk()
        else:
            self.parent = parent

        self.frame = LabelFrame(self.parent)
        if config["type"] == "dir": #TODO: Think about these each being a diffrent class
            self.config = ConfigDir(self.frame, config["name"], config)
        elif config["type"] == "bool":
            self.config = ConfigBool(self.frame, config["name"], config)
        else:
            raise RuntimeError(f"Unsupported configuration type {self.config.type}")

        if not parent:
            self.frame.pack()
            self.parent.mainloop()
    
    def get_frame(self):
        return self.frame
    
    def get_configOption(self):
        return self.config

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=1, pady=15)

        self.components = {}
        
        self.install_dirs = Frame(self.notebook)
        self.optional_features = Frame(self.notebook)
        
        self.install_dirs.pack(fill = "both", expand=1)
        self.optional_features.pack(fill = "both", expand=1)

        self.components["dir"] = Option(parent=self.install_dirs, config=config["bindir"])
        self.components["dir"].get_frame().pack(fill="x")
        
        config["enable-java"]["name"] = 'enable-java'
        self.components["java"] = Option(parent=self.optional_features, config=config["enable-java"])
        self.components["java"].get_frame().pack(fill = "x")

        self.done_button = Button(self.root, text="Done", command=self.done)
        self.done_button.pack(side="right")

        self.notebook.add(self.install_dirs, text="install directories")
        self.notebook.add(self.optional_features, text="optional features")

        self.root.mainloop()
    
    def done(self):
        config = []
        for key in self.components:
            config.append(self.components[key].get_configOption())
        print(Configure(config).get_command())

        
    

if __name__ == "__main__":
    App()