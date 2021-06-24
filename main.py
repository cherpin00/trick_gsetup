#!/usr/bin/python3
# import PIL
from posixpath import curdir
import tkinter
# import ttkthemes

import tkinter as tk
from tkinter import StringVar, Tk, ttk
#from ttkthemes import ThemedTk
from tkinter import BooleanVar, Toplevel, Text, Menu, Canvas
from tkinter.constants import NONE, SUNKEN
from tkinter.ttk import Frame, Button, Entry, Label, Checkbutton, LabelFrame, Scrollbar
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
import argparse
import shutil
import time
import errno
import ntpath
import glob

# from idlelib.ToolTip import *


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

def get_configure_command(command, config_json, include_vars=False):
    def get_with_catch(my_dict, key):
        try:
            return my_dict[key]
        except KeyError as e:
            raise RuntimeError(f"Required key {e} not found in the following json: {my_dict}")

    sep = " "
    vars = ""
    for section_name, section in get_with_catch(config_json, "sections").items():
        for option_name, option in get_with_catch(section, "options").items():
            if get_with_catch(option, "type") in ("bool", "flag"):
                value = bool_to_string(string_to_bool(str(get_with_catch(option, "value"))))
            elif get_with_catch(option, "type") in ("dir"):
                value = str(get_with_catch(option, "value"))
                if value == "":
                    continue
            elif get_with_catch(option, "type") == "envvar":
                value = str(get_with_catch(option, "value"))
                if value == "":
                    if option_name in os.environ:
                        del os.environ[option_name]
                else:
                    os.environ[option_name] = value
                    if include_vars:
                        vars += f"{option_name} = {value}\n"
                continue
            else:
                my_type = get_with_catch(option, "type")
                raise RuntimeError(f"Option type '{my_type}' in {option} is not implemented yet.")
            if value not in ("no"): #TODO: Check what possible values there are for false
                #TODO: Should we add the no's to the comand
                command += f"{sep}--{option_name}"
                if option["type"] != "flag":
                    value = QuoteForPOSIX(value)
                    command += f"={value}"
    if include_vars:
        command = vars + command
    return command

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
    time = kargs.get("time", False)
    new_args = []
    for key in kargs:
        value = kargs[key]
        new_args.append(f"--{key}={value}")
    for value in args:
        new_args.append(f"--{value}")
    if time:
        program = "time " + program
    logging.info("Running: " + str(program.split(" ") + new_args))
    process = subprocess.run(program.split(" ") + new_args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    return process.stdout.decode()

def textEvent(e):
    print("state", e.state)
    print("key", e.keysym)
    if (e.state == 20 and e.keysym == "c"): #TODO: Add other exceptions like Ctrl+a
        return
    else:
        return "break"

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

class ToolTip(object): #Adapted from https://stackoverflow.com/questions/20399243/display-message-when-hovering-over-something-with-mouse-cursor-in-python

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(tw, text=self.text, justify="left",
                      background="#ffffe0", relief="solid", borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


class OptionDir(Option):
    def __init__(self, parent, section, name, data):
        super().__init__(parent, section, name, data, special_valid_params=["width"])
        # Setting defaults
        self.width = 20 if self.width == "default" else self.width
        self.label = self.name if self.label == "default" else self.label
        self.value = "" if self.value == "default" else self.value

        #Building GUI
        self.container = self.get_frame()
        self.container = LabelFrame(self.get_frame(), text=f"{self.label} - {self.desc}")
        self.pack(self.container, fill="both", expand=True)
        # self.label_tk = Label(self.container, text=self.label)
        # self.pack(self.label_tk, side="left")
        self.directory_entry = Entry(self.container, width=self.width)
        self.directory_entry.bind('<KeyRelease>', self.handler)
        self.directory_entry.insert(0, self.value)
        self.pack(self.directory_entry, side="left", fill="both", expand=True)
        self.browse_button = Button(self.container, text="browse", command=self.browse_dir)
        self.pack(self.browse_button, side="right")
        CreateToolTip(self.browse_button, "Browse for a directory.")
        # self.desc_label = Label(self.container, text = self.desc, font=("", 8)) #TODO: Make a hover-over pop up
        # CreateToolTip(self.desc_label, self.desc)
        # self.pack(self.desc_label, side="left")
    
    def handler(self, event):
        logging.debug(f"Setting value to {self.directory_entry.get()}")
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
            self.directory_entry.delete(0, "end")
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
        # self.desc_label = Label(self.get_frame(), text = self.desc) #TODO: Make a pop up
        # self.pack(self.desc_label, side="left")
        CreateToolTip(self.check_button, self.desc)
    
    def handler(self):
        logging.debug(f"Setting value to {self.bool.get()}.")
        self.value = "yes" if self.bool.get() else "no"

class OptionEnvVar(OptionDir):
    def __init__(self, parent, section, name, data):
        super().__init__(parent, section, name, data)

        self.container["text"] = "ENV: " + self.container["text"]
        self.browse_button.pack_forget()

        # self.value = "" if self.value == "default" else self.value
        # self.label = self.name if self.label == "default" else self.label

        # self.tk_label = Label(self.get_frame(), text=self.label)
        # self.pack(self.tk_label, side="left", pady=10)

        # self.directory_entry = Entry(self.get_frame())
        # self.directory_entry.bind('<KeyRelease>', self.handler)
        # self.directory_entry.insert(0, self.value)
        # self.pack(self.directory_entry, fill="both", expand=True, side="left")


    # def handler(self, event):
        # logging.debug(f"Setting value to {self.directory_entry.get()}")
        # self.value = self.directory_entry.get()    

class Section(Component):
    def __init__(self, parent, section, data:Data): #TODO: Figure out if I can pass in data instead of making it global
        valid_params = ["options", "size"] #TODO: Use size or take it out of valid params
        required_params = ["options"]
        super().__init__(parent, section, getattr(getattr(data, "sections"), section), special_valid_params=valid_params, special_required_params=required_params)
    
        self.components = {}
        # self.frame = Frame(parent)
        # self.frame.pack(fill="both", expand = 1) #TODO: Not sure if this is needed
        if type(parent) == Notebook:
            parent.add(self.get_frame(), text=section)
        
        options = getattr(self.source, "options")._dict_()
        for option in options: #TODO: Don't repeat this logic in get_configure_command
            obj = getattr(getattr(self.source, "options"), option)
            my_type = obj.type
            if my_type == "dir":
                self.components[option] = OptionDir(self.get_frame(), section, option, data)
            elif my_type == "bool" or my_type == "flag":
                self.components[option] = OptionBool(self.get_frame(), section, option, data)
            elif my_type == "string" or my_type == "envvar":
                self.components[option] = OptionEnvVar(self.get_frame(), section, option, data)
            else:
                raise RuntimeError(f"Option type '{my_type}' in {option} is not implemented yet.")
            
            # self.components[option].get_frame().pack(fill="both", expand=1, side="top")
            self.pack(self.components[option].get_frame(), fill = self.components[option].fill, expand = self.components[option].expand)
    
    def get_frame(self):
        return self.frame

class App(Component):
    def __init__(self, my_json_or_filename, program="/home/cherpin/git/trick/configure"):
        if type(my_json_or_filename) == str:
            self.open(my_json_or_filename)
            self.filename = my_json_or_filename
        elif type(my_json_or_filename == dict):
            self.filename = None
            self.data = Data(**my_json_or_filename)
            self.my_json = my_json_or_filename
        else:
            raise RuntimeError(f"Invalid parameter my_json_or_file: {my_json_or_filename}.")

        self._program = program

        self.root = tkinter.Tk()
        # self.root = ThemedTk() #TODO: Figure out how to run this without pip install.
        # self.root.get_themes()
        # self.root.set_theme("plastik")
        self.root.geometry("1050x800") #TODO: Set geometry based on width of notebook

        super().__init__(self.root, "app", self.data, special_required_params=["sections"], special_valid_params=["sections", "name"])
        
        self.name = "app" if self.name == "default" else self.name

        self.root.title(self.name)
        self.root.minsize(width=1000, height=400)
        # self.root.maxsize(width=800, height=800)

        self.root.report_callback_exception = self.report_callback_exception
        
        self.header = Frame(self.root)
        self.header.pack(side = "top", fill="x")
        self.footer = Frame(self.root)
        self.footer.pack(side="bottom", fill="x")
        self.options_title = "Options for script"
        self.notebook_label_frame = LabelFrame(self.root, text=self.options_title) #TODO: Add dynamic (script) and (filtered) text
        self.notebook_label_frame.pack(expand=True, fill="both")
        self.body = self.get_body(self.notebook_label_frame)

        self.add_shortcuts()
        self.build_menu(self.root)
        self.build_search_bar(self.header)
        
        self.notebook_frame = Frame(self.body)
        self.notebook_frame.pack(side="top", expand=True, fill='both')
        self.build_notebook(self.body)
        self.build_current_command() #We can only run this after we build a notebook

        self._status = StringVar()
        self.status_label = Label(self.footer, textvariable=self._status)
        self.set_status()
        self.status_label.pack(side="left")
    
    @property
    def program(self):
        return self._program
    
    @program.setter
    def program(self, value):
        self._program = value
        self.update_status()
        self.build_current_command()
    
    def set_status(self, msg=None):
        if msg is None:
            msg = f"Config file: {self.filename}"
        self._status.set("Status - " + msg)

    def add_shortcuts(self):
        self.root.bind(f"<Alt-h>", lambda e: self.show_help())
        self.root.bind(f"<Alt-e>", lambda e: self.execute())
        self.root.bind(f"<Alt-o>", lambda e: self.focus_options())
        self.root.bind(f"<Alt-s>", lambda e: self.focus_search())

    def focus_options(self):
        # print("Hello")
        self.notebook_label_frame.focus_set()
    
    def focus_search(self):
        self.search_entry.focus_set()

    def get_body(self, parent):
        main_frame = Frame(parent)
        main_frame.pack(fill="both", expand=True)

        my_canvas = Canvas(main_frame)
        my_canvas.pack(side="left", fill="both", expand=True)

        my_scrollbar = ttk.Scrollbar(master=main_frame, orient="vertical", command=my_canvas.yview)
        my_scrollbar.pack(side="right", fill="y")

        my_canvas.configure(yscrollcommand=my_scrollbar.set)

        second_frame = Frame(my_canvas)
        canvasFrame = my_canvas.create_window((0, 0), window=second_frame, anchor="nw")
        
        self.setIsInCanvas(False)
        second_frame.bind("<Configure>", lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))
        my_canvas.bind('<Configure>', lambda e: my_canvas.itemconfig(canvasFrame, width=e.width))
        def _scroll(e, dir):
            if self.isInCanvas:
                speed = 1
                my_canvas.yview_scroll(dir * speed, "units")

        self.root.bind_all('<Button-4>', lambda e: _scroll(e, -1))
        self.root.bind_all('<Button-5>', lambda e: _scroll(e, 1))
        my_canvas.bind('<Enter>', lambda e: self.setIsInCanvas(True))
        my_canvas.bind('<Leave>', lambda e: self.setIsInCanvas(False))

        return second_frame
    def setIsInCanvas(self, value):
        self.isInCanvas = value

    def conf(self, e):
            self.body.update()
            height = self.body.winfo_height()
            width = self.body.winfo_width()
            self.notebook.configure(height=height, width=width)

    def build_notebook(self, parent):
        self.notebook = ttk.Notebook(parent)
        # self.body.bind("<Configure>", self.conf)
        self.notebook.pack(fill="both", expand=True) 
        self.sections = {}
        sections = getattr(self.source, "sections")._dict_()
        for section in sections:
            obj = getattr(getattr(self.source, "sections"), section)
            if len(getattr(obj, "options")._dict_()) > 0: #Note: not adding section if empty
                self.sections[section] = Section(self.notebook, section, self.source)
        
        self.previous_section_length = 0

    def build_search_bar(self, parent):
        #Search box
        # SearchBox(self).get_frame().pack(anchor="e")
        self.outer_search_box = LabelFrame(parent, text="Filter Options")
        self.outer_search_box.pack(side="right", anchor="n", fill="x")

        self.search_box = Frame(self.outer_search_box)
        self.search_box.rowconfigure(0, weight=1)
        self.search_box.columnconfigure(0, weight=1)
 
        self.search_entry = Entry(self.search_box)
        self.search_entry.bind("<KeyRelease>", self.call_search)
        CreateToolTip(self.search_entry, "Search for a specific option.")
        self.search_entry.grid(row=0, column=1, sticky="e")

        self.search_label = Label(self.search_box, text = "Search for options:", underline=0)
        self.search_label.grid(row=0, column=0, sticky="e")

        self.pack(self.search_box, side="top", anchor="e", expand=False, fill="x")

        self.only_checked = BooleanVar(False)
        self.checked_toggle = Checkbutton(self.outer_search_box, variable=self.only_checked, text="Show only used options", command=self.call_search)
        self.checked_toggle.pack(side="right", anchor="e", expand=False, fill="x")

        #End Search box
        

        #Current Script
        self.current_script = Frame(parent)
        self.current_script.pack(side="left", anchor="n", fill="x", expand=True)

        self.label_frame = LabelFrame(self.current_script, text="Current Script with Options", underline=21)
        self.label_frame.pack(side="top", expand=True, fill="x")

        # self.win = tk.Toplevel()
        # self.win.title("General help for the configure script")
        # self.win.geometry("800x500")
        # output = run(self.program, "help")
        # self.output = ScrolledText(self.win, state="normal", height=8, width=50)
        # self.output.insert(1.0, output)
        # self.output["state"] = "disabled"
        # self.pack(self.output, fill="both", expand=True, anchor="w")
        self.current_command = ScrolledText(self.label_frame, height=8, state="normal")
        self.current_command.bind("<Key>", textEvent)
        self.current_command.bind("<Enter>", lambda e: self.setIsInCurrentCommand(True))
        self.current_command.bind("<Leave>", lambda e: self.setIsInCurrentCommand(False))
        self.current_command.pack(side="top", anchor="w", fill="x", expand=True)

        self.setIsInCurrentCommand(False)

        self.root.bind("<KeyRelease>", self.build_current_command)
        self.root.bind("<ButtonRelease-1>", self.build_current_command)

        self.status_frame = Frame(self.label_frame)
        self.status_frame.pack()

        status, color = self.get_status()
        self.label_status = Label(self.status_frame, text=f"Status: {status}", foreground=color)
        self.label_status.pack()

        self.button_frame = Frame(self.label_frame)
        self.button_frame.pack()

        self.help_button = Button(self.button_frame, text=f"Help for script", command=self.show_help, underline=0)
        self.help_button.pack(side="left", anchor="w", expand=True, fill="both", padx=10)


        self.done_button = Button(self.button_frame, text="Execute command with options (will remember settings)", command=self.execute, underline=0)
        CreateToolTip(self.done_button, "Execute command with options")
        self.done_button.pack(side="right", anchor="e", expand=True, fill="both", padx=5)
    
    def setIsInCurrentCommand(self, value):
        self.isInCurrentCommand = value

    def update_status(self):
        self.label_status["text"], self.label_status["foreground"] = self.get_status()

    def get_status(self):
        rvalue = ""
        color = "black"
        if os.access(self.program, os.X_OK):
            rvalue += "Valid"
            color = "green"
        else:
            rvalue += "Invalid"
            color = "red"
        return rvalue + " Executable File", color

    def show_help(self): #TODO: This code is being repeated where we a ScrolledText widget
        self.win = tk.Toplevel()
        self.win.title("General help for the configure script")
        self.win.geometry("800x500")
        output = run(self.program, "help")
        self.output = ScrolledText(self.win, state="normal", height=8, width=50)
        self.output.bind("<Key>", textEvent)
        self.output.insert(1.0, output)
        self.pack(self.output, fill="both", expand=True, anchor="w")

    def build_current_command(self, e=None):
        # self.current_command["state"] = "normal"
        if not self.isInCurrentCommand:
            text = get_configure_command(self.program, self.source._dict_(), include_vars=True)
            self.current_command.delete(1.0, "end")
            self.current_command.insert(1.0, text)
        # self.current_command["state"] = "disabled"
        # self.current_command["text"] = text

    def build_menu(self, parent):
        menubar = Menu(parent)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Select command", command=self.select_command)
        # filemenu.add_command(label="Open", command=lambda: print("hello"))
        filemenu.add_command(label="Save options", command=self.save)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=parent.destroy) #TODO: This may not work for non root parents
        menubar.add_cascade(label="File", menu=filemenu, underline=0)
    
        parent.config(menu=menubar)

    def select_command(self):
        initDir = os.path.abspath(os.path.dirname(self.program))
        file = filedialog.askopenfilename(initialdir=initDir)
        if file not in ("", ()):
            self.program = os.path.abspath(file)
            

    def call_search(self, e=None):
        current = self.search_entry.get()
        self._search(current, self.sections)
        msg = " (filtered)"
        if current != "" or self.only_checked.get():
            self.notebook_label_frame["text"] = self.options_title + msg
        else:
            self.notebook_label_frame["text"] = self.options_title
    
    def _search(self, word, sections):
        section_id = 0
        self.current_section_length = 0
        showing = { "sections" : {} } #This is used for testing.
        for section in sections:
            options = sections[section].components
            count_hidden = 0
            showing["sections"][section] = {}
            showing["sections"][section]["options"] = {}
            for option in options: #TODO: Allow for double grouping
                if (word != '' and not App.is_match(word, option)) or (self.only_checked.get() and options[option].value in ("no", "")):
                    options[option].get_frame().pack_forget()
                    count_hidden += 1
                else:
                    options[option].get_frame().pack(fill = options[option].fill, )
                    showing["sections"][section]["options"][option] = self.my_json["sections"][section]["options"][option]
            if count_hidden == len(sections[section].components):
                self.notebook.hide(section_id)
                del showing["sections"][section]
            else:
                if self.previous_section_length == 0:
                    self.notebook.select(0)
                self.notebook.add(sections[section].get_frame(), text=section)
                self.current_section_length += 1
            section_id += 1
        self.previous_section_length = self.current_section_length
        return showing
    
    @staticmethod
    def is_match(search, *args): #Pass in args to see if search is a match with any of the arguments
        rvalue = False
        for a in args:
            if search.lower() in a.lower():
                rvalue = True
        return rvalue


    def get_frame(self):
        return self.root
    
    def execute(self, source=None, autoRun=False, parent=None, answer=None):
        self.set_status("Running script")
        if source == None:
            cmd = get_configure_command(self.program, self.source._dict_())
        else:
            cmd = get_configure_command(self.program, source._dict_())
        # RunCommand(self, cmd, autoRun=autoRun)
        if not answer:
            answer = messagebox.askyesno(title="Confirmation", message=f"Would you like to configure trick with your chosen options?")
            
        if answer:
            output = run(cmd)
            self.win = tk.Tk()
            def quit():
                self.win.destroy()
                self.root.destroy()
            self.win.title("Script's output")
            self.win.geometry("800x500")
            self.output = ScrolledText(self.win, state="normal", height=8, width=50)
            self.output.bind("<Key>", textEvent)
            self.output.insert(1.0, output)
            self.output.pack(fill="both", expand=True, anchor="w")
            self.finish_button = Button(self.win, text="Finished", command=quit)
            self.finish_button.pack(anchor="e")
            # self.root.destroy() #TODO: Check for a successfull output.
            self.save()
            # self.set_status()
            self.win.mainloop()
        # self.save()
        else:
            self.set_status()

    def save(self, filename=None):
        if filename == None:
            if self.filename == None:
                raise RuntimeError(f"No file to save configuration to.")
            else:
                filename = self.filename
        with open(filename, "w") as f:
            f.write(json.dumps(self.source._dict_(), indent=4)) #TODO: What happens if there is an error on this line
            try:
                os.makedirs("archive")
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise
        timestr = time.strftime("%Y%m%d-%H%M%S")
        shutil.copyfile(filename, f"archive/{timestr}_{ntpath.basename(filename)}")

    
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
    
    def get_scrollable_frame(self, parent, axis):
    #Create a Main Frame
        main_frame = Frame(parent)
        main_frame.pack(fill="both", expand=True, side="left")

        #Create  Canvas
        my_canvas = Canvas(main_frame)
        # my_canvas.pack(fill="both", expand=True)
        my_canvas.grid(row=0, column=0, sticky="nsew")

        self.get_scroll_bar(main_frame, my_canvas, axis)

        #Create another frame inside the canvas
        second_frame = Frame(my_canvas)
        
        #Add new frame to window in canvas
        my_canvas.create_window((0,0), window=second_frame, anchor="nw")

        return second_frame
    
    def get_scroll_bar(self, main_frame, my_canvas, axis):
    #Add a scrollbar to canvas
        if axis == "x" or axis == "both":
            my_scrollbar = Scrollbar(main_frame, orient="horizontal", command=my_canvas.xview)
            # my_scrollbar.pack(side="bottom", fill="x")
            my_scrollbar.grid(row=100, column=0, sticky="ew")
            my_canvas.configure(xscrollcommand=my_scrollbar.set)
            my_canvas.bind("<Configure>", lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))
            def _on_mouse_wheel(event):
                my_canvas.xview_scroll(-1 * int((event.delta / 120)), "units")

            my_canvas.bind_all("<MouseWheel>", _on_mouse_wheel)
        if axis == "y" or axis == "both":
            #Add a scrollbar to canvas
            my_scrollbar = Scrollbar(main_frame, orient="vertical", command=my_canvas.yview)
            # my_scrollbar.pack(side="right", fill="y")
            my_scrollbar.grid(row=0, column=100, sticky="ns")
            my_canvas.configure(yscrollcommand=my_scrollbar.set)
            my_canvas.bind("<Configure>", lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))
            def _on_mouse_wheel(event):
                my_canvas.yview_scroll(-1 * int((event.delta / 120)), "units")

            my_canvas.bind_all("<MouseWheel>", _on_mouse_wheel)
        
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        #TODO: put error here if of the options above
    
