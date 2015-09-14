import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup
import time

client = MongoClient()
database = client.coursecrunch
headers_collection = database.headers
metadata_collection = database.metadata
coursedata_collection = database.coursedata

API = "https://info.uwaterloo.ca/cgi-bin/cgiwrap/infocour/salook.pl"
TERM = "1159"
LEVEL = "under"
SUBJECT = "CS"
COURSE_NUM = "135"

COURSE_LIST = [
    {
        "subject": "CS",
        "course_numbers": [
            "115",
            "135",
            "145",
            "240",
            "241",
            "245",
            "246",
            "251",
        ]
    },
    {
        "subject": "MATH",
        "course_numbers": [
            "127",
            "135",
            "137",
            "145",
            "147",
            "235",
            "237",
            "235",
            "237",
            "239",
        ]
    },
]


def fetch(subject, course_num, term=TERM, level=LEVEL):
    """
    Fetches the Soup for a given course from the schedule

    TODO: determine if response is bad (like no data etc.)
    """
    payload = {
        "sess": term,
        "level": level,
        "subject": subject,
        "cournum": course_num,
    }

    result = requests.get(API, params=payload)
    soup = BeautifulSoup(result.text, 'html.parser')
    return soup

def process_headers(soup):
    """
    Processes out the headers for the tables (first 4 are outer table, rest are inner table)
    """
    headers = [x.get_text().strip() for x in soup.find("table").find_all("th")]
    return headers


def process_course_metadata(soup):
    """
    Processes out the course metadata
    """
    metadata = [x.get_text().strip() for x in soup.find("table").find_all("td")[:4]]
    return metadata

def process_data(soup):
    """
    Processes out the data for the table
    """
    data = []
    table = soup.find('table').find("table")

    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele]) # Get rid of empty values
    return data

def save_data(headers, metadata, course_data, subject, course_num):
    retrieve_time = int(time.time())

    headers_collection.insert_one({
        "time": retrieve_time,
        "subject": subject,
        "course_num": course_num,
        "data": headers,
    })

    metadata_collection.insert_one({
        "time": retrieve_time,
        "subject": subject,
        "course_num": course_num,
        "data": metadata,
    })

    coursedata_collection.insert_one({
        "time": retrieve_time,
        "subject": subject,
        "course_num": course_num,
        "data": course_data,
    })

if __name__ == "__main__":
    for subject_group in COURSE_LIST:
        subject = subject_group['subject']
        for course_num in subject_group['course_numbers']:
            try:
                soup = fetch(subject, course_num)
                headers = process_headers(soup)
                metadata = process_course_metadata(soup)
                course_data = process_data(soup)

                save_data(headers, metadata, course_data, subject, course_num)
            except Exception as err:
                print("Error with %s %s" % (subject, course_num))
                print("%s" % err)
