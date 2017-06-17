import os
import json
import urllib.parse

from flask import request, jsonify

from flaskapp.routes import routes_module
from flaskapp.process.file_handle import make_new_file_name
from flaskapp.process.chem_process import parse_file
from flaskapp.process.json_util import jsonify_mongo, show
import flaskapp.shared_variables as var

# Directory where uploaded files will be saved temporarily
dir_path = "flaskapp/uploads/"


# Upload a log file and view parsed info from it
@routes_module.route("/api/upload", methods=["POST"])
def upload_file_api():
    if request.method == "POST":
        f = request.files["file"]
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        new_log_file_name = make_new_file_name()
        f.save(new_log_file_name)
        d = parse_file(new_log_file_name)
        os.remove(new_log_file_name)
        return json.dumps(d, sort_keys=True)


# List molecules in database
@routes_module.route("/api/browse", methods=["POST"])
def browse_home_api():
    if request.method == "POST":
        try:
            db = var.mongo.db
            mols = db.molecule.find({}).sort("formula")
            mols = jsonify_mongo(list(mols))
            d = {
                "success": 1,
                "results": mols
            }
        except Exception as e:
            d = {
                "success": 0,
                "results": [],
                "message": e.args
            }
        return jsonify(d)


# List files for a molecule in database
@routes_module.route("/api/browse/<formula>", methods=["POST"])
def browse_molecule_api(formula):
    if request.method == "POST":
        try:
            formula = urllib.parse.unquote(formula)
        except Exception as e:
            d = {
                "success": 0,
                "formula": "",
                "results": [],
                "message": e.args
            }
            return d
        try:
            db = var.mongo.db
            mol_doc = db.molecule.find_one({"formula": formula})
        except Exception as e:
            d = {
                "success": 0,
                "formula": formula,
                "results": [],
                "message": e.args
            }
            return d
        docs = []
        try:
            if mol_doc is not None:
                ids = mol_doc["parsed_files"]
                docs = db.parsed_file.find({"_id": {"$in": ids}})
                docs = jsonify_mongo(list(docs))
                d = {
                    "success": 1,
                    "formula": formula,
                    "results": docs
                }
                return jsonify(d)
        except Exception as e:
            d = {
                "success": 0,
                "formula": formula,
                "results": [],
                "message": e.args
            }
            return d