class RunCommand:
    def __init__(self, parent, command, autoRun = False) -> None:
        self.win = tk.Toplevel()
        # sys.stderr = Stderr(self.win)
        self.parent = parent
        self.command = command
        self.win.title("Running command")
        self.title = Text(self.win, height=3)
        self.title.insert(1.0, f"Click run to run the folling command:\n{command}")
        self.pack(self.title, anchor="w", expand=False, fill="x")
        self.run_button = Button(self.win, text="run", command=self.run)
        self.pack(self.run_button, anchor="w")
        self.output = ScrolledText(self.win, state="disabled", height=8, width=50)
        self.pack(self.output, fill="both", expand=True, anchor="w")
        self.quit_button_and_save = Button(self.win, text="Quit and Save", command=self.quit_and_save)
        self.pack(self.quit_button_and_save, anchor="w")
        self.quit_button = Button(self.win, text="Quit", command=self.quit)
        self.pack(self.quit_button, anchor="w")

        if autoRun:
            self.run()

        self.win.bind("<Alt-r>", lambda e: self.run())
        self.win.bind("<Alt-q>", lambda e: self.quit())
        self.win.bind("<Alt-s>", lambda e: self.quit())
    
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
        self.output.insert("end", msg)
        self.output.configure(state="disabled")
        self.output.yview("end")

