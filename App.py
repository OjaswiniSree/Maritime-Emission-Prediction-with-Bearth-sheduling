from flask import Flask, request, render_template
import joblib
import pandas as pd
import sqlite3
from db import create_connection, create_table
from Milpp import ship_arrives
from datetime import datetime

app = Flask(__name__)

# Load trained model
rf_classifier = joblib.load('trained_model.pkl')

# Read dataset to understand expected features
data = pd.read_csv("emissions_dataset2.csv")
X = data.drop(columns=['emissions'])  
expected_columns = list(X.columns) 

@app.route('/submit', methods=['POST'])
def submit():
    conn = create_connection()
    if conn is not None:
        create_table(conn)
        cursor = conn.cursor()

        try:
            # Get form data
            ship_type = request.form['ship-type']
            ship_size = int(request.form['ship-size'])
            vessel_age = int(request.form['vessel-age'])
            fuel_type = request.form['fuel-type']
            fuel_consumption = request.form['fuel-consumption']
            engine_type = request.form['engine-type']
            emission_control = request.form['emission-control']
            load_factor = float(request.form['load-factor'])
            priority = request.form['priority']

            # Convert fuel consumption to numeric
            fuel_consumption_mapping = {
                "Low": 0,
                "Medium": 1,
                "High": 2
            }
            fuel_consumption = fuel_consumption_mapping.get(fuel_consumption, -1)
            if fuel_consumption == -1:
                return "Error: Invalid fuel consumption value", 400

            # Log received data
            app.logger.info(f"Received Form Data: Ship Type: {ship_type}, Ship Size: {ship_size}, Vessel Age: {vessel_age}, Fuel Type: {fuel_type}, Fuel Consumption: {fuel_consumption}, Engine Type: {engine_type}, Emission Control: {emission_control}, Load Factor: {load_factor}")

            # Insert into database
            cursor.execute('''
                INSERT INTO ship_infoo (ship_type, ship_size, vessel_age, fuel_type, fuel_consumption, engine_type,
                                        emission_control_technologies, load_factor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ship_type, ship_size, vessel_age, fuel_type, fuel_consumption, engine_type, emission_control, load_factor))

            last_id = cursor.lastrowid
            app.logger.info(f"Inserted Ship ID: {last_id}")

            # Map fuel type to numeric
            fuel_type_mapping = {
                "Heavy Fuel Oil": 0,
                "Diesel": 1,
                "LNG": 2,
                "Biofuel": 3
            }
            fuel_type_numeric = fuel_type_mapping.get(fuel_type, -1)
            if fuel_type_numeric == -1:
                conn.rollback()
                return "Error: Unknown fuel type", 400

            # Map Engine Type to Numeric Values
            engine_type_mapping = {
                "Two-Stroke Diesel Engines": 0,
                "Four-Stroke Diesel Engines": 1,
                "Gas Turbine Engines": 2,
                "Electric Propulsion": 3
            }
            engine_type_numeric = engine_type_mapping.get(engine_type, -1)
            if engine_type_numeric == -1:
                conn.rollback()
                return "Error: Invalid engine type", 400

            # Convert Emission Control to Numeric
            emission_control_mapping = {
                "Yes": 1,
                "No": 0
            }
            emission_control_numeric = emission_control_mapping.get(emission_control, -1)
            if emission_control_numeric == -1:
                conn.rollback()
                return "Error: Invalid emission control value", 400

            # Prepare input data for prediction
            input_values = {
                "Ship Size": ship_size,
                "Vessel Age": vessel_age,
                "Fuel Consumption": fuel_consumption,
                "Engine Type": engine_type_numeric,
                "Emission Control Tech": emission_control_numeric,
                "Load Factor": load_factor,
            }

            # Ensure input values match model's expected features
            input_data = pd.DataFrame([input_values])
            for col in expected_columns:
                if col not in input_data:
                    input_data[col] = 0
            
            # Reorder columns to match model training order
            input_data = input_data[expected_columns]
            
            # Make prediction
            predicted_emissions = int(rf_classifier.predict(input_data)[0])

            # Update database with prediction
            cursor.execute('''
                UPDATE ship_infoo
                SET Emissions = ?
                WHERE id = ?
            ''', (predicted_emissions, last_id))

            conn.commit()
            app.logger.info(f"Prediction Updated for Ship ID: {last_id}")

            # Determine emission level and ship size
            emission_levels = {
                0: "Low",
                1: "Moderate",
                2: "High"
            }
            sizeOfShip_levels = {
                2: "Large",
                0: "Small",
                1: "Medium"
            }
            sizeOfShip = sizeOfShip_levels.get(ship_size)
            emission_level = emission_levels.get(predicted_emissions, "Unknown")

            # Call ship_arrives function
            ship_arrives(int(last_id), sizeOfShip, priority, emission_level)

            return render_template('check.html', status_message="Check your ship status.", ship_id=last_id, emission_level=emission_level)

        except Exception as e:
            conn.rollback()
            app.logger.error(f"Database Error: {e}")
            return "Error processing data", 500

        finally:
            conn.close()

    else:
        return 'Error: Unable to connect to the database'

@app.route('/check')
def check():
    ship_id = request.args.get('ship_id')
    emission_level=request.args.get('emission_level')
    # Connect to the database
    conn = create_connection()
    cursor = conn.cursor()
    
    # Retrieve the ship information from the database based on the ship_id
    cursor.execute('''
        SELECT Berth, from_time, to_time
        FROM ship_infoo
        WHERE id = ?
    ''', (ship_id,))
    ship_info = cursor.fetchone()  # Fetch one row
    
    # Close the database connection
    conn.close()
    
    # Check if ship_info is not None (i.e., ship_id exists in the database)
    if ship_info:
        berth, from_time, to_time = ship_info
        
        # app.logger.info(f"Ship {ship_id} has been assigned to Berth {berth} from {from_time_str} to {to_time_str}.")
        
        if berth == 0:
            # If the ship is in the waiting lobby, display a message
            return render_template('check.html', status_message="Your ship is in the waiting lobby.", ship_id=ship_id)
        else:
            # If the ship has been allocated a berth, form the message
            # Fix by adding:
            from_time_str = datetime.fromtimestamp(from_time).strftime('%Y-%m-%d %H:%M:%S')
            to_time_str = datetime.fromtimestamp(to_time).strftime('%Y-%m-%d %H:%M:%S')


            return render_template('result.html', berth=berth, from_time=from_time_str, to_time=to_time_str, emission_level=emission_level)

            
    else:
        # If ship_id does not exist in the database, display an error message
        return render_template('check.html', status_message="Ship ID not found in the database.",ship_id= ship_id)


@app.route('/result')
def result():
    ship_id = request.args.get('ship_id')
    emission_level = request.args.get('emission_level')

    app.logger.info(f"Received ship_id: {ship_id}, emission_level: {emission_level}") 

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT Berth, from_time, to_time FROM ship_infoo WHERE id = ?
    ''', (ship_id,))
    ship_info = cursor.fetchone()
    conn.close()

    if ship_info:
        berth, from_time, to_time = ship_info
        
        from_time_str = datetime.fromtimestamp(float(from_time)).strftime('%Y-%m-%d %H:%M:%S') if from_time else "N/A"
        to_time_str = datetime.fromtimestamp(float(to_time)).strftime('%Y-%m-%d %H:%M:%S') if to_time else "N/A"

        print(f"Retrieved from DB -> Berth: {berth}, From: {from_time_str}, To: {to_time_str}")  # Debugging

        return render_template('result.html', 
                               berth = str(berth) if berth else "Your Ship is Assigned to Waiting Area. We will notify you when it is available",
                               from_time=from_time_str, 
                               to_time=to_time_str, 
                               emission_level=emission_level)
    
    print("No berthing details found for this ship.")  # Debugging
    return render_template('result.html', 
                           berth="Your Ship is Assigned to Waiting Area. We will notify you when it is available", 
                           from_time="N/A", 
                           to_time="N/A", 
                           emission_level=emission_level)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/intimate')
def intimate():
    return render_template('intimate.html')

@app.route('/contactus')
def contactus():
    return render_template('contactus.html')

@app.route('/form')
def form():
    return render_template('form.html')


if __name__ == '__main__':
    app.run(debug=True)
