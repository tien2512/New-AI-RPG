class EconomicSystem:
    """Main controller for the economic simulation"""
    def __init__(self, database_connection):
        self.db = database_connection
        # Initialize component managers
        self.resources = ResourceManager(self.db)
        self.locations = LocationManager(self.db)
        self.production = ProductionManager(self.db)
        self.markets = MarketManager(self.db)
        self.trade = TradeManager(self.db)
        self.shops = ShopManager(self.db)
        self.events = EventManager(self.db)
        self.crafting = CraftingSystem(self.db)
        self.factions = FactionEconomicManager(self.db)
        
    def update(self, game_time_delta):
        """Update the entire economic system for a time period"""
        # Update in sequence to create proper cascading effects
        self.events.update(game_time_delta)
        self.production.update(game_time_delta)
        self.trade.update(game_time_delta)
        self.markets.update(game_time_delta)
        self.factions.update(game_time_delta)
        self.shops.update(game_time_delta)
        
    def process_player_action(self, action_type, player_id, **action_data):
        """Handle economic effects of player actions"""
        if action_type == "purchase":
            return self.shops.process_purchase(player_id, **action_data)
        elif action_type == "sale":
            return self.shops.process_sale(player_id, **action_data)
        elif action_type == "craft":
            return self.crafting.craft_item(player_id, **action_data)
        elif action_type == "trade_route_action":
            return self.trade.process_route_action(player_id, **action_data)
        elif action_type == "production_action":
            return self.production.process_site_action(player_id, **action_data)
    
    def get_market_data(self, location_id, resource_ids=None):
        """Get current market information for a location"""
        return self.markets.get_market_data(location_id, resource_ids)
    
    def get_economic_report(self, location_id):
        """Generate an economic report for a location"""
        # Gather data from various subsystems
        market_data = self.markets.get_market_data(location_id)
        production_data = self.production.get_production_data(location_id)
        trade_data = self.trade.get_location_trade_data(location_id)
        shop_data = self.shops.get_location_shops(location_id)
        
        # Compile into a report dictionary
        return {
            "market": market_data,
            "production": production_data,
            "trade": trade_data,
            "shops": shop_data,
            "local_events": self.events.get_location_events(location_id),
            "economic_health": self._calculate_economic_health(location_id)
        }
    
    def _calculate_economic_health(self, location_id):
        """Calculate overall economic health of a location (1-100)"""
        # Composite score based on multiple factors
        location = self.locations.get_location(location_id)
        
        # Various economic indicators
        supply_sufficiency = self._calculate_supply_sufficiency(location_id)
        price_stability = self._calculate_price_stability(location_id)
        trade_activity = self._calculate_trade_activity(location_id)
        
        # Weighted average of indicators
        health = (
            supply_sufficiency * 0.4 +
            price_stability * 0.3 +
            trade_activity * 0.3
        )
        
        return min(100, max(1, health))  # Clamp between 1-100