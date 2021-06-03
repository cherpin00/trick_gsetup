# class Component:
#     def __init__(self, name, obj, parent=None) -> None:
#         if not parent:
#             self.parent = Frame()
#         else:
#             self.parent = parent

#         self.name = name
#         self.blob = obj

from tkinter import Frame


class Section:
    def __init__(self, name, obj, parent) -> None:
        self.name = name
        self.obj = obj

        self.frame = Frame()
        self.options = {}
        for option_name in obj:
            self.options[option_name] = Option(option_name, obj[option_name])


class Option:
    def __init__(self, name, obj, parent = None, special_valid_params=[], special_required_params=[]) -> None:
        self.name = name
        self.obj = obj

        self.valid_params = ["type", "value", "label",
                             "desc", "section", "name"] + special_valid_params
        self.required_params = ["name", "type"] + special_required_params

        def get_json():
            return self.obj
