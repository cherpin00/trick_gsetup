import tkinter as tk
from tkinter import BooleanVar, Button, Checkbutton, Entry, Frame, Label, LabelFrame, ttk, filedialog
from tkinter.constants import END
from abc import ABC, ABCMeta, abstractmethod
import json

from util import run

class Configure:
    def __init__(self, configs):
        self.program = "/home/cherpin/git/trick/configure" #TODO: use configure in the right directory
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

class ConfigOption(metaclass=ABCMeta):
    def __init__(self, name:str, config:dict):
        self.config = config
        self.name = name
        self.type = config["type"]
        self.value = config.get("value", "") 
        if type(self.value) == str:
            self.value = self.value.lower() #Make sure all strings are lower for comparison
        self.label = config.get("label", self.name)
        self.desc = config.get("desc", "No help given.")
        self.section = config.get("section", "general")
    
    @abstractmethod
    def get_value(self):
        pass

    @abstractmethod
    def get_type(self):
        pass
    
    @abstractmethod
    def get_label(self):
        pass
    
    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_desc(self):
        pass

    @abstractmethod
    def get_section(self):
        pass
    
    def get_dict(self):
        d= {}
        for attribute in dir(self):
            if callable(getattr(self, attribute)):
                if attribute[:3] == "get" and attribute != "get_dict":
                    d[attribute[4:]] = getattr(self, attribute)()
        self.config = d
        return d
    


class ConfigBool(ConfigOption):
    def __init__(self, frame, name: str, config: dict):
        super().__init__(name, config)
        self.frame = frame
        self.bool = BooleanVar(value=self.value)
        self.check_button = Checkbutton(self.frame, text=self.label, variable=self.bool)
        self.check_button.pack(side="left")
        self.desc = Label(self.frame, text = self.desc) #TODO: Make a pop up
        self.desc.pack(side="left")
    
    def get_value(self):
        return self.bool.get()
    
    def get_type(self):
        return self.type
    
    def get_label(self):
        return self.label
    
    def get_name(self):
        return self.name
    
    def get_desc(self):
        return self.desc.cget("text")
    
    def get_section(self):
        return self.section
        
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
    
    def get_type(self):
        return self.type
    
    def get_label(self):
        return self.label.cget("text")
    
    def get_name(self):
        return self.name
    
    def get_desc(self):
        return self.desc.cget("text")
    
    def get_section(self):
        return self.section
        
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
        if config["type"] == "dir": #TODO: Think about these each being a diffrent class
            self.config = ConfigDir(self.frame, config["name"], config)
        elif config["type"] == "bool":
            self.config = ConfigBool(self.frame, config["name"], config)
        else:
            raise RuntimeError(f"Unsupported configuration type {self.config.type}")

    
    def get_frame(self):
        return self.frame
    
    def get_configOption(self):
        return self.config

class App:
    def __init__(self):
        self.filename = "config.json"
        self.root = tk.Tk()
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=1, pady=15)

        self.components = {}
        self.frames = {}
        
        # self.install_dirs = Frame(self.notebook)
        # self.optional_features = Frame(self.notebook)
        
        # self.install_dirs.pack(fill = "both", expand=1)
        # self.optional_features.pack(fill = "both", expand=1)

        self.read_config()
        # self.components["dir"] = Option(parent=self.install_dirs, config=config["bindir"])
        # self.components["dir"].get_frame().pack(fill="x")
        
        # config["enable-java"]["name"] = 'enable-java'
        # self.components["java"] = Option(parent=self.optional_features, config=config["enable-java"])
        # self.components["java"].get_frame().pack(fill = "x")

        self.done_button = Button(self.root, text="Done", command=self.done)
        self.done_button.pack(side="right")

        # self.notebook.add(self.install_dirs, text="install directories")
        # self.notebook.add(self.optional_features, text="optional features")

        self.root.mainloop()
    
    def write_config(self):
        d = self.get_config_dicts()
        with open(self.filename, "w") as f:
            f.write(json.dumps(d, indent=4))

    def read_config(self):
        with open(self.filename, "r") as f:
            options = json.load(f)
        for c in options: #TODO: Load into an option class first
            c = Option(config=c).get_configOption()
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

    def get_config_objects(self):
        config = []
        for key in self.components:
            option = self.components[key].get_configOption()
            config.append(option)
        return config

    def get_config_dicts(self):
        config_dicts = []
        for key in self.components:
            option = self.components[key].get_configOption()
            config_dicts.append(option.get_dict())
        return config_dicts

    def done(self):
        self.write_config()
        self.read_config()
        configs = self.get_config_objects()
        cmd = Configure(configs).get_command()
        p = run(cmd)
        print("stdout:", p.stdout)
        print("stderr:", p.stderr)
        

        
    

if __name__ == "__main__":
    App()