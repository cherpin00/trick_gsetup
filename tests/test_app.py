import pytest
from main import App
import threading

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
    result = a._search("help", a.sections)
    expected = {
        "sections" : {
            "Test" : {
                "options" : {
                    "help" : {
                        "type" : "flag"
                    }
                }
            }
        }
    }
    assert expected == result

    

if __name__ == "__main__":
    test_search()