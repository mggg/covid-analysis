import pandas as pd

def preprocess_colleges(colleges_file: str,
                        min_endowment: float,
                        min_dorm_capacity:float):

    colleges_df = pd.read_csv(colleges_file)

    def clean_numbers(string:str):
        # for the NaN values
        if type(string) == float:
            return string

        new_str = ""
        for char in string:
            if char.isnumeric():
                new_str += char

        if new_str == "":
            return 0
        else:
            return (new_str)

    colleges_df["endowment"] = colleges_df["endowment"].map(clean_numbers)
    colleges_df["dorm capacity"] = colleges_df["dorm capacity"].map(clean_numbers)

    colleges_df = colleges_df[(colleges_df["endowment"] > min_endowment) & (colleges_df["dorm capacity"] > min_dorm_capacity)]

    return colleges_df

df = preprocess_colleges("./data/ma_dorm_capacity.csv", 100000000, 500)
print(df)
