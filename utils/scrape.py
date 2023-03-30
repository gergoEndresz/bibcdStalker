import concurrent
import configparser
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib import request
from utils import transform
import time

reader = configparser.ConfigParser()
reader.read("config.ini")

BASE_URL = reader.get("JENKINS", "URL")


reader = configparser.ConfigParser()
reader.read("config.ini")

BASE_URL = reader.get("JENKINS", "URL")


def get_api_path(folders:list, job_id=None):
    path = ""
    if type(folders) is list:
        path += "".join([f"/job/{folder}" for folder in folders])
        path += f"/{job_id}" if job_id is not None else ""
        path += "/api/json"
    return path


def request_url(folders, job_id=None, base_url=BASE_URL):
    return f"{base_url}{get_api_path(folders, job_id)}"


def get_and_decode(path_components: list[str]):
    processed_response = {}
    try:
        url = request_url(path_components)
        resp = request.urlopen(url).read().decode("UTF-8")
        processed_response = json.loads(resp)
    except:
        logging.error(f"There has been an error when parsing the following url: {url}", resp)
    return processed_response, path_components


def extract_jobs(decoded, names_only=False):
    extracted = []
    if decoded.get("jobs") is not None and len(decoded.get("jobs")) != 0:
        extracted = decoded["jobs"] if not names_only else [j["name"] for j in decoded["jobs"]]
    return extracted


def extract_tasks(decoded:dict, numbers_only=False):
    extracted = []
    if decoded.get("builds") is not None:
        extracted = decoded["builds"] if not numbers_only else [j["number"] for j in decoded["builds"]]
    return extracted


def scan_for_jobs(base_path_components):
    decoded, _ = get_and_decode(base_path_components)
    start_names = extract_jobs(decoded, names_only=True)
    names_queue = [base_path_components + [name] for name in start_names]
    names_return = names_queue.copy()
    tasks_return = []
    tasks_already_scanned = transform.past_scrapes_job_ids(standardize=True)

    print(f"Scaning job paths with base path {get_api_path(base_path_components)} has started.\n")

    with ThreadPoolExecutor(max_workers=64) as EXECUTOR:
        while len(names_queue) != 0:
            print(f"Processing next {len(names_queue)} job paths.")
            futures = [EXECUTOR.submit(get_and_decode, comps_for_future) for comps_for_future in names_queue]
            names_queue = []
            for future in concurrent.futures.as_completed(futures, 60):

                decoded, components_temp = future.result()
                names_temp = extract_jobs(decoded, names_only=True)
                if len(names_temp) != 0:
                    components_new = [components_temp + [name] for name in names_temp]
                    names_queue.extend(components_new)
                    names_return.extend(components_new)
                else:
                    numbers_temp = extract_tasks(decoded, numbers_only=True)
                    tasks_new = [components_temp + [str(number)] for number in numbers_temp]
                    tasks_diff = set(map(transform.path_components_to_standard, tasks_new)).difference(
                        tasks_already_scanned)

                    mapped_diff = map(transform.path_components_from_standard, tasks_diff)

                    tasks_return.extend(mapped_diff)
    print(
        f"Scaning job paths with base path {get_api_path(base_path_components)} has finished.\nFound paths: {len(names_return)}, \nFound new tasks: {len(tasks_return)}")
    return names_return, tasks_return


def task_helper(comps, retries=3):
    parsed_response = {}
    for i in range(0, retries):
        try:
            current_url = request_url(comps[0:-1], comps[-1])
            resp = request.urlopen(current_url).read().decode("UTF-8")
            parsed_response = json.loads(resp)
            log_url = current_url.replace("api/json", "consoleText")
            parsed_response["consoleText"] = request.urlopen(log_url, timeout=30).read().decode("UTF-8")
            break
        except Exception as e:
            if i == retries:
                print(f"Request for the url {current_url} has failed after {retries} retries.")
            else:
                sleep_time = 2 ** (i + 1)
                print(f"Request for the url {current_url} has failed with error {e}. Retrying in {sleep_time} second..")
                time.sleep(sleep_time)
    return parsed_response


def scan_for_task(jobs):
    list_of_runs = []

    with ThreadPoolExecutor(max_workers=4) as EXECUTOR:
        futures = [EXECUTOR.submit(task_helper, job) for job in jobs]
        print(f"Parsing results for {len(futures)} urls.")
        for idx, future in enumerate(concurrent.futures.as_completed(futures, 60)):
            print(f"Has parsed the first {idx + 1} logs. {len(jobs) - idx - 1} is left.")
            parsed_response = future.result()
            if len(parsed_response) > 0:
                list_of_runs.append(parsed_response)
            list_of_runs.append(parsed_response)

    return list_of_runs


def scan_for_task_sync(jobs):
    list_of_runs = []

    for idx, job in enumerate(jobs):
        print(f"Has parsed the first {idx + 1} logs. {len(jobs) - idx - 1} is left.")
        parsed_response = task_helper(job)
        if len(parsed_response) > 0:
            list_of_runs.append(parsed_response)
    return list_of_runs

