-- Core Resource Definition
CREATE TABLE resources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    base_value NUMERIC(10,2) NOT NULL,
    weight NUMERIC(8,2) DEFAULT 1.0,
    perishability INTEGER DEFAULT 0, -- 0-100 scale (0=permanent)
    rarity INTEGER DEFAULT 50, -- 1-100 scale
    category VARCHAR(50) NOT NULL, -- "raw", "processed", "finished"
    type VARCHAR(50) NOT NULL -- "agricultural", "mining", etc.
);

-- World Locations
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL, -- "city", "village", "mine", etc.
    x_coordinate INTEGER,
    y_coordinate INTEGER,
    size INTEGER DEFAULT 50, -- 1-100 scale
    prosperity INTEGER DEFAULT 50, -- 1-100 scale
    population INTEGER DEFAULT 1000
);

-- Production Nodes
CREATE TABLE production_sites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location_id INTEGER REFERENCES locations(id),
    resource_id INTEGER REFERENCES resources(id),
    base_production_rate NUMERIC(10,2) NOT NULL, -- units per day
    current_production_rate NUMERIC(10,2) NOT NULL,
    technology_level INTEGER DEFAULT 1, -- affects efficiency
    labor_capacity INTEGER DEFAULT 100,
    current_labor INTEGER DEFAULT 100,
    active BOOLEAN DEFAULT TRUE
);

-- Production Modifiers (temporary effects)
CREATE TABLE production_modifiers (
    id SERIAL PRIMARY KEY,
    production_site_id INTEGER REFERENCES production_sites(id),
    modifier_type VARCHAR(50) NOT NULL, -- "season", "weather", "technology", etc.
    modifier_value NUMERIC(5,2) NOT NULL, -- multiplier (1.0 = normal)
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    description TEXT
);

-- Market System
CREATE TABLE market_listings (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    resource_id INTEGER REFERENCES resources(id),
    current_price NUMERIC(10,2) NOT NULL,
    base_price NUMERIC(10,2) NOT NULL, -- reference price
    available_quantity INTEGER NOT NULL DEFAULT 0,
    demand_level INTEGER DEFAULT 50, -- 1-100 scale
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Price History for trends and analysis
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    market_listing_id INTEGER REFERENCES market_listings(id),
    price NUMERIC(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    recorded_date TIMESTAMP DEFAULT NOW()
);

-- Trade Routes between locations
CREATE TABLE trade_routes (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES locations(id),
    destination_id INTEGER REFERENCES locations(id),
    distance NUMERIC(10,2) NOT NULL,
    base_travel_time INTEGER NOT NULL, -- in hours
    current_travel_time INTEGER NOT NULL, -- modified by conditions
    safety_rating INTEGER DEFAULT 50, -- 1-100 scale
    capacity INTEGER DEFAULT 100, -- max units per shipment
    active BOOLEAN DEFAULT TRUE
);

-- Shipments (goods in transit)
CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    trade_route_id INTEGER REFERENCES trade_routes(id),
    resource_id INTEGER REFERENCES resources(id),
    quantity INTEGER NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    expected_arrival_time TIMESTAMP NOT NULL,
    actual_arrival_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'in_transit', -- "in_transit", "delivered", "lost"
    owner_type VARCHAR(50) NOT NULL, -- "npc", "player", "faction"
    owner_id INTEGER NOT NULL
);

-- Shops in locations
CREATE TABLE shops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location_id INTEGER REFERENCES locations(id),
    shop_type VARCHAR(50) NOT NULL, -- "general", "blacksmith", "alchemist", etc.
    wealth NUMERIC(12,2) DEFAULT 500.0, -- available money
    restock_rate NUMERIC(5,2) DEFAULT 1.0, -- multiplier for restock speed
    reputation INTEGER DEFAULT 50, -- affects prices
    owner_npc_id INTEGER -- link to NPC system
);

-- Shop Inventory
CREATE TABLE shop_inventory (
    id SERIAL PRIMARY KEY,
    shop_id INTEGER REFERENCES shops(id),
    resource_id INTEGER REFERENCES resources(id),
    quantity INTEGER NOT NULL DEFAULT 0,
    quality INTEGER DEFAULT 50, -- 1-100 scale
    price_multiplier NUMERIC(5,2) DEFAULT 1.0, -- shop-specific price adjustment
    last_restocked TIMESTAMP DEFAULT NOW()
);

-- Economic Events
CREATE TABLE economic_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL, -- "harvest", "war", "festival", etc.
    description TEXT,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    severity INTEGER DEFAULT 50, -- 1-100 scale
    active BOOLEAN DEFAULT TRUE
);

-- Event Effects (how events affect the economy)
CREATE TABLE event_effects (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES economic_events(id),
    effect_type VARCHAR(50) NOT NULL, -- "production", "price", "demand", etc.
    target_type VARCHAR(50) NOT NULL, -- "resource", "location", "trade_route"
    target_id INTEGER NOT NULL, -- id of the affected entity
    effect_value NUMERIC(5,2) NOT NULL, -- multiplier or absolute value
    description TEXT
);

-- Faction Economic Data
CREATE TABLE faction_economics (
    id SERIAL PRIMARY KEY,
    faction_id INTEGER NOT NULL, -- references factions table
    resource_id INTEGER REFERENCES resources(id),
    demand_level INTEGER DEFAULT 50, -- 1-100 scale
    stockpile_quantity INTEGER DEFAULT 0,
    consumption_rate NUMERIC(10,2) DEFAULT 0.0, -- units per day
    production_preference INTEGER DEFAULT 50 -- 1-100 scale
);

-- Resource Recipes (for crafting)
CREATE TABLE resource_recipes (
    id SERIAL PRIMARY KEY,
    result_resource_id INTEGER REFERENCES resources(id),
    result_quantity INTEGER DEFAULT 1,
    skill_required VARCHAR(50), -- "smithing", "alchemy", etc.
    min_skill_level INTEGER DEFAULT 1,
    time_to_craft INTEGER DEFAULT 60 -- in minutes
);

-- Recipe Ingredients
CREATE TABLE recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES resource_recipes(id),
    resource_id INTEGER REFERENCES resources(id),
    quantity INTEGER NOT NULL
);

-- Player Transactions (for analytics)
CREATE TABLE player_transactions (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- "buy", "sell", "craft"
    resource_id INTEGER REFERENCES resources(id),
    quantity INTEGER NOT NULL,
    price_per_unit NUMERIC(10,2),
    location_id INTEGER REFERENCES locations(id),
    transaction_date TIMESTAMP DEFAULT NOW()
);