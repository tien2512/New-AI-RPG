class ProductionManager:
    """Manages resource production throughout the game world"""
    def __init__(self, db):
        self.db = db
    
    def update(self, time_delta):
        """Update all production sites for a time period"""
        # Get all active production sites
        query = "SELECT * FROM production_sites WHERE active = TRUE"
        production_sites = self.db.execute_query(query)
        
        for site in production_sites:
            # Calculate current production rate with modifiers
            current_rate = self.calculate_production_rate(site['id'])
            
            # Calculate produced amount for time period
            produced_amount = current_rate * time_delta
            
            # Add produced resources to local market
            self.add_to_local_market(site['location_id'], site['resource_id'], produced_amount)
            
            # Log production for analytics
            self.log_production(site['id'], produced_amount, time_delta)
    
    def calculate_production_rate(self, site_id):
        """Calculate current production rate with all modifiers applied"""
        # Get base production site data
        query = "SELECT * FROM production_sites WHERE id = %s"
        site = self.db.execute_query(query, (site_id,))[0]
        
        base_rate = site['base_production_rate']
        
        # Get all active modifiers for this site
        now = datetime.now()
        query = """
            SELECT * FROM production_modifiers 
            WHERE production_site_id = %s 
            AND start_date <= %s 
            AND (end_date IS NULL OR end_date >= %s)
        """
        modifiers = self.db.execute_query(query, (site_id, now, now))
        
        # Apply all modifiers
        rate_multiplier = 1.0
        for mod in modifiers:
            rate_multiplier *= mod['modifier_value']
        
        # Apply labor efficiency
        labor_ratio = site['current_labor'] / site['labor_capacity']
        labor_efficiency = min(1.0, labor_ratio)  # Cap at 100% efficiency
        
        # Calculate final rate
        current_rate = base_rate * rate_multiplier * labor_efficiency
        
        # Update the current rate in database
        update_query = """
            UPDATE production_sites 
            SET current_production_rate = %s 
            WHERE id = %s
        """
        self.db.execute_query(update_query, (current_rate, site_id))
        
        return current_rate
    
    def add_to_local_market(self, location_id, resource_id, amount):
        """Add produced resources to the local market"""
        # First check if a market listing exists
        query = """
            SELECT * FROM market_listings 
            WHERE location_id = %s AND resource_id = %s
        """
        listing = self.db.execute_query(query, (location_id, resource_id))
        
        if listing:
            # Update existing listing
            update_query = """
                UPDATE market_listings 
                SET available_quantity = available_quantity + %s,
                    last_updated = NOW()
                WHERE location_id = %s AND resource_id = %s
            """
            self.db.execute_query(update_query, (amount, location_id, resource_id))
        else:
            # Create new listing
            # First get base price from resources table
            resource_query = "SELECT base_value FROM resources WHERE id = %s"
            resource = self.db.execute_query(resource_query, (resource_id,))[0]
            
            insert_query = """
                INSERT INTO market_listings 
                (location_id, resource_id, current_price, base_price, available_quantity)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.db.execute_query(
                insert_query, 
                (location_id, resource_id, resource['base_value'], resource['base_value'], amount)
            )
    
    def log_production(self, site_id, amount, time_delta):
        """Log production for analytics"""
        # Implementation details for logging production
        pass
