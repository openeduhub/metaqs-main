def transpose(data: list) -> list:
    rows = [entry["metadatum"] for entry in data]
    columns = list(data[0]["columns"].keys())
    output = []
    for column in columns:
        new_row = {"metadatum": column}
        new_row.update({"columns": {}})
        for row in rows:
            entry = {}
            for line in data:
                if line["metadatum"] == row:
                    entry = line
                    break
            new_row["columns"].update({row: entry["columns"][column]})
        output.append(new_row)
    return output
