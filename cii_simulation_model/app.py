from flask import Flask, request, jsonify
from flask_cors import CORS
from waitress import serve
import logging
from model import fscurve

app = Flask(__name__)
CORS(app)

app.temp_response = None


@app.route('/get_fscurve', methods=['POST'])
def GetFScurve():
    res = {"data": []}
    try:
        req = request.json

        # simulation_type_id is 1 = Desired CII
        # simulation_type_id is 2 = Desired Schedule

        if (req["simulation_type_id"] == 1):
            res["data"] = fscurve(req["vessel_id"], req["mean_draft"])
        elif (req["simulation_type_id"] == 2):
            res["data"] = fscurve(
                req["vessel_id"], req["mean_draft"], req["speed"])

        res["ErrorCode"] = "9999"
    except Exception as e:
        logging.error(e)
        res["ErrorCode"] = "0000"
        res["data"] = "Server Error"
    return jsonify(res)


if __name__ == '__main__':
    logging.basicConfig(filename='logging.log', level=logging.ERROR,
                        format='%(asctime)s - [%(filename)s:%(lineno)d] - %(funcName)20s() %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S')
    serve(app, host='0.0.0.0', port=5004)
    # port (DEV,UAT,STG) = 5002
    # port (PROD) = 5004
