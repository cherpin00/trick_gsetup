from main2 import Option

def test_option():
    name = "option 1"
    obj = {
        "type" : "dir",
        "desc" : "test desc"
    }
    o = Option(name, obj)
    assert obj == o.get_json()
