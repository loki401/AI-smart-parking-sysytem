
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import json
from datetime import datetime, timedelta
import os
import uuid
import hashlib
import random

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')

# Sample data for parking spots
parking_lot = {
    "name": "Downtown Central Garage",
    "address": "123 Main Street, Metropolis",
    "totalSpots": 36,
    "availableSpots": 14,
    "openingHours": "24/7",
    "pricing": {
        "hourly": 5.99,
        "daily": 24.99,
        "premium": 9.99,
    },
    "coordinates": {
        "lat": 40.7128,
        "lng": -74.0060
    }
}

# Additional parking locations for map view
parking_locations = [
    {
        "id": "downtown-central",
        "name": "Downtown Central Garage",
        "address": "123 Main Street, Metropolis",
        "totalSpots": 36,
        "availableSpots": 14,
        "coordinates": {"lat": 40.7128, "lng": -74.0060},
        "pricing": {"hourly": 5.99, "daily": 24.99}
    },
    {
        "id": "midtown-plaza",
        "name": "Midtown Plaza Parking",
        "address": "456 Park Avenue, Metropolis",
        "totalSpots": 50,
        "availableSpots": 22,
        "coordinates": {"lat": 40.7215, "lng": -73.9932},
        "pricing": {"hourly": 7.99, "daily": 29.99}
    },
    {
        "id": "riverside-lot",
        "name": "Riverside Parking Lot",
        "address": "789 River Road, Metropolis",
        "totalSpots": 28,
        "availableSpots": 6,
        "coordinates": {"lat": 40.7031, "lng": -74.0212},
        "pricing": {"hourly": 4.99, "daily": 19.99}
    },
    {
        "id": "station-garage",
        "name": "Central Station Garage",
        "address": "321 Transit Way, Metropolis",
        "totalSpots": 45,
        "availableSpots": 3,
        "coordinates": {"lat": 40.7506, "lng": -73.9935},
        "pricing": {"hourly": 8.99, "daily": 34.99}
    }
]

# Mock user database
users = {
    "user@example.com": {
        "email": "user@example.com",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "name": "John Doe",
        "vehicles": [
            {"plate": "ABC123", "make": "Toyota", "model": "Corolla", "color": "Blue"},
            {"plate": "XYZ789", "make": "Honda", "model": "Civic", "color": "Silver"}
        ],
        "payment_methods": [
            {"id": "card1", "type": "credit", "last4": "4242", "exp": "12/25"},
            {"id": "paypal1", "type": "paypal", "email": "john@example.com"}
        ]
    },
    "admin@example.com": {
        "email": "admin@example.com",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "name": "Admin User",
        "is_admin": True
    }
}

# Reservations database
reservations = []

# Generate reservation history for demo
for i in range(5):
    spot_id = f"{chr(65 + random.randint(0, 5))}-{random.randint(1, 6)}"
    start_time = datetime.now() - timedelta(days=random.randint(1, 30))
    end_time = start_time + timedelta(hours=random.randint(1, 8))
    
    reservations.append({
        "id": str(uuid.uuid4()),
        "user_email": "user@example.com",
        "spot_id": spot_id,
        "parking_lot_id": "downtown-central",
        "start_time": start_time.strftime("%Y-%m-%d %H:%M"),
        "end_time": end_time.strftime("%Y-%m-%d %H:%M"),
        "vehicle_plate": "ABC123",
        "status": "completed",
        "amount_paid": round(5.99 * (end_time - start_time).total_seconds() / 3600, 2)
    })

# Add a few active/upcoming reservations
for i in range(2):
    spot_id = f"{chr(65 + random.randint(0, 5))}-{random.randint(1, 6)}"
    start_time = datetime.now() + timedelta(days=random.randint(1, 7))
    end_time = start_time + timedelta(hours=random.randint(1, 4))
    
    reservations.append({
        "id": str(uuid.uuid4()),
        "user_email": "user@example.com",
        "spot_id": spot_id,
        "parking_lot_id": "downtown-central",
        "start_time": start_time.strftime("%Y-%m-%d %H:%M"),
        "end_time": end_time.strftime("%Y-%m-%d %H:%M"),
        "vehicle_plate": "XYZ789",
        "status": "upcoming",
        "amount_paid": round(5.99 * (end_time - start_time).total_seconds() / 3600, 2)
    })

# Generate parking spots with different statuses
def generate_parking_spots(occupied_spots=None):
    if occupied_spots is None:
        occupied_spots = []
        
    spots = []
    status_distribution = {
        "available": 14,
        "occupied": 13,
        "reserved": 5,
        "premium": 2,
        "disabled": 2,
    }
    
    spot_count = {
        "available": 0,
        "occupied": 0,
        "reserved": 0,
        "premium": 0,
        "disabled": 0,
    }
    
    for i in range(1, parking_lot["totalSpots"] + 1):
        spot_id = f"{chr(65 + (i - 1) // 6)}-{((i - 1) % 6) + 1}"
        
        # Check if spot is in occupied list
        if spot_id in occupied_spots:
            status = "occupied"
            spot_count["occupied"] += 1
        else:
            status = "available"
            
            # Determine spot status based on distribution
            for status_type in ["available", "occupied", "reserved", "premium", "disabled"]:
                if spot_count[status_type] < status_distribution[status_type]:
                    status = status_type
                    spot_count[status_type] += 1
                    break
        
        price = parking_lot["pricing"]["premium"] if status == "premium" else parking_lot["pricing"]["hourly"]
        
        spots.append({
            "id": spot_id,
            "status": status,
            "price": price
        })
    
    return spots

