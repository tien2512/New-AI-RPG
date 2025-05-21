class TradeManager:
    """Manages trade routes and shipments"""
    def __init__(self, db):
        self.db = db
        
    def update(self, time_delta):
        """Update all active shipments and generate new trade"""
        # Update existing shipments
        self.update_active_shipments(time_delta)
        
        # Generate NPC trade if needed
        self.generate_npc_trade(time_delta)
    
    def update_active_shipments(self, time_delta):
        """Move shipments along their routes and process arrivals"""
        # Get all in-transit shipments
        query = "SELECT * FROM shipments WHERE status = 'in_transit'"
        shipments = self.db.execute_query(query)
        
        current_time = datetime.now()
        
        for shipment in shipments:
            # Check if shipment has arrived
            if current_time >= shipment['expected_arrival_time']:
                # Process arrival
                self.process_shipment_arrival(shipment['id'])
            else:
                # Update progress (for UI purposes if needed)
                pass
    
    def process_shipment_arrival(self, shipment_id):
        """Process a shipment that has arrived at its destination"""
        # Get shipment details
        query = "SELECT * FROM shipments WHERE id = %s"
        shipment = self.db.execute_query(query, (shipment_id,))[0]
        
        # Get trade route details
        route_query = "SELECT * FROM trade_routes WHERE id = %s"
        route = self.db.execute_query(route_query, (shipment['trade_route_id'],))[0]
        
        # Check for mishaps based on route safety
        # Higher safety = less chance of loss
        loss_chance = max(5, 100 - route['safety_rating']) / 100
        
        if random.random() < loss_chance:
            # Shipment is lost (partial or complete)
            loss_percentage = random.uniform(0.3, 1.0)
            lost_quantity = int(shipment['quantity'] * loss_percentage)
            remaining_quantity = shipment['quantity'] - lost_quantity
            
            # Update shipment status
            if remaining_quantity <= 0:
                # Complete loss
                update_query = """
                    UPDATE shipments 
                    SET status = 'lost',
                        actual_arrival_time = NOW()
                    WHERE id = %s
                """
                self.db.execute_query(update_query, (shipment_id,))
                
                # Generate event about lost shipment
                self.events.create_trade_event("shipment_lost", {
                    'route_id': shipment['trade_route_id'],
                    'resource_id': shipment['resource_id'],
                    'quantity': shipment['quantity'],
                    'owner_type': shipment['owner_type'],
                    'owner_id': shipment['owner_id']
                })
                
                return
            else:
                # Partial loss, continue with reduced quantity
                shipment['quantity'] = remaining_quantity
        
        # Process successful delivery
        
        # Add goods to destination market
        self.market_manager.add_to_local_market(
            route['destination_id'], 
            shipment['resource_id'],
            shipment['quantity']
        )
        
        # Update shipment status to delivered
        update_query = """
            UPDATE shipments 
            SET status = 'delivered',
                actual_arrival_time = NOW()
            WHERE id = %s
        """
        self.db.execute_query(update_query, (shipment_id,))
        
        # If NPC shipment, pay the NPC entity
        if shipment['owner_type'] == 'npc':
            # Calculate payment based on goods value and distance
            self.pay_npc_for_shipment(shipment)
    
    def generate_npc_trade(self, time_delta):
        """Generate new NPC trade shipments based on market needs"""
        # This is a simplified implementation
        # In a full system, this would analyze supply/demand across markets
        # and create appropriate shipments
        
        # Get all active trade routes
        query = "SELECT * FROM trade_routes WHERE active = TRUE"
        routes = self.db.execute_query(query)
        
        for route in routes:
            # Determine if we should create a shipment on this route
            # Based on time since last shipment, route importance, etc.
            if self._should_generate_shipment(route['id'], time_delta):
                # Find resources that would be profitable to ship
                profitable_resources = self._find_profitable_trades(
                    route['source_id'],
                    route['destination_id']
                )
                
                if profitable_resources:
                    # Pick one resource to ship
                    resource = random.choice(profitable_resources)
                    
                    # Create the shipment
                    self.create_shipment(
                        trade_route_id=route['id'],
                        resource_id=resource['id'],
                        quantity=self._determine_shipment_quantity(resource, route),
                        owner_type='npc',
                        owner_id=self._select_merchant_npc(route)
                    )
    
    def create_shipment(self, trade_route_id, resource_id, quantity, owner_type, owner_id):
        """Create a new shipment"""
        # Get trade route details
        query = "SELECT * FROM trade_routes WHERE id = %s"
        route = self.db.execute_query(query, (trade_route_id,))[0]
        
        # Calculate expected travel time based on current conditions
        current_travel_time = route['current_travel_time']
        
        # Calculate departure and arrival times
        departure_time = datetime.now()
        expected_arrival_time = departure_time + timedelta(hours=current_travel_time)
        
        # Insert the shipment
        insert_query = """
            INSERT INTO shipments
            (trade_route_id, resource_id, quantity, 
             departure_time, expected_arrival_time, 
             status, owner_type, owner_id)
            VALUES (%s, %s, %s, %s, %s, 'in_transit', %s, %s)
            RETURNING id
        """
        shipment_id = self.db.execute_query(
            insert_query, 
            (trade_route_id, resource_id, quantity, 
             departure_time, expected_arrival_time,
             owner_type, owner_id)
        )[0]['id']
        
        # Remove resources from source location if this is an NPC shipment
        if owner_type == 'npc':
            # Deduct from source market
            source_market_query = """
                UPDATE market_listings
                SET available_quantity = available_quantity - %s
                WHERE location_id = %s AND resource_id = %s
                AND available_quantity >= %s
            """
            self.db.execute_query(
                source_market_query,
                (quantity, route['source_id'], resource_id, quantity)
            )
        
        return shipment_id