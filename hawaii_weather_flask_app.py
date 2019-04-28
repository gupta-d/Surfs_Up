# Import libraries
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect, desc, Date, cast

import numpy as np
import pandas as pd
from matplotlib import style
import matplotlib.pyplot as plt

from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta



#################################################
# Flask Setup
from flask import Flask, jsonify
app = Flask(__name__)
#################################################

# Dictionary of flask app API's
API_info = [
     {"/api/v1.0/precipitation": "Returns past 12 months' precipation data"},
     {"/api/v1.0/stations": "Returns list of stations"},
     {"/api/v1.0/tobs": "Returns past 12 months' temp observations"},
     {"/api/v1.0/<start>": "Returns min/avg/max temp from supplied date onwards"},
     {"/api/v1.0/<start>/<end>": "Returns min/avg/max temp between a start and end date"},
     ]

####### initializing sqlalchemy environment ###########
# starting a sqlalchemy engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Create objects for ORM
Measurement = Base.classes.measurement
Station = Base.classes.station

# sessions will be created in individual flask route definitions below to avoid errors thread references


# Flask Routes
#################################################

@app.route("/")
def home_page():
	print("Home page..")
	return jsonify(API_info) 
#################################################

@app.route("/api/v1.0/precipitation")

def precipation():

    print("Server received request for precipation...")
    session = Session(engine) # start sqlalchemy ORM session

	# Get date of last record in database and date 12 months before it
    latest_date = session.query(Measurement.date).order_by(desc(Measurement.date)).first()[0]
    latest_date1 = datetime.strptime(latest_date, "%Y-%m-%d")
    one_year_ago = latest_date1 - relativedelta(years=1)
    one_year_ago1 = one_year_ago.strftime("%Y-%m-%d")

  
    # query to get 12 months data and save in a pandas dataframe, set index to date
    df = pd.read_sql(session.query(Measurement.date, func.avg(Measurement.prcp).label('prcp')).group_by(Measurement.date).filter(Measurement.date > one_year_ago1).order_by((Measurement.date)).statement, session.bind)
    df.set_index('date', drop=True, inplace=True)
    df.prcp = round(df.prcp,2)
    #convert dataframe to dictionary for returning the data
    dict_prcp = df.to_dict(orient ='dict')
    return jsonify(dict_prcp)

################################################	

@app.route("/api/v1.0/stations")

def stations():
    print("Server received request for stations list...")
    session = Session(engine) # start sqlalchemy ORM session

    # Query desired data from database, convert to dictionary and returns
    df = pd.read_sql(session.query(Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).statement, session.bind)
    dict_stations = df.to_dict(orient ='records')
    return jsonify(dict_stations)
#################################################

@app.route("/api/v1.0/tobs")
def tobs():
    print("Server received request for temperature observations...")
    session = Session(engine) # start sqlalchemy session

    # Get date of latest record in database and date 12 months before it
    latest_date = session.query(Measurement.date).order_by(desc(Measurement.date)).first()[0]
    latest_date1 = datetime.strptime(latest_date, "%Y-%m-%d")
    one_year_ago = latest_date1 - relativedelta(years=1)
    one_year_ago1 = one_year_ago.strftime("%Y-%m-%d")

    # Query to get 12 months data and save in a pandas dataframe, set index to date
    session = Session(engine)
    df = pd.read_sql(session.query(Measurement.date, func.avg(Measurement.tobs).label('tobs')).group_by(Measurement.date).filter(Measurement.date > one_year_ago1).order_by((Measurement.date)).statement, session.bind)
    df.set_index('date', drop=True, inplace=True)
    df.tobs = round(df.tobs,2)
    
    #convert dataframe to dictionary for returning the data
    dict_tobs = df.to_dict(orient ='dict')
    return jsonify(dict_tobs)

################################################

