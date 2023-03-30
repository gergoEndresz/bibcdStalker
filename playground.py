import configparser
import os
import pandas as pd
from utils import transform

if __name__ == "__main__":
    # meta_df, combined_logs = IO.generate_combined_files()
    # meta_df["datetime"] = meta_df.timestamp.map(IO.millis_to_datetime)
    # combined_logs["datetime"] = combined_logs.timestamp.map(IO.millis_to_datetime)
    #
    # culprits_df = IO.process_culprits(meta_df)
    # culprits_df.to_csv(f"{IO.OUTPUT_DIR}/culprits_all.csv")
    # df = pd.read_csv("/bin/2023-03-30-14-09-31.meta.csv")
    path = "/Users/GEZ03/PycharmProjects/bibcdStalker/resources/output/2023-03-30-14-31-32.meta.csv"
    df = pd.read_csv(path)
    df = transform.get_path_from_fullDisplayName(df)