class SearchBox:
    def __init__(self, parent:App) -> None:
        self.parent = parent
        
        self.top = Frame(self.parent.get_frame())

        self.search_box = LabelFrame(self.top, text="Filter Options")
        self.search_box.rowconfigure(0, weight=1)
        self.search_box.columnconfigure(0, weight=1)

        # self.done_button = Button(self.search_box, text="Continue", command=self.my_continue)
        # CreateToolTip(self.done_button, "Continue to run and save screen.")
        # self.done_button.grid(row=0,column=2, sticky="e")
        
        self.search_entry = Entry(self.search_box)
        self.search_entry.bind("<KeyRelease>", self.parent.call_search)
        CreateToolTip(self.search_entry, "Search for a specific option.")
        self.search_entry.grid(row=0, column=1, sticky="e")

        self.search_label = Label(self.search_box, text = "Search for options:")
        self.search_label.grid(row=0, column=0, sticky="e")

        self.search_box.pack(side="top", anchor="e", expand=False, fill="x")
    
    def get_frame(self):
        return self.top

class CurrentBox:
    def __init__(self, parent:App) -> None:
        self.parent = parent
        

class ChooseConfigure:
    def __init__(self, parent=None) -> None:
        if parent is None:
            self.root = Tk()
        else:
            self.root = parent
        
        self.label = Label(text="Config file not found.  Please click browse to find your config file or click continue to use the default.")
        self.label.pack()
        
        self.dir = ""
        self.browse_button = Button(self.root, text="Browse", command=self.browse)
        self.browse_button.pack()

        self.continue_button = Button(self.root, text="Continue", command=self.continue_func)
        self.continue_button.pack()
    
    def continue_func(self):
        self.file = {
            "name" : "Trick Setup",
            "sections" : {}
        }
        self.root.destroy()

    def get_frame(self):
        return self.root
    
    def browse(self):
        initDir=os.getcwd()
        if not os.path.isdir(initDir):
            messagebox.showerror("Error", f'Specified directory not found.  Value was:{"(Empty)" if initDir=="" else initDir}')
            initDir=""
        file = filedialog.askopenfilename(initialdir=initDir) #TODO: Fix this logic
        if not dir in ("", ()): #askdirectory can return an empty tuple(Escape pressed) or an empty string(Cancel pressed)
            self.file = file
        self.root.destroy()
    
    def get_file(self):
        return self.file