@app.route("/api/v1.0/<start>")
def starting(start):
    print(f"Server received request for data starting from {start}")
    session = Session(engine) #start sqlalchemy ORM session

    try:
        # convert start date string input to datetime, compare with oldest/latest record in databse to check if data exists from this date
        start_date_str = start
        start_date_dt = datetime.strptime(start, "%Y-%m-%d")
        earliest_date_str = session.query(Measurement.date).order_by(Measurement.date).first()[0]
        earliest_date_dt = datetime.strptime(earliest_date_str, "%Y-%m-%d")
        #earliest_date_str = session.query(Measurement.date).order_by(Measurement.date).first()[0]
    	#earliest_date_dt = datetime.strptime(earliest_date_str, "%Y-%m-%d")
        latest_date_str = session.query(Measurement.date).order_by(desc(Measurement.date)).first()[0]
        latest_date_dt = datetime.strptime(latest_date_str, "%Y-%m-%d")
    except:
        return f"ensure you have entered a valid date in YYYY-MM-DD format"


    if (start_date_dt<=latest_date_dt) and (start_date_dt>=earliest_date_dt):
        try:
    	    df = pd.read_sql(session.query(Measurement.date, func.min(Measurement.tobs).label('TMIN'), func.avg(Measurement.tobs).label('TAVG'), func.max(Measurement.tobs).label('TMAX'))\
    	    	.group_by(Measurement.date).filter(Measurement.date >= start_date_str).order_by((Measurement.date)).statement, session.bind)
    	    df.set_index('date', drop=True, inplace=True)
    	    df.TMIN = round(df.TMIN,2)
    	    df.TAVG = round(df.TAVG,2)
    	    df.TMAX = round(df.TMAX,2)
    	    dict_tobs = df.to_dict(orient ='index')
    	    return jsonify(dict_tobs)
        except:
            return f"encountered error in fetching from database"
    elif (start_date_dt < earliest_date_dt):
        return f"sorry..but databse has records starting {earliest_date_str} only"
    elif (start_date_dt > latest_date_dt):
        return f"sorry..but databse has records upto {latest_date_str} only"
##########################################################################	

@app.route("/api/v1.0/<start>/<end>")
def start_to_end(start, end):
    print(f"Server received request for data from {start} to {end}")
    session = Session(engine)

    try:

        start_date_str = start
        start_date_dt = datetime.strptime(start, "%Y-%m-%d")

        end_date_str = end
        end_date_dt = datetime.strptime(end, "%Y-%m-%d")

        earliest_date_str = session.query(Measurement.date).order_by(Measurement.date).first()[0]
        earliest_date_dt = datetime.strptime(earliest_date_str, "%Y-%m-%d")

        latest_date_str = session.query(Measurement.date).order_by(desc(Measurement.date)).first()[0]
        latest_date_dt = datetime.strptime(latest_date_str, "%Y-%m-%d")
    except:
        return f"ensure you have entered a valid date in YYYY-MM-DD format"

    if (start_date_dt<=latest_date_dt) and (end_date_dt>=earliest_date_dt):
        try:
    	    df = pd.read_sql(session.query(Measurement.date, func.min(Measurement.tobs).label('TMIN'), func.avg(Measurement.tobs).label('TAVG'), func.max(Measurement.tobs).label('TMAX'))\
    	    	.group_by(Measurement.date).filter(Measurement.date <= end_date_str).filter(Measurement.date >=start_date_str).order_by((Measurement.date)).statement, session.bind)
    	    df.set_index('date', drop=True, inplace=True)
    	    df.TMIN = round(df.TMIN,2)
    	    df.TAVG = round(df.TAVG,2)
    	    df.TMAX = round(df.TMAX,2)
    	    dict_tobs1 = df.to_dict(orient ='index')
    	    return jsonify(dict_tobs1)
        except:
            return f"encountered error in fetching from database"

    elif (start_date_dt < earliest_date_dt):
        return f"sorry..but databse has records starting {earliest_date_str} only"
    elif (end_date_dt > latest_date_dt):
        return f"sorry..but databse has records upto {latest_date_str} only"
    else:
	    return (f" Sorry.. the records are available only from {earliest_date_str} to {latest_date_str}")

if __name__ == "__main__":
    app.run(debug=True)