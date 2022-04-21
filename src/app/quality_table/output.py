import json


def main():
    result = {}
    with open("output_properties.json") as file:
        data = json.load(file)

        for element in data["hits"]["hits"]:

            if "ccm:replicationsource" in element["_source"]["properties"].keys():
                replication_source = element["_source"]["properties"][
                    "ccm:replicationsource"
                ]
                print(replication_source)
                if replication_source not in result.keys():
                    result.update({replication_source: {"entries": 0}})
                result[replication_source]["entries"] += 1
                for key, content in element["_source"]["properties"].items():
                    content_value = 0
                    # TODO differentiate depending on type, e.g., string or list
                    if content != "":
                        content_value = 1

                    if key not in result[replication_source].keys():
                        result[replication_source].update({key: content_value})
                    else:
                        result[replication_source][key] = (
                            content_value + result[replication_source][key]
                        )
                    print(content, content_value, result[replication_source][key])
    print(result)
    # TODO: Potentially some sources do not have all properties
    for replication_source, properties in result.items():
        print(f"----{replication_source}----")
        number_of_entries = properties["entries"]
        for key, value in properties.items():
            if key != "entries":
                print(f"{key}: {value/number_of_entries * 100}%")


if __name__ == "__main__":
    main()
