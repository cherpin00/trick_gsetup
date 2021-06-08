import pytest
from main import App

def test_search():
    my_json = {
        "sections" : {
            "Test" : {
                "options" : {
                    "help" : {
                        "type" : "flag"
                    },
                    "another" : {
                        "type" : "bool"
                    }
                }
            }
        }
    }
    a = App(my_json)
    a.search_data = a.data
    r_value = a._search("help", a.search_data)._dict_()
    assert {'sections': {'Test': {'options': {'another': {'hidden': 'true', 'type': 'bool', 'value': 'no'}, 'help': {'type': 'flag', 'value': 'no'}}}}} == r_value

if __name__ == "__main__":
    test_search()