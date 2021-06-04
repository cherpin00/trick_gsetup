from abc import abstractproperty
import tkinter as tk
from tkinter import *
from tkinter import ttk
import json
from collections import namedtuple
import pickle
from tkinter import filedialog
from pprint import pprint
from tkinter.ttk import Notebook

class Data:
    def __init__(self, **kargs) -> None:
        for key, value in kargs.items():
            if type(value) != dict:
                setattr(self, key, value)
            else:
                setattr(self, key, Data(**value))
    
    def _dict_(self):
        d = {}
        for attribute in dir(self):
            if not attribute.startswith("_"):
                var = getattr(self, attribute)
                if type(var) == Data:
                    d[attribute] = var._dict_()
                else:
                    d[attribute] = var
        return d

class Component:
    def __init__(self, parent, name, source, special_valid_params, special_required_params) -> None:
        self.parent = parent
        self.frame = Frame(parent)
        self.name = name
        self.source = source
        

        self.params = [x for x in dir(self.source) if not x.startswith("_")]
        self.required_params = special_required_params
        self.valid_params = special_valid_params

        for p in self.required_params:
            if p not in self.params:
                raise RuntimeError(f"Parameter {p} is required and not found in object '{source}.{name}'")
        
        for key in self.params:
            if key not in self.valid_params:
                raise RuntimeError(f"Parameter '{key}' in '{source}.{name}' is not a valid param. Valid params are {self.valid_params}.")
            setattr(self, key, getattr(self.source, key))
        
        for key in list(set(self.params).symmetric_difference(set(self.valid_params))):
            setattr(self, key, "default")
            self.params.append(key)
        
        @abstractproperty
        def source_attribute(self):
            pass

class Option(Component):
    def __init__(self, parent, section, name, data, special_valid_params = [], special_required_params=[]) -> None:
        self.source_attribute = "value"
        required_params = ["type"]
        valid_params = ["type", "value", "label", "desc"]
        super().__init__(parent, name, getattr(getattr(getattr(getattr(data, "sections"), section), "options"), name), special_required_params=special_required_params + required_params, special_valid_params=special_valid_params + valid_params)

    @property
    def value(self):
        return getattr(self.source, self.source_attribute)
    
    @value.setter
    def value(self, value):
        setattr(self.source, self.source_attribute, value)
        
    def get_frame(self):
        return self.frame



class OptionDir(Option):
    def __init__(self, parent, section, name, data):
        super().__init__(parent, section, name, data, special_valid_params=["width"])
        # Setting defaults
        self.width = 10 if self.width == "default" else self.width

        #Building GUI
        self.label = Label(self.get_frame(), text=self.label)
        self.label.pack(side="left")
        self.directory_entry = Entry(self.get_frame(), width=self.width)
        self.directory_entry.bind('<KeyRelease>', self.handler)
        self.directory_entry.insert(0, self.value)
        self.directory_entry.pack(side="left")
        self.browse_button = Button(self.get_frame(), text="browse", command=self.browse_dir)
        self.browse_button.pack(side="right")
        self.desc = Label(self.get_frame(), text = self.desc) #TODO: Make a pop up
        self.desc.pack(side="left")
    
    def handler(self, event):
        print(f"Setting value to {self.directory_entry.get()}")
        self.value = self.directory_entry.get()
    
    def browse_dir(self):
        dir = filedialog.askdirectory()
        self.directory_entry.delete(0, END)
        self.directory_entry.insert(0, dir)

class OptionBool(Option):
    def __init__(self, parent, section, name, data):
        super().__init__(parent ,section, name, data)
        #Setting defaults
        self.value = "no" if self.value == "default" else self.value

        #Building GUI
        self.bool = BooleanVar(value = self.value)
        self.check_button = Checkbutton(self.get_frame(), text=self.label, command=self.handler, variable=self.bool)
        self.check_button.pack(side="left")
        self.desc = Label(self.get_frame(), text = self.desc) #TODO: Make a pop up
        self.desc.pack(side="left")
    
    def handler(self):
        print(f"Setting value to {self.bool.get()}.")
        self.value = "yes" if self.bool.get() else "no"

class Section(Component):
    def __init__(self, parent, section, data): #TODO: Figure out if I can pass in data instead of making it global
        valid_params = ["options", "size"] #TODO: Use size or take it out of valid params
        required_params = ["options"]
        super().__init__(parent, section, getattr(getattr(data, "sections"), section), special_valid_params=valid_params, special_required_params=required_params)
    
        self.components = {}
        self.frame = Frame(parent)
        # self.frame.pack(fill="both", expand = 1) #TODO: Not sure if this is needed
        if type(parent) == Notebook:
            parent.add(self.get_frame(), text=section)
        
        options = getattr(self.source, "options")._dict_()
        for option in options:
            obj = getattr(getattr(self.source, "options"), option)
            my_type = obj.type
            if my_type == "dir":
                self.components[option] = OptionDir(self.get_frame(), section, option, data)
            elif my_type == "bool":
                self.components[option] = OptionBool(self.get_frame(), section, option, data)
            else:
                raise RuntimeError(f"Option {my_type} is not implemented yet.")
            
            self.components[option].get_frame().pack()
    
    def get_frame(self):
        return self.frame
    
class App(Component):
    def __init__(self, data):
        self.root = tk.Tk()
        super().__init__(self.root, "app", data, special_required_params=["sections"], special_valid_params=["sections"])
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=1)    

        self.sections = {}
        sections = getattr(self.source, "sections")._dict_()
        for section in sections:
            obj = getattr(getattr(self.source, "sections"), section)
            self.sections[section] = Section(notebook, section, data)
            # self.sections[section].get_frame().pack(fill="both", expand=1)
    
    def get_frame(self):
        return self.root
        

class Control():
    def __init__(self, my_json):
        data = Data(**my_json)
        pprint(data._dict_())
        App(data)
        pprint(data._dict_())
    
    def start():
        App.get_frame().mainloop()

#individual tests
    # root = tk.Tk()
    # notebook = ttk.Notebook(root)
    # notebook.pack(fill="both", expand=1)

    # Section(notebook, "test_cases")
    ## OptionDir(sec, "test_cases", "option_name0").get_frame().pack()
    ## OptionDir(sec, "test_cases", "option_name1").get_frame().pack()
    ## OptionDir(sec, "test_cases", "option_name2").get_frame().pack()

    ## OptionBool(sec, "test_cases", "option_name3").get_frame().pack()
    ## OptionBool(sec, "test_cases", "option_name4").get_frame().pack()
    ## OptionBool(sec, "test_cases", "option_name5").get_frame().pack()

    # root.mainloop()

if __name__ == "__main__":
    my_json = {
            "sections" : {
                "test_cases" : {
                    "size" : 12,
                    "options" : {
                        "option_name0" : {
                            "type" : "dir",
                            "value" : "/home/cherpin",
                        },
                        "option_name1" : {
                            "type" : "dir",
                            "value" : "/home/cherpin",
                            "width" : 20
                        },
                        "option_name2" : {
                            "type" : "dir",
                            "width" : 20
                        },
                        "option_name3" : {
                            "type" : "bool",
                        },
                        "option_name4" : {
                            "type" : "bool",
                        },
                        "option_name5" : {
                            "type" : "bool",
                        }
                    }
                }, 
            }
        }
    data = Data(**my_json)
    pprint(data._dict_())
    App().get_frame().mainloop()
    pprint(data._dict_())
    # Control(my_json).start()

