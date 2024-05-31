import datetime as dt
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

station = Base.classes.station
measurement = Base.classes.measurement

session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def homepage():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"- List of last year rain totals for all stations<br/>"
        f"<br/>"
        f"/api/v1.0/stations<br/>"
        f"- List of Station numbers and names<br/>"
        f"<br/>"
        f"/api/v1.0/tobs<br/>"
        f"- List of last year temperatures for all stations<br/>"
        f"<br/>"
        f"/api/v1.0/start/<start><br/>"
        f"- Giving the start date format: (YYYY-MM-DD), it will calculate the MIN/AVG/MAX temperature for all dates greater than and equal to the start date<br/>"
        f"<br/>"
        f"/api/v1.0/start/end/<start>/<end><br/>"
        f"- Giving the start and the end date format: (YYYY-MM-DD), it will calculate the MIN/AVG/MAX temperature for dates between the start and end date inclusive<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return a list of rain fall for prior year"""
    last_date = session.query(measurement.date).order_by(measurement.date.desc()).first()
    last_yr = dt.date(2017, 8, 23) - dt.timedelta(days=365)
    rain = session.query(measurement.date, measurement.prcp).\
        filter(measurement.date > last_yr).\
        order_by(measurement.date).all()

    rain_totals = []
    for result in rain:
        row = {}
        row["date"] = result.date
        row["prcp"] = result.prcp
        rain_totals.append(row)

    return jsonify(rain_totals)

@app.route("/api/v1.0/stations")
def stations():
    stations_query = session.query(station.name, station.station)
    stations = pd.read_sql(stations_query.statement, stations_query.session.bind)
    return jsonify(stations.to_dict())

@app.route("/api/v1.0/tobs")
def tobs():
    """Return a list of temperatures for prior year"""
    last_date = session.query(measurement.date).order_by(measurement.date.desc()).first()
    last_year = dt.date(2017, 8, 23) - dt.timedelta(days=365)
    temperature = session.query(measurement.date, measurement.tobs).\
        filter(measurement.date > last_year).\
        order_by(measurement.date).all()

    temp_totals = []
    for result in temperature:
        row = {}
        row["date"] = result.date
        row["tobs"] = result.tobs
        temp_totals.append(row)

    return jsonify(temp_totals)

@app.route("/api/v1.0/start/<start>")
def trip(start):
    try:
        start_date = dt.datetime.strptime(start, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD format."}), 400

    one_year_ago = start_date - dt.timedelta(days=365)
    
    # Retrieve the latest date from the database
    latest_date_query = session.query(func.max(measurement.date)).scalar()
    latest_date = dt.datetime.strptime(latest_date_query, '%Y-%m-%d')

    trip_data = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= one_year_ago).filter(measurement.date <= latest_date).all()

    trip_temps = list(np.ravel(trip_data))

    return jsonify(trip_temps)



@app.route("/api/v1.0/start/end/<start>/<end>")
def trip_range(start, end):
    try:
        start_date = dt.datetime.strptime(start, '%Y-%m-%d')
        end_date = dt.datetime.strptime(end, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD format."}), 400


    if start_date > end_date:
        return jsonify({"error": "Start date cannot be after end date."}), 400

    year_ago_start = start_date - dt.timedelta(days=365)
    year_ago_end = end_date - dt.timedelta(days=365)

    trip_data = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= year_ago_start).filter(measurement.date <= year_ago_end).all()

    trip_temps = list(np.ravel(trip_data))

    return jsonify(trip_temps)


if __name__ == "__main__":
    app.run(debug=True)


