from main import ConfigOption, Configure

config = [
    {
        "type" : "dir",
        "value" : "/usr/bin",
        "label" : "Enter your binary directory",
        "name" : "bindir"
    },
    {
        "type" : "bool",
        "value" : "false",
        "name" : "java-enable"
    }
]




if __name__ == "__main__":
    configs = []
    for c in config:
        configs.append(ConfigOption(c["name"], c))
    c = Configure(configs)
    print(c.get_command())
