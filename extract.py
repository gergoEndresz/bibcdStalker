from utils import scrape
from utils import transform
import json
import pandas as pd
from datetime import datetime

if __name__ == "__main__":
    path_components = ["sdp"]
    current_url = scrape.request_url(path_components)
    resp = scrape.request.urlopen(current_url).read().decode("UTF-8")
    parsed_response = json.loads(resp)
    paths, jobs = scrape.scan_for_jobs(path_components)
    list_of_runs = scrape.scan_for_task_sync(jobs)
    if len(list_of_runs) != 0:

        df = pd.DataFrame(list_of_runs)
        df = transform.standardize_fullname_in_df(df)
        df_meta = df[transform.META_COLS]
        df_meta = transform.add_TimeInQueueAction_columns(df_meta)
        df_meta = transform.get_path_from_fullDisplayName(df_meta)
        df_logs = df[transform.LOGS_COLS]
        df_culprits = transform.process_culprits(df_meta)
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        df_meta.to_csv(f"./resources/output/{now}.meta.csv", index=False)
        df_logs.to_csv(f"./resources/output/{now}.logs.csv", index=False)
        df_culprits.to_csv(f"./resources/output/{now}.culprits.csv", index=False)
    transform.generate_combined_files()
