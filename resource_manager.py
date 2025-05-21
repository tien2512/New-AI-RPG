class ResourceManager:
    """Manages all resources in the game world"""
    def __init__(self, db):
        self.db = db
        self.resources_cache = {}  # For performance
        self.load_resources()
        
    def load_resources(self):
        """Load all resources from database into memory"""
        query = "SELECT * FROM resources"
        resources = self.db.execute_query(query)
        for resource in resources:
            self.resources_cache[resource['id']] = resource
    
    def get_resource(self, resource_id):
        """Get resource by ID"""
        if resource_id in self.resources_cache:
            return self.resources_cache[resource_id]
        
        query = "SELECT * FROM resources WHERE id = %s"
        resource = self.db.execute_query(query, (resource_id,))
        if resource:
            self.resources_cache[resource_id] = resource[0]
            return resource[0]
        return None
    
    def get_resources_by_category(self, category):
        """Get all resources of a specific category"""
        return [r for r in self.resources_cache.values() if r['category'] == category]
    
    def get_resources_by_type(self, resource_type):
        """Get all resources of a specific type"""
        return [r for r in self.resources_cache.values() if r['type'] == resource_type]