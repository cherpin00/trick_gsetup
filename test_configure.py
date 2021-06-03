from main import ConfigOption, Configure


def test_configure():
    config = [
        {
            "type": "dir",
            "value": "/usr/bin",
            "label": "Enter your binary directory",
            "name": "bindir"
        },
        {
            "type": "bool",
            "value": "false",
            "name": "java-enable"
        }
    ]

    configs = []
    for c in config:
        configs.append(ConfigOption(c["name"], c))
    c = Configure(configs)
    assert c.get_command(
    ) == "/home/cherpin/git/trick/configure --bindir=/usr/bin --java-enable=false"

{
    "section" : {
        "name" : {

        },
        "name" : {

        },
        "name" : {

        }
    }
}
def test_option():
    name = "bindir"
    option = {
        "type": "dir"
    }
    Option(name, option)


if __name__ == "__main__":
    test_spaces()