def execute(parent, source, program, autoRun=False, answer=None):
        cmd = get_configure_command(program, source._dict_())
        # RunCommand(self, cmd, autoRun=autoRun)
        if not answer:
            answer = messagebox.askyesno(title="Confirmation", message=f"Are you sure that you want to run the following command:\n{cmd}")
            
        if answer:
            output_txt = run(cmd)
            win = tk.Tk()
            def quit():
                win.destroy()
                if parent:
                    parent.destroy()
            win.title("Script's output")
            win.geometry("800x500")
            output = ScrolledText(win, state="normal", height=8, width=50)
            output.bind("<Key>", textEvent)
            output.insert(1.0, output_txt)
            output.pack(fill="both", expand=True, anchor="w")
            finish_button = Button(win, text="Finished", command=quit)
            finish_button.pack(anchor="e")
            # self.save()
            win.mainloop()

class LandingPage:
    def __init__(self, parent=None, config_file="./config.json", initial_dir=os.getcwd()) -> None:
        if parent:
            self.root = parent
        else:
            self.root = Tk()
        self.root.title("Configure trick")
        self.config_file = os.path.abspath(config_file)
        
        self.open_advanced = False
        self.to_close = True

        self.header = Frame(self.root)
        self.body = Frame(self.root)
        self.footer = Frame(self.root)

        self.header.pack()
        self.body.pack()
        self.footer.pack()

        self.release_label = Label(self.header, text="Release x.x")
        self.release_label.pack(anchor="w")
        self.desc_label = Label(self.header, text="Welcome to Trick.", font='Helvetica 15 bold')
        self.desc_label.pack()
        self.desc_label2 = Label(self.header, wraplength=500, text="This setup guide will allow you to easily see all the options that are available to configure Trick with.")
        self.desc_label2.pack(pady=10)

        self.label = Label(self.body, text="Location:")
        self.label.pack(anchor="w")

        self.folder_location = StringVar(value=initial_dir)
        self.folder_entry = Entry(self.body, textvariable=self.folder_location)
        self.folder_entry.pack(side="left")

        self.change_button = Button(self.body, text="Change", command=self.change_dir)
        CreateToolTip(self.change_button, "Click here to choose Trick's home directory.  Configure will run from within this directory.")
        self.change_button.pack(side="left", pady=10, padx=10)

        self.configure_fast_button = Button(self.footer, text="Configure with defaults", command=self.configure)
        CreateToolTip(self.configure_fast_button, "Run configure with the default options.")
        self.configure_fast_button.pack(side="left", padx=10, pady=10)

        self.configure_button = Button(self.footer, text="Configure with advanced options", command=self.configure_with_options)
        CreateToolTip(self.configure_button, "Choose advanced options to configure trick with.")
        self.configure_button.pack(side="left", padx=10, pady=10)
        
        self.close_button = Button(self.footer, text="Close", command=self.close)
        self.close_button.pack(side="left", padx=10, pady=10)

    def change_dir(self):
        dir = filedialog.askdirectory(initialdir=self.folder_location.get())
        if not dir in ("", ()):
            self.folder_location.set(dir)
        else:
            logging.error("Invalid directory.")
    
    def set_program(self):
        currdir = os.path.abspath(os.getcwd())
        try:
            os.chdir(self.folder_location.get())
        except:
            messagebox.showerror(title="Invalid directory", message=f"{self.folder_location.get()} is not a valid directory")
            return False
        arr = glob.glob("configure")
        if len(arr) > 0:
            self.program = os.path.abspath(arr[0])
            return True
        else:
            os.chdir(curdir)
            messagebox.showerror(title="Wrong home directory", message=f"No configure file found in location: {self.folder_location.get()}.  Please enter your trick home directory.")
            return False

    def configure(self):
        if self.set_program():
            self.open_advanced = False
            self.to_close = False
            self.close()
    
    def close(self):
        self.root.destroy()

    def configure_with_options(self):
            if self.set_program():
                self.open_advanced = True
                self.to_close = False
                self.close()
    def get_frame(self):
        return self.root
        
        

