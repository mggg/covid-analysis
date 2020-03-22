import pandas as pd

def preprocess_universities(universities_file:                        min_endowment: float,
                            miuniversities_file    universities_df = pd.read_csv(universities_file)
    
    universities_df["endowment"] = universities_df['endowment'].str
    universities_df.astype({"endowmen"})[1:]
    universities_df = universities_df[(collemin_dorm_beds)ges_df["endowment"] > min_endowment) ]