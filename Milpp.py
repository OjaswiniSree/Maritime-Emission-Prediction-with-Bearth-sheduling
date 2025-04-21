import time
from datetime import datetime, timedelta
from db import create_connection
import logging
import random

logging.basicConfig(level=logging.INFO)

berthing_lobby = {}
waiting_lobby = {}

berthing_capacity = 5
waiting_capacity = 15

ship_size_mapping = {"Small": 4, "Medium": 3, "Large": 2, "Ultra Large": 1}
berthing_time = {"Small": 8, "Medium": 16, "Large": 24, "Ultra Large": 32}
emission_index_mapping = {"High": 2, "Moderate": 1, "Low": 0}

priority_mapping = {
    "Emergencies (vessel damage)": 1,
    "Humanitarian aid & relief operation": 2,
    "Environmental concerns": 3,
    "Pre arranged priority": 4,
    "Deadlock Waiting": 5,
    "No priority": 6
}

available_berths = {berth: False for berth in range(1, berthing_capacity + 1)}

def check_status_and_departures():
    current_time = time.time()
    for ship_id, ship_info in list(berthing_lobby.items()):
        time_remaining = ship_info['berthing_time'] - (current_time - ship_info['arrival_time'])
        if time_remaining <= 0:
            ship_leaves(ship_id)
        else:
            time_remaining_str = str(timedelta(seconds=int(time_remaining)))
            print(f"Ship ID: {ship_id}, Berth Number: {ship_info['berth_number']}, Status: Berthing, Time Remaining: {time_remaining_str}")

def available_berths_check():
    available_berths_list = [berth for berth, status in available_berths.items() if not status]
    return random.choice(available_berths_list) if available_berths_list else None

def ship_arrives(ship_id, ship_size, ship_priority, ship_emission_index):
    print(f"Ship {ship_id} has arrived.")
    arrival_time = time.time()
    berth_number = available_berths_check()
    
    if berth_number is None:
        waiting_lobby[ship_id] = {
            "size": ship_size,
            "priority": ship_priority,
            "emission_index": ship_emission_index,
            "arrival_time": arrival_time
        }
        print(f"Ship {ship_id} is in the waiting lobby.")
        return

    available_berths[berth_number] = True  
    berthing_time_seconds = berthing_time[ship_size] * 3600
    berthing_lobby[ship_id] = {
        "size": ship_size,
        "priority": ship_priority,
        "emission_index": ship_emission_index,
        "arrival_time": arrival_time,
        "berth_number": berth_number,
        "berthing_time": berthing_time_seconds
    }
    
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(''' 
            UPDATE ship_infoo
            SET Berth = ?, from_time = ?, to_time = ? 
            WHERE id = ?
        ''', (int(berth_number), arrival_time, arrival_time + berthing_time_seconds, ship_id))
        conn.commit()
        conn.close()

    print(f"Ship {ship_id} assigned to Berth {berth_number}.")

def ship_leaves(ship_id):
    print(f"Ship {ship_id} has left.")
    if ship_id in berthing_lobby:
        berth_number = berthing_lobby[ship_id]['berth_number']
        available_berths[berth_number] = False
        del berthing_lobby[ship_id]
        print(f"Berth {berth_number} is now available.")
        vacancy_arises()

def vacancy_arises():
    if not waiting_lobby:
        return
    
    berth_number = available_berths_check()
    if berth_number is None:
        return
    
    sorted_ships = sorted(waiting_lobby.items(), key=lambda x: (priority_mapping[x[1]['priority']], x[1]['arrival_time']))
    selected_ship_id, selected_ship_info = sorted_ships[0]
    
    berthing_lobby[selected_ship_id] = {
        **selected_ship_info,
        "berth_number": berth_number,
        "berthing_time": berthing_time[selected_ship_info["size"]] * 3600
    }
    available_berths[berth_number] = True
    del waiting_lobby[selected_ship_id]
    print(f"Ship {selected_ship_id} moved to berth {berth_number}.")

if __name__ == "__main__":
    while True:
        if berthing_lobby or waiting_lobby:
            check_status_and_departures()
            time.sleep(1)
        else:
            print("No more ships in the system. Exiting...")
            break
