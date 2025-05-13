from enum import Enum, auto
from typing import Dict, List, Optional, Union, Set
from pydantic import BaseModel, Field, validator
import uuid
from datetime import datetime


class DomainType(str, Enum):
    """Enumeration of the seven domains of life"""
    BODY = "body"         # Physical health, stamina, manual labor, illness resistance
    MIND = "mind"         # Logic, learning, memory, magic theory, problem solving
    SPIRIT = "spirit"     # Willpower, luck, intuition, empathy, divine favor
    SOCIAL = "social"     # Persuasion, negotiation, reputation, manipulation
    CRAFT = "craft"       # Practical skills, making, fixing, performance under time pressure
    AUTHORITY = "authority" # Leadership, command, strategy, decree enforcement
    AWARENESS = "awareness" # Perception, reaction time, timing in social or combat interactions


class TagCategory(str, Enum):
    """Categories of tags for organizing them"""
    COMBAT = "combat"     # Combat-related tags
    CRAFTING = "crafting" # Crafting-related tags
    SOCIAL = "social"     # Social interaction tags
    MAGIC = "magic"       # Magic-related tags
    SURVIVAL = "survival" # Survival and wilderness tags
    KINGDOM = "kingdom"   # Kingdom management tags
    GENERAL = "general"   # General purpose tags


