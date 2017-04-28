import math
import os
import sys
import json
import pymongo
import cclib

import config
from process import processFile

# Default values
default_db_host = config.mongo_host
default_db_port = config.mongo_port
default_db_name = config.mongo_name
db_collection_name = config.mongo_collection
# Store count of processed files
success_count = 0
# Modify database (1) or just loop through files and parse them (0)
insert_mode = 1
# Unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)


def main():
    message = (
        "\nThis script will seed mongodb database by parsing info from "
        "computational chemistry output files\n"
        "Ensure that :\n"
        "1. You have mongodb setup on your/remote machine\n"
        "2. Data files ( .out , .log etc) are present on your machine "
        "in a read-accessible folder\n"
    )
    print(message)
    choice = input("Proceed to setup database (N/y) : ")
    if choice == "y" or choice == "Y":
        try:
            db_conn = pymongo.MongoClient(default_db_host, int(default_db_port))
            db = db_conn[default_db_name]
            db_cursor = db[db_collection_name]

            message = "Path to folder containing data files : "
            data_folder_path = input(message)
            if data_folder_path == "":
                data_folder_path = default_data_folder_path
            if os.path.isdir(data_folder_path):
                    if insert_mode == 1:
                        db_cursor.delete_many({})
                    iterate(data_folder_path, db_cursor, insert_mode)
                    print("\nDone!")
                    print("-" * 50)
            else:
                print("This folder was not found")
        except Exception as e:
            print("\nCannot setup database")
            print("-" * 50)
            print(e.message)
            print("-" * 50)


# Recursively iterate through files in a directory
def iterate(dir_path, db_cursor, insert_mode=0):
    if not(dir_path.endswith("/")):
        dir_path = dir_path + "/"
    for file_name in os.listdir(dir_path):
        f = dir_path + file_name
        if os.path.isfile(f):
            add_file_to_database(f, db_cursor, insert_mode)
        elif os.path.isdir(f):
            iterate(f, db_cursor, insert_mode)


# Process a file and add to database if parsing was successful
def add_file_to_database(file_path, db_cursor, insert_mode=0):
    print("Processing file : ", file_path, ". . . ", end="")
    res = processFile(file_path)
    if res["success"]:
        if "formula_string" not in res["attributes"]:
            print("  Failed: Unable to determine molecular formula")
        else:
            global success_count
            success_count  += 1
            print("  Done!")
            if insert_mode == 1:
                insert_data(res["attributes"], db_cursor)
    else:
        print("  Failed: Unable to parse the file")


# Insert given parsed data in database
def insert_data(data, db_cursor):
    formula = data["formula_string"]
    res = db_cursor.find_one({"formula": formula},{"_id":1})
    try:
        if res is None:
            db_cursor.insert_one({"formula": formula, "log_files": [data]})
        else:
            db_cursor.update_one({"_id": res["_id"]},
                                 {"$push": {"log_files": data}})
    except Exception as e:
        print("Error in inserting document")
        print("-" * 50)
        print(e)
        print("-" * 50)
        pass


# Function to get distances between atoms of molecule
def distance_list(atom_coords):
    dist_list = []
    l = len(atom_coords)
    for i in range(l):
        for j in range(l):
            if i != j:
                dist_list.append(distance(atom_coords[i],atom_coords[j]))
    dist_list.sort()
    return dist_list


# Utility function to compute distance between 2 atom coordinates
def distance(p1, p2):
    sq_sum = 0
    for i in range(3):
        sq_sum  += (p1[i]-p2[i])**2
    return math.sqrt(sq_sum)


# Utility function to display indented JSON data
def show(d):
    print(json.dumps(d,indent=4))


if __name__ == '__main__':
    main()
