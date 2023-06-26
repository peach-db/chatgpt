from typing import Optional

import pandas as pd
from chatgpt.connectors.structured import convert_df_to_texts, get_months_diff, get_years_diff, grammar_clean_texts

USER_DATA_CSV_PATH = "/Users/vatsalaggarwal/Downloads/user_sample.csv"
CMS_CSV_PATH = "/Users/vatsalaggarwal/Downloads/payload_cms_products.csv"


def get_cms_data():
    df = pd.read_csv(CMS_CSV_PATH)
    # Filter
    df = df[df["category"] == "63e0db9b76cea5c5e3c01620"]

    # Convert
    return convert_df_to_texts(df, ["name", "title", "description"], "# {}\n{}\n\n## Description\n{}")


def get_user_data(max_rows: Optional[int] = None):
    user_data = pd.read_csv(USER_DATA_CSV_PATH)
    if max_rows:
        user_data = user_data.head(max_rows)

    # Filter
    assert len(user_data[user_data["goal_target"] == 0]) == 0
    for columns in user_data.columns:
        assert len(user_data[user_data[columns].isna()]) == 0

    # Clean
    ## DOB to "years old"
    user_data["years_old"] = user_data["dob"].apply(get_years_diff).apply(int)
    ## Goal target date to "months remaining"
    user_data["months_to_goal"] = user_data["goal_target_date"].apply(get_months_diff).apply(int)

    # Convert
    users_with_salary = user_data[user_data["current_salary"] != 0]
    texts_salaried = convert_df_to_texts(
        users_with_salary,
        [
            "first_name",
            "last_name",
            "years_old",
            "empoyment_status",  # NOTE: bug in original data which misspells "employment"
            "current_salary",
            "highest_education_level",
            "goal_type",
            "months_to_goal",
        ],
        "{} {} is {} years old. They are {} and earn {} per year. They have {} education and their goal is {} in {} months.",
    )

    # Convert
    users_without_salary = user_data[user_data["current_salary"] == 0]
    texts_unsalaried = convert_df_to_texts(
        users_without_salary,
        [
            "first_name",
            "last_name",
            "years_old",
            "empoyment_status",  # NOTE: bug in original data which misspells "employment"
            "highest_education_level",
            "goal_type",
            "months_to_goal",
        ],
        "{} {} is {} years old. They are {}. They have {} education and their goal is {} in {} months.",
    )

    texts = texts_salaried + texts_unsalaried

    # Clean grammar
    texts = grammar_clean_texts(texts)

    return texts


if __name__ == "__main__":
    cms_data = get_cms_data()
    user_data = get_user_data(max_rows=5)
