from abc import abstractproperty
import tkinter as tk
from tkinter import *
from tkinter import ttk
import json
from tkinter import filedialog
from tkinter.ttk import Notebook
import subprocess
from tkinter import messagebox
import logging
from tkinter.scrolledtext import ScrolledText
import traceback
import os


#TODO: Write test case for this function
def QuoteForPOSIX(string): #Adapted from https://code.activestate.com/recipes/498202-quote-python-strings-for-safe-use-in-posix-shells/
    '''quote a string so it can be used as an argument in a  posix shell

       According to: http://www.unix.org/single_unix_specification/
          2.2.1 Escape Character (Backslash)

          A backslash that is not quoted shall preserve the literal value
          of the following character, with the exception of a <newline>.

          2.2.2 Single-Quotes

          Enclosing characters in single-quotes ( '' ) shall preserve
          the literal value of each character within the single-quotes.
          A single-quote cannot occur within single-quotes.

    '''

    return "\\'".join("'" + p + "'" for p in string.split("'"))

def get_configure_command(comand, config_json):
    sep = " "
    for section_name, section in config_json["sections"].items():
        for option_name, option in section["options"].items():
            if option["type"] in ("bool", "flag"):
                value = bool_to_string(string_to_bool(str(option["value"])))
            elif option["type"] in ("dir"):
                value = str(option["value"])
                if value == "":
                    continue
            if value not in ("no"): #TODO: Check what possible values there are for false
                #TODO: Should we add the no's to the comand
                comand += f"{sep}--{option_name}"
                if option["type"] != "flag":
                    value = QuoteForPOSIX(value)
                    comand += f"={value}"
    return comand

def string_to_bool(string):
    if string.lower() in ("yes", "true"):
        return True
    else:
        return False

def bool_to_string(bool):
    if bool:
        return "yes"
    else:
        return "no"

