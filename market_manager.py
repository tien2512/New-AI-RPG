class MarketManager:
    """Handles market prices and trading"""
    def __init__(self, db):
        self.db = db
        
    def update(self, time_delta):
        """Update all markets' prices based on supply and demand"""
        # Get all market listings
        query = "SELECT * FROM market_listings"
        listings = self.db.execute_query(query)
        
        for listing in listings:
            # Calculate new price
            new_price = self.calculate_price(
                listing['location_id'], 
                listing['resource_id'],
                listing['available_quantity'],
                listing['demand_level'],
                listing['base_price']
            )
            
            # Update the price
            self.update_price(listing['id'], new_price)
            
            # Record price history
            self.record_price_history(listing['id'], new_price, listing['available_quantity'])
    
    def calculate_price(self, location_id, resource_id, quantity, demand, base_price):
        """Calculate the current price based on multiple factors"""
        # Get the location data for regional factors
        location_query = "SELECT * FROM locations WHERE id = %s"
        location = self.db.execute_query(location_query, (location_id,))[0]
        
        # Get the resource data
        resource_query = "SELECT * FROM resources WHERE id = %s"
        resource = self.db.execute_query(resource_query, (resource_id,))[0]
        
        # Get active economic events affecting this resource/location
        event_query = """
            SELECT ee.* FROM event_effects ee
            JOIN economic_events e ON ee.event_id = e.id
            WHERE e.active = TRUE
            AND ((ee.target_type = 'resource' AND ee.target_id = %s)
                OR (ee.target_type = 'location' AND ee.target_id = %s))
            AND ee.effect_type = 'price'
        """
        events = self.db.execute_query(event_query, (resource_id, location_id))
        
        # Calculate supply factor (inverse relationship)
        supply_factor = self._calculate_supply_factor(quantity, location['size'])
        
        # Calculate demand factor
        demand_factor = self._calculate_demand_factor(demand)
        
        # Calculate location factor (based on prosperity)
        location_factor = 0.8 + (location['prosperity'] / 250)  # 0.8 to 1.2
        
        # Calculate rarity factor
        rarity_factor = 0.5 + (resource['rarity'] / 100)  # 0.5 to 1.5
        
        # Apply event effects
        event_factor = 1.0
        for event in events:
            event_factor *= event['effect_value']
        
        # Calculate final price with constraints
        raw_price = base_price * supply_factor * demand_factor * location_factor * rarity_factor * event_factor
        
        # Apply price constraints (min 50% of base, max 300% of base)
        min_price = base_price * 0.5
        max_price = base_price * 3.0
        
        return max(min_price, min(raw_price, max_price))
    
    def _calculate_supply_factor(self, quantity, location_size):
        """Calculate how supply affects price"""
        # Normalize quantity relative to location size
        normalized_supply = quantity / (location_size * 10)
        
        # Inverse relationship: more supply = lower price
        # Uses sigmoid function to create a smooth curve
        return 2.0 / (1 + math.exp(normalized_supply - 1))
    
    def _calculate_demand_factor(self, demand):
        """Calculate how demand affects price"""
        # Normalize demand (1-100 scale)
        normalized_demand = demand / 50.0
        
        # Direct relationship: more demand = higher price
        return 0.5 + normalized_demand
    
    def update_price(self, listing_id, new_price):
        """Update a market listing with new price"""
        query = """
            UPDATE market_listings 
            SET current_price = %s,
                last_updated = NOW()
            WHERE id = %s
        """
        self.db.execute_query(query, (new_price, listing_id))
    
    def record_price_history(self, listing_id, price, quantity):
        """Record price history for analytics"""
        query = """
            INSERT INTO price_history 
            (market_listing_id, price, quantity)
            VALUES (%s, %s, %s)
        """
        self.db.execute_query(query, (listing_id, price, quantity))