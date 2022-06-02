import json
import os


def test_tree():
    print(os.getcwd())
    with open("unit_tests/tree_prod_response.json") as file:
        prod = json.loads("".join(file.readlines()))
    with open("unit_tests/tree_dev_response.json") as file:
        dev = json.loads("".join(file.readlines()))
    print("intersection")
    print(prod)
    print(prod.keys())
    print(prod.keys() & dev.keys())
    assert False