def run(program, *args, **kargs):
    new_args = []
    for key in kargs:
        value = kargs[key]
        new_args.append(f"--{key}={value}")
    for value in args:
        new_args.append(f"-{value}")
    print("Running: " + str([program.split(" ")] + new_args))
    process = subprocess.run(program.split(" ") + new_args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    return process.stdout.decode()

#Adapted from https://stackoverflow.com/questions/4770993/how-can-i-make-silent-exceptions-louder-in-tkinter
class Stderr(object):
    def __init__(self, parent):
        self.txt = Text(parent)
        self.pack(self.txt, )
    def write(self, s):
        self.txt.insert('insert', s)
    def fileno(self):
        return 2

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
    def __init__(self, parent, name, source:Data, special_valid_params, special_required_params) -> None:
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
                raise RuntimeError(f"Parameter '{key}' in '{name}' is not a valid param. Valid params are {self.valid_params}.")
            setattr(self, key, getattr(self.source, key))
        
        for key in list(set(self.params).symmetric_difference(set(self.valid_params))):
            setattr(self, key, "default")
            self.params.append(key)
    
    def get_hidden(self):
        try:
            return string_to_bool(self.hidden)
        except:
            return False

    def pack(self, tk, **kargs):        
        if not self.get_hidden():
            tk.pack(kargs)
    
    def grid(self, tk, **kargs):
        if not self.get_hidden():
            tk.grid(kargs)

class Option(Component):
    def __init__(self, parent, section, name, data, special_valid_params = [], special_required_params=[]) -> None:
        self.source_attribute = "value"
        required_params = ["type"]
        valid_params = ["type", "value", "label", "desc", "hidden", "fill", "side", "expand"]
        super().__init__(parent, name, getattr(getattr(getattr(getattr(data, "sections"), section), "options"), name), special_required_params=special_required_params + required_params, special_valid_params=special_valid_params + valid_params)
        self.fill = "both" if self.fill == "default" else self.fill
        self.side = "top" if self.side == "default" else self.side
        self.expand = False if self.expand == "default" else self.expand

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
        self.width = 50 if self.width == "default" else self.width
        self.label = self.name if self.label == "default" else self.label
        self.value = "" if self.value == "default" else self.value

        #Building GUI
        self.container = self.get_frame()
        # self.container = LabelFrame(self.get_frame(), text=self.label)
        # self.pack(self.container, fill="both", expand=True)
        self.label_tk = Label(self.container, text=self.label)
        self.pack(self.label_tk, side="left")
        self.directory_entry = Entry(self.container, width=self.width)
        self.directory_entry.bind('<KeyRelease>', self.handler)
        self.directory_entry.insert(0, self.value)
        self.pack(self.directory_entry, side="left")
        self.browse_button = Button(self.container, text="browse", command=self.browse_dir)
        self.pack(self.browse_button, side="right")
        self.desc = Label(self.container, text = self.desc, font=("", 8)) #TODO: Make a hover-over pop up
        self.pack(self.desc, side="left")
    
    def handler(self, event):
        print(f"Setting value to {self.directory_entry.get()}")
        self.value = self.directory_entry.get()
    
    def browse_dir(self):
        initDir=self.value
        if initDir=="":
            initDir=os.getcwd()
        if not os.path.isdir(initDir):
            messagebox.showerror("Error", f'Specified directory not found.  Value was:{"(Empty)" if initDir=="" else initDir}')
            initDir=""
        dir = filedialog.askdirectory(initialdir=initDir)
        if not dir in ("", ()): #askdirectory can return an empty tuple(Escape pressed) or an empty string(Cancel pressed)
            self.directory_entry.delete(0, END)
            self.directory_entry.insert(0, dir)
            self.handler(None)

class OptionBool(Option):
    def __init__(self, parent, section, name, data):
        super().__init__(parent ,section, name, data)
        #Setting defaults
        self.value = "no" if self.value == "default" else self.value
        self.label = self.name if self.label == "default" else self.label

        #Building GUI
        self.bool = BooleanVar(value = self.value)
        self.check_button = Checkbutton(self.get_frame(), text=self.label, command=self.handler, variable=self.bool)
        self.pack(self.check_button, side="left")
        self.desc = Label(self.get_frame(), text = self.desc) #TODO: Make a pop up
        self.pack(self.desc, side="left")
    
    def handler(self):
        print(f"Setting value to {self.bool.get()}.")
        self.value = "yes" if self.bool.get() else "no"

class Section(Component):
    def __init__(self, parent, section, data:Data): #TODO: Figure out if I can pass in data instead of making it global
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
            elif my_type == "bool" or my_type == "flag":
                self.components[option] = OptionBool(self.get_frame(), section, option, data)
            else:
                raise RuntimeError(f"Option attribute '{my_type}' in {option} is not implemented yet.")
            
            # self.components[option].get_frame().pack(fill="both", expand=1, side="top")
            self.pack(self.components[option].get_frame(), fill = self.components[option].fill, expand = self.components[option].expand)
    
    def get_frame(self):
        return self.frame
    
class App(Component):
    def __init__(self, my_json_or_filename):
        if type(my_json_or_filename) == str:
            self.open(my_json_or_filename)
            self.filename = my_json_or_filename
        elif type(my_json_or_filename == dict):
            self.filename = None
            self.data = Data(**my_json_or_filename)
            self.my_json = my_json_or_filename
        else:
            raise RuntimeError(f"Invalid parameter my_json_or_file: {my_json_or_filename}.")


        self.root = tk.Tk()
        super().__init__(self.root, "app", self.data, special_required_params=["sections"], special_valid_params=["sections", "name"])
        
        self.name = "app" if self.name == "default" else self.name
        
        self.root.title(self.name)
        self.root.report_callback_exception = self.report_callback_exception

        self.search_box = Frame(self.root)
        self.search_entry = Entry(self.search_box)
        self.search_entry.bind("<KeyRelease>", self.call_search)
        self.pack(self.search_entry, side = "right")
        self.search_label = Label(self.search_box, text = "Search for options:")
        self.pack(self.search_label, side = "right")
        self.pack(self.search_box, side="top", anchor="e")

        self.build_notebook()

        self.done_button = Button(self.root, text="Continue", command=self.my_continue)
        self.pack(self.done_button, side="bottom", anchor="e")

    def build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.pack(self.notebook, fill="both", expand=1)    
        self.program = "/home/cherpin/git/trick/configure"
        self.sections = {}
        sections = getattr(self.source, "sections")._dict_()
        for section in sections:
            obj = getattr(getattr(self.source, "sections"), section)
            if len(getattr(obj, "options")._dict_()) > 0: #Note: not adding section if empty
                self.sections[section] = Section(self.notebook, section, self.source)
            


    def call_search(self, e):
        current = self.search_entry.get()
        self._search(current, self.sections)
        # App(self.search_data._dict_())
        # self.notebook.destroy()
        # self.build_notebook()
    
    def _search(self, word, sections):
        section_id = 0
        for section in sections:
            options = sections[section].components
            count_hidden = 0
            for option in options: #TODO: Allow for double grouping
                if word != '' and not App.is_match(word, option):
                    options[option].get_frame().pack_forget()
                    count_hidden += 1
                else:
                    options[option].get_frame().pack(fill = options[option].fill, )
            if count_hidden == len(sections[section].components):
                self.notebook.hide(section_id)
            else:
                self.notebook.add(sections[section].get_frame(), text=section)
                pass
            section_id += 1
    @staticmethod
    def is_match(search, book):
        return search.lower() in book
    # def _search(self, word, search_obj):
    #     for att_name in search_obj._dict_():
    #         att = getattr(search_obj, att_name)
    #         if att_name == "options":
    #             for option in att._dict_():
    #                 if word not in option: #TODO: Change to search in whole dict with getattr
    #                     setattr(getattr(att, option), "hidden", "true")
    #                 else:
    #                     setattr(getattr(att, option), "hidden", "false")
    #         elif type(att) is Data:
    #             self._search(word, att)
    #     # self.search(word, search_obj)

        return self.source

    # def search(self, word, search_obj):
    #     flat_json = {
    #         "sections" : {
    #             "results" : {

    #             }
    #         }
    #     }
    #     found = None
    #     for str_att in search_obj._dict_():
    #         att = getattr(search_obj, str_att)
    #         if type(att) is Data:
    #             if word in str_att:
    #                 found = str_att
    #             else:
    #                 self.search(word, att)
    #         else:
    #             if word in str(att):
    #                 found = str(att)
    #     return found
                

    def get_frame(self):
        return self.root
    
    def my_continue(self):
        cmd = get_configure_command(self.program, self.source._dict_())
        RunCommand(self, cmd)
        # self.save()

    def save(self, filename=None):
        if filename == None:
            if self.filename == None:
                raise RuntimeError(f"No file to save configuration to.")
            else:
                filename = self.filename
        with open(filename, "w") as f:
            f.write(json.dumps(self.source._dict_(), indent=4)) #TODO: What happens if there is an error on this line

    
    def open(self, filename):
        with open(filename, "r") as f:
            new_json = json.load(f)
            self.data = Data(**new_json)
            self.my_json = new_json
    
    #Adapted from https://stackoverflow.com/questions/4770993/how-can-i-make-silent-exceptions-louder-in-tkinter
    def report_callback_exception(self, exc, val, tb):
        #Handles tkinter exceptions
        err_msg = {}
        err = err_msg.get(str(val), f'Unknown Error:{val}')
        logging.error(traceback.format_exception(exc, val, tb))
        messagebox.showerror('Error Found', err)
    
    def is_saved(self):
        # return DeepDiff(self.original_dict, self.data._dict_())
        return self.original_dict == self.data._dict_()
    
class RunCommand:
    def __init__(self, parent, command) -> None:
        self.win = tk.Toplevel()
        # sys.stderr = Stderr(self.win)
        self.parent = parent
        self.command = command
        self.win.title("Running command")
        self.title = Label(self.win, text = "Click run to run the folling command:")
        self.pack(self.title, padx=10, pady=10)
        self.label = Label(self.win, text=command)
        self.pack(self.label, pady=10, padx=10)
        self.run_button = Button(self.win, text="run", command=self.run)
        self.pack(self.run_button, pady=10)
        self.output = ScrolledText(self.win, state="disabled", height=8, width=50)
        self.pack(self.output, fill="both", expand=True)
        self.quit_button_and_save = Button(self.win, text="Quit and Save", command=self.quit_and_save)
        self.pack(self.quit_button_and_save, )
        self.quit_button = Button(self.win, text="Quit", command=self.quit)
        self.pack(self.quit_button, )
    
    def pack(self, tk, **kargs):
        tk.pack(kargs)
    
    def grid(self, tk, **kargs):
        tk.grid(kargs)

    def quit(self):
        self.win.destroy()
    
    def quit_and_save(self):
        self.parent.save()
        self.win.destroy()

    def run(self):
        stdout = run(self.command)
        self.display(stdout)
    
    def display(self, msg):
        self.output.configure(state="normal")
        self.output.insert(END, msg)
        self.output.configure(state="disabled")
        self.output.yview(END)

            
if __name__ == "__main__":
    config_file = "config.json"
    if not os.path.isfile(config_file):
        config_file = {
            "name" : "Trick Setup",
            "sections" : {}
        }
    a = App(config_file)
    a.get_frame().mainloop()