from load import load, write_help
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser()

    default = "(default: %(default)s)"
    parser.add_argument("-s", "--script-file", default="./configure", help=f"script to add args to {default}")
    # parser.add_argument("-c", "--config", default="./config.json", help=f"json file with gui options and settings {default}")
    parser.add_argument("-c", "--config", default=f"{os.path.dirname(os.path.realpath(__file__))}/sample_config.json", help=f"json file with gui options and settings {default}")
    parser.add_argument("-b", "--build", action="store_true", default=False, help=f"guess the parameter choices from the scripts help output {default}")
    args = parser.parse_args()
    
    if args.build:
        write_help(args.script_file)
        load()
    
    config_file = args.config
    if not os.path.isfile(config_file):
        c = ChooseConfigure()
        c.get_frame().mainloop()
        config_file = c.get_file()
    config_file = os.path.abspath(config_file) #Landing page will change cwd so we get abs path
    if os.path.exists(args.script_file):
        script_folder = os.path.dirname(os.path.abspath(args.script_file))
    else:
        script_folder = os.getcwd()
    l = LandingPage(parent=None, config_file=config_file, initial_dir=script_folder)
    l.get_frame().mainloop()
    if not l.to_close:
        if l.open_advanced:
            a = App(config_file, l.program)
            a.get_frame().mainloop()
        else:
            execute(None, Data(sections=Data()), l.program, autoRun=True, answer=True)


