from os import EX_CANTCREAT
import json
from pprint import pprint

with open("help.txt", "r") as f:
    sections = {}
    section = None
    for line in f:
        if line.endswith(":\n"):
            section = line[:-1] 
            sections[section] = []
        elif section is not None and line != "\n":
            try:
                argIndex = line.index("--") #TODO: Add env var
                helpIndex = line.index(" ", argIndex)
                sections[section].append((line[argIndex:helpIndex], line[helpIndex:].strip()))
            except:
                print("Invalid line:", line)
myJson = []
for section in sections:
    for t in sections[section]:
        arg = t[0]
        help = t[1]
        try:
            s = arg.split("=")
            arg = s[0]
            if "=" in arg:
                continue
            type = s[1]
            if "DIR" in type:
                type = "dir"
        except:
            type = "bool"
        # print(arg, "=", type, ":", help)
        if type in ("dir", "bool"):
            myJson.append({
                "name": arg[2:],
                "section": section,
                "type": type,
            })
            if type == "bool":
                myJson[-1]["value"] = False
        else:
            print("type:", type)

with open("config.json", "w") as f:
    f.write(json.dumps(myJson, indent=4))