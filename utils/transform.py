import configparser
import os
import logging
import pandas as pd
from datetime import datetime

reader = configparser.ConfigParser()
reader.read("config.ini")

SEPARATOR = "/"
JENKINS_PATH_SEPARATOR = " » "
JENKINS_JOB_PREFIX = " #"
OUTPUT_DIR = reader.get("APP", "OUTPUT_DIR")
PRIMARY_KEY = reader.get("JENKINS", "PRIMARY_KEY")

META_COLS = ['_class', 'actions', 'artifacts', 'building', 'description',
             'displayName', 'duration', 'estimatedDuration', 'executor',
             'fullDisplayName', 'id', 'keepLog', 'number', 'queueId', 'result',
             'timestamp', 'url', 'builtOn', 'changeSet', 'culprits',
             'changeSets', 'nextBuild', 'previousBuild']

LOGS_COLS = ['fullDisplayName', 'timestamp', 'consoleText']
FULL_PATH_COL = "fullPath"
ACTIONS_SOURCE = "actions"
TIME_IN_QUEUE_ACTION_KEYS = ['blockedDurationMillis', 'blockedTimeMillis', 'buildableDurationMillis',
                             'buildableTimeMillis', 'buildingDurationMillis', 'executingTimeMillis',
                             'executorUtilization', 'subTaskCount', 'waitingDurationMillis', 'waitingTimeMillis']
TIME_IN_QUEUE_ACTION_COL = "TimeInQueueAction"

META_COLS_TO_KEEP = ['building', FULL_PATH_COL,
                     'displayName', 'duration', 'estimatedDuration', 'executor',
                     'fullDisplayName', 'id', 'keepLog', 'number', 'queueId', 'result',
                     'timestamp', 'url', 'builtOn'] + TIME_IN_QUEUE_ACTION_KEYS

CULPRITS_COLS_TO_KEEP = "fullDisplayName,timestamp,fullName,url".split(",")


def get_meta_files():
    return [f.path for f in os.scandir(OUTPUT_DIR) if f.name.endswith("meta.csv")]


def get_log_files():
    return [f.path for f in os.scandir(OUTPUT_DIR) if f.name.endswith("logs.csv")]


def get_culprit_files():
    return [f.path for f in os.scandir(OUTPUT_DIR) if f.name.endswith("culprits.csv")]


def past_scrapes_job_ids(standardize=True):
    fs = get_meta_files()
    if len(fs) != 0:
        df = pd.read_csv(fs[0])[PRIMARY_KEY]
        for i in range(1, len(fs)):
            df_temp = pd.read_csv(fs[i])[PRIMARY_KEY]
            df = pd.concat([df, df_temp])
        df.drop_duplicates(inplace=True)
        temp_list = df.tolist()
        return set(map(standardize_full_display_name, temp_list)) if standardize else temp_list
    else:
        return []


def non_standard_to_path_components(full_display_name: str):
    if full_display_name.count(JENKINS_PATH_SEPARATOR) != 0:
        temp = [d.strip() for d in full_display_name.split(JENKINS_PATH_SEPARATOR)]
        dir_and_id = temp[-1].split(JENKINS_JOB_PREFIX)
        return temp[0:-1] + dir_and_id


def standardize_full_display_name(full_display_name):
    try:
        temp = non_standard_to_path_components(full_display_name)
        temp = SEPARATOR.join(temp)
        return temp
    except:
        logging.info("Value passed to `standardize_full_display_name` is not an iterable.", full_display_name)
        return full_display_name


def path_components_from_standard(full_display_name):
    return full_display_name.split(SEPARATOR)


def path_components_to_standard(list_of_components):
    return SEPARATOR.join(list_of_components)


def path_components_to_non_standard(list_of_components: list[str]):
    if len(list_of_components) != 0:
        if list_of_components[-1].isdigit():
            rest = list_of_components[0:-1]
            list_of_components = JENKINS_PATH_SEPARATOR.join(rest) + JENKINS_JOB_PREFIX + list_of_components[-1]
    return JENKINS_PATH_SEPARATOR.join(map(str, list_of_components))


def standardize_fullname_in_df(path_or_df):
    df = pd.read_csv(path_or_df) if type(path_or_df) is str else path_or_df
    if PRIMARY_KEY in df.columns:
        df[PRIMARY_KEY] = df[PRIMARY_KEY].map(standardize_full_display_name)
        return df


