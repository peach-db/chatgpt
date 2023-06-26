# Connector for converting structured data to text
import random
from datetime import datetime

import pandas as pd
from chatgpt import ChatGPT


def convert_df_to_texts(df: pd.DataFrame, columns: list[str], conversion_str: str) -> list[str]:
    texts = []
    for row in df.iterrows():
        texts.append(conversion_str.format(*[str(row[1][column]).strip() for column in columns]))
    return texts


def grammar_clean_texts(in_texts: list[str]) -> list[str]:
    llm = ChatGPT(
        model="gpt-4-0613",
        system_prompt="Clean up the grammar",
        temperature=0,
    )

    out_texts = []
    for text in in_texts:
        out_texts.append(llm(text)[-1]["content"])

    return out_texts


def get_years_diff(time_str: str) -> int:
    return datetime.now().year - datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f").year


def get_months_diff(time_str: str) -> int:
    months = (datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f") - datetime.now()).days / 30
    if months < 0:
        months = random.randint(1, 7)

    return months