# Routes
@app.route('/')
def index():
    parking_spots = generate_parking_spots()
    current_year = datetime.now().year
    return render_template('index.html', 
                          parking_spots=parking_spots, 
                          parking_lot=parking_lot, 
                          current_year=current_year,
                          now_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/parking/<spot_id>')
def parking_details(spot_id):
    parking_spots = generate_parking_spots()
    spot = next((spot for spot in parking_spots if spot["id"] == spot_id), None)
    
    if not spot:
        return redirect(url_for('index'))
    
    return render_template('parking_details.html', 
                          spot=spot, 
                          parking_lot=parking_lot,
                          current_year=datetime.now().year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in users:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if users[email]['password_hash'] == password_hash:
                session['user_email'] = email
                session['user_name'] = users[email]['name']
                session['is_admin'] = users[email].get('is_admin', False)
                
                next_page = request.args.get('next', 'index')
                return redirect(url_for(next_page))
        
        error = "Invalid email or password"
    
    return render_template('login.html', error=error, current_year=datetime.now().year)

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    session.pop('user_name', None)
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if email in users:
            error = "Email already registered"
        else:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            users[email] = {
                "email": email,
                "password_hash": password_hash,
                "name": name,
                "vehicles": [],
                "payment_methods": []
            }
            
            session['user_email'] = email
            session['user_name'] = name
            return redirect(url_for('index'))
    
    return render_template('register.html', error=error, current_year=datetime.now().year)

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login', next='dashboard'))
    
    user_email = session['user_email']
    user = users[user_email]
    
    # Get user's reservations
    user_reservations = [r for r in reservations if r['user_email'] == user_email]
    
    return render_template('dashboard.html', 
                          user=user, 
                          reservations=user_reservations,
                          current_year=datetime.now().year)

@app.route('/map')
def map_view():
    return render_template('map.html', 
                          parking_locations=parking_locations,
                          current_year=datetime.now().year)

@app.route('/api/reserve', methods=['POST'])
def reserve_spot():
    if 'user_email' not in session:
        return jsonify({"success": False, "message": "Please log in to reserve a spot"})
    
    data = request.json
    spot_id = data.get('spotId')
    arrival_date = data.get('arrivalDate')
    arrival_time = data.get('arrivalTime')
    departure_date = data.get('departureDate')
    departure_time = data.get('departureTime')
    vehicle_plate = data.get('vehiclePlate')
    
    # Create arrival and departure datetime
    start_datetime = f"{arrival_date} {arrival_time}"
    end_datetime = f"{departure_date} {departure_time}"
    
    # Calculate duration and cost
    start = datetime.strptime(start_datetime, '%Y-%m-%d %H:%M')
    end = datetime.strptime(end_datetime, '%Y-%m-%d %H:%M')
    duration_hours = (end - start).total_seconds() / 3600
    
    # Get parking spot
    parking_spots = generate_parking_spots()
    spot = next((s for s in parking_spots if s["id"] == spot_id), None)
    
    if not spot:
        return jsonify({"success": False, "message": "Invalid parking spot"})
    
    if spot["status"] != "available":
        return jsonify({"success": False, "message": "Spot is no longer available"})
    
    # Calculate cost
    cost = spot["price"] * duration_hours
    
    # Create reservation
    reservation_id = str(uuid.uuid4())
    new_reservation = {
        "id": reservation_id,
        "user_email": session['user_email'],
        "spot_id": spot_id,
        "parking_lot_id": "downtown-central",
        "start_time": start_datetime,
        "end_time": end_datetime,
        "vehicle_plate": vehicle_plate,
        "status": "upcoming",
        "amount_paid": round(cost, 2)
    }
    
    # Add to reservations
    reservations.append(new_reservation)
    
    return jsonify({
        "success": True, 
        "message": "Spot reserved successfully",
        "reservation": new_reservation
    })

@app.route('/api/cancel-reservation/<reservation_id>', methods=['POST'])
def cancel_reservation(reservation_id):
    if 'user_email' not in session:
        return jsonify({"success": False, "message": "Please log in to cancel a reservation"})
    
    reservation = next((r for r in reservations if r['id'] == reservation_id), None)
    
    if not reservation:
        return jsonify({"success": False, "message": "Reservation not found"})
    
    if reservation['user_email'] != session['user_email']:
        return jsonify({"success": False, "message": "Not authorized to cancel this reservation"})
    
    # Update reservation status
    reservation['status'] = 'cancelled'
    
    return jsonify({
        "success": True, 
        "message": "Reservation cancelled successfully"
    })

@app.route('/api/parking-lots')
def get_parking_lots():
    return jsonify(parking_locations)

if __name__ == '__main__':
    app.run(debug=True)