def standardize_past_files(list_of_some_logs):
    standardized = [(standardize_fullname_in_df(f), f) for f in list_of_some_logs]
    for df, path in standardized:
        df.to_csv(path, index=False)


def combine_logs(list_of_paths, maybe_output_path=None, cols_to_keep=None):
    dfs = [pd.read_csv(m) for m in list_of_paths]
    combined = pd.concat(dfs).drop_duplicates()
    if cols_to_keep is not None:
        combined = combined[cols_to_keep]
    if maybe_output_path is not None:
        combined.to_csv(maybe_output_path, index=False)
    return combined


def generate_combined_files():
    combined_meta = combine_logs(get_meta_files(), maybe_output_path=f"{OUTPUT_DIR}/meta_all.csv",
                                 cols_to_keep=META_COLS_TO_KEEP)
    combined_logs = combine_logs(get_log_files(), maybe_output_path=f"{OUTPUT_DIR}/logs_all.csv",
                                 cols_to_keep=LOGS_COLS)
    combined_culprits = combine_logs(get_culprit_files(), maybe_output_path=f"{OUTPUT_DIR}/culprits_all.csv",
                                     cols_to_keep=CULPRITS_COLS_TO_KEEP)
    return combined_meta, combined_logs, combined_culprits


def millis_to_datetime(millis):
    return datetime.fromtimestamp(millis / 1000)


def process_culprits(meta_df):
    culprits_df = meta_df[["fullDisplayName", "timestamp", "culprits"]]
    culprits_df.loc[:, "culprits"] = culprits_df.culprits.map(lambda x: eval(x) if type(x) is str else x)

    row_template = {"fullDisplayName": "", "timestamp": "", "fullName": "", "url": ""}
    new_rows = []

    for row_index in range(0, culprits_df.shape[0]):
        row_commons = culprits_df.iloc[row_index, [0, 1]].to_dict()
        row_culprits = culprits_df.iloc[row_index, 2]
        new_row = row_template.copy()
        new_row.update(row_commons)

        if len(row_culprits) > 0:
            for culprit in row_culprits:
                temp = new_row.copy()
                temp["fullName"] = culprit.get("fullName", "")
                temp["url"] = culprit.get("absoluteUrl", "")
                new_rows.append(temp)
        else:
            new_rows.append(new_row)
    return pd.DataFrame(new_rows)


def extract_TimeInQueueAction(df: pd.DataFrame):
    def extract_helper(col_value):
        if type(col_value) is str:
            col_list = eval(col_value)
        TimeInQueueAction = [l for l in col_list if l.get("_class", "") == "jenkins.metrics.impl.TimeInQueueAction"]
        return TimeInQueueAction[0] if len(TimeInQueueAction) != 0 else {}

    source_col = ACTIONS_SOURCE
    if source_col in df.columns:
        df[TIME_IN_QUEUE_ACTION_COL] = df[source_col].map(extract_helper)
    return df


def flatten_TimeInQueueAction(df: pd.DataFrame):
    default_value = {k: "na" for k in TIME_IN_QUEUE_ACTION_KEYS}

    def extract_helper(col_value):
        if type(col_value) is str:
            col_value = eval(col_value)
        if type(col_value) is dict:
            if "_class" in col_value.keys():
                del (col_value["_class"])
            new_cols = col_value
        if len(new_cols) != len(TIME_IN_QUEUE_ACTION_KEYS):
            logging.logger.warning(f"Length of new cols is not the same as TIME_IN_QUEUE_ACTION_KEYS: {col_value}")
            new_cols = default_value
        return new_cols

    if TIME_IN_QUEUE_ACTION_COL in df.columns:
        extracted = df[TIME_IN_QUEUE_ACTION_COL].map(extract_helper).to_list()
        new = pd.concat([df, pd.DataFrame(extracted)], axis=1)
        df = new
    return df


def get_path_from_fullDisplayName(df):
    df[FULL_PATH_COL] = (df["fullDisplayName"].map(lambda x: "/".join(x.split("/")[0:-1])))
    return df


def add_TimeInQueueAction_columns(df):
    if TIME_IN_QUEUE_ACTION_COL not in df.columns:
        df = extract_TimeInQueueAction(df)
    if len(set(df.columns.tolist()).difference(set(TIME_IN_QUEUE_ACTION_KEYS))) != 0:
        df = flatten_TimeInQueueAction(df)
    return df