class Tag(BaseModel):
    """A tag represents a specific skill or knowledge area"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: TagCategory
    description: str
    domains: List[DomainType] = Field(description="Primary domains associated with this tag")
    rank: int = Field(default=0, ge=0, le=5, description="Current rank from 0-5")
    xp: int = Field(default=0, description="Experience points toward next rank")
    xp_required: int = Field(default=100, description="XP required for next rank")

    def gain_xp(self, amount: int) -> bool:
        """Add XP to this tag and return True if a rank up occurred"""
        self.xp += amount
        if self.xp >= self.xp_required and self.rank < 5:
            self.rank += 1
            self.xp = 0
            self.xp_required = self.xp_required * 2  # Double XP required for next rank
            return True
        return False


class GrowthTier(str, Enum):
    """Growth tiers for domains"""
    NOVICE = "novice"       # Range 0-2
    SKILLED = "skilled"     # Range 3-4
    EXPERT = "expert"       # Range 5-7
    MASTER = "master"       # Range 8-9
    PARAGON = "paragon"     # Range 10+


class GrowthLogEntry(BaseModel):
    """An entry in the domain growth log"""
    date: datetime = Field(default_factory=datetime.now)
    domain: DomainType
    action: str
    success: bool
    
    def __str__(self) -> str:
        return f"{self.date.strftime('%Y-%m-%d')} | {self.domain.value} | {self.action} | {'✅' if self.success else '❌'}"


class Domain(BaseModel):
    """A domain represents one of the seven core stats"""
    type: DomainType
    value: int = Field(default=0, ge=0, description="Current value, 0+ with higher tiers possible")
    growth_points: int = Field(default=0, description="Points accumulated toward next value increase")
    growth_required: int = Field(default=100, description="Points required for next value increase")
    usage_count: int = Field(default=0, description="How often this domain is used")
    growth_log: List[GrowthLogEntry] = Field(default_factory=list, description="Log of growth events")
    level_ups_required: int = Field(default=8, description="Number of log entries required for level up")
    
    def get_tier(self) -> GrowthTier:
        """Get the current growth tier based on value"""
        if self.value <= 2:
            return GrowthTier.NOVICE
        elif self.value <= 4:
            return GrowthTier.SKILLED
        elif self.value <= 7:
            return GrowthTier.EXPERT
        elif self.value <= 9:
            return GrowthTier.MASTER
        else:
            return GrowthTier.PARAGON
    
    def add_growth_log_entry(self, action: str, success: bool) -> bool:
        """Add a growth log entry and check for level up
        
        Args:
            action: Description of the action performed
            success: Whether the action was successful
            
        Returns:
            True if a level up occurred, False otherwise
        """
        # Add to log
        entry = GrowthLogEntry(
            domain=self.type,
            action=action,
            success=success
        )
        self.growth_log.append(entry)
        
        # Check if we have enough entries for a level up
        successful_entries = [e for e in self.growth_log if e.success]
        if len(successful_entries) >= self.level_ups_required:
            # Level up
            self.value += 1
            
            # Increase the required number of entries for next level
            self.level_ups_required += 1
            
            # Remove the entries we used for this level up
            # Keep the most recent ones that weren't used
            self.growth_log = self.growth_log[self.level_ups_required - 1:]
            
            return True
        return False
    
    def use(self, action: str, success: bool) -> bool:
        """Record a usage of this domain and return True if growth occurred"""
        self.usage_count += 1
        
        # Add growth points - more for success, less for failure
        points = 10 if success else 3  # "Hard Lesson" rule
        self.growth_points += points
        
        # Add to growth log
        level_up = self.add_growth_log_entry(action, success)
        
        return level_up


class Character(BaseModel):
    """Character model with domains and tags"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Core domains
    domains: Dict[DomainType, Domain] = Field(default_factory=dict)
    
    # Character tags/skills
    tags: Dict[str, Tag] = Field(default_factory=dict)
    
    # Track domain usage history for the "drift" mechanic
    domain_history: Dict[DomainType, List[int]] = Field(default_factory=dict)
    
    @validator('domains', pre=True, always=True)
    def set_domains(cls, domains):
        """Ensure all domains exist with default values"""
        result = domains or {}
        for domain_type in DomainType:
            if domain_type not in result:
                result[domain_type] = Domain(type=domain_type)
        return result
    
    def roll_check(self, domain_type: DomainType, tag_name: Optional[str] = None, difficulty: int = 10) -> dict:
        """Perform a domain check with optional tag bonus
        
        Args:
            domain_type: The primary domain to use
            tag_name: Optional tag to add if character has it
            difficulty: DC of the check (default 10)
            
        Returns:
            Result dict with success flag, roll details, and margin
        """
        import random
        
        # Get the domain
        domain = self.domains[domain_type]
        
        # Roll d20
        d20_roll = random.randint(1, 20)
        
        # Calculate total with domain bonus
        total = d20_roll + domain.value
        roll_breakdown = f"d20({d20_roll}) + {domain_type.value}({domain.value})"
        
        # Add tag bonus if applicable
        tag_bonus = 0
        if tag_name and tag_name in self.tags:
            tag = self.tags[tag_name]
            tag_bonus = tag.rank
            total += tag_bonus
            roll_breakdown += f" + {tag_name}({tag_bonus})"
        
        # Determine success and margin
        success = total >= difficulty
        margin = total - difficulty
        
        # Record domain usage
        domain.use("Domain check", success)
        
        # Record tag usage if applicable
        if tag_name and tag_name in self.tags and success:
            self.tags[tag_name].gain_xp(10)  # Award XP for successful use
        
        # Return result with details
        return {
            "success": success,
            "roll": d20_roll,
            "domain_bonus": domain.value,
            "tag_bonus": tag_bonus,
            "total": total,
            "difficulty": difficulty,
            "margin": margin,
            "breakdown": roll_breakdown
        }
    
    def get_domain_drift_candidates(self) -> List[DomainType]:
        """Return domains that are candidates for drifting (least used)"""
        # Sort domains by usage count
        sorted_domains = sorted(self.domains.values(), key=lambda d: d.usage_count)
        
        # Return the types of the least used domains (bottom 2)
        return [d.type for d in sorted_domains[:2]]
    
    def drift_domain(self, from_domain: DomainType, to_domain: DomainType) -> bool:
        """Shift a point from one domain to another (domain drift mechanic)"""
        if from_domain == to_domain:
            return False
            
        if self.domains[from_domain].value > 0 and self.domains[to_domain].value < 5:
            self.domains[from_domain].value -= 1
            self.domains[to_domain].value += 1
            
            # Record this for character development history
            if from_domain not in self.domain_history:
                self.domain_history[from_domain] = []
            if to_domain not in self.domain_history:
                self.domain_history[to_domain] = []
                
            self.domain_history[from_domain].append(-1)
            self.domain_history[to_domain].append(1)
            
            return True
        return False
