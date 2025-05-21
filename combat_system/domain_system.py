"""
Domain progression system for the game engine.

This module handles domain checks, growth, and progression.
"""
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from ..shared.models import (
    Domain, DomainType, GrowthTier, GrowthLogEntry, Character, Tag, TagCategory
)
from ..events.event_bus import event_bus, GameEvent, EventType


class DomainSystem:
    """
    System for managing domain progression and checks.
    
    This class handles:
    - Domain checks (with dice rolls)
    - Domain growth and progression
    - Tag/skill advancement
    - Growth log maintenance
    """
    
    def __init__(self):
        """Initialize the domain system."""
        # Cache of domain growth status for active characters
        self._domain_growth_cache: Dict[str, Dict[DomainType, int]] = {}
        
        # Subscribe to relevant events
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Register event handlers for the domain system."""
        event_bus.subscribe(EventType.DOMAIN_CHECK, self._handle_domain_check)
        event_bus.subscribe(EventType.SKILL_CHECK, self._handle_skill_check)
    
    def _handle_domain_check(self, event: GameEvent):
        """
        Handler for domain check events.
        
        Args:
            event: The domain check event
        """
        # Extract relevant information
        character_id = event.actor
        domain_type = event.context.get('domain')
        success = event.context.get('success', False)
        action = event.context.get('action', 'Unknown action')
        
        # Log domain usage and check for growth
        if domain_type and isinstance(domain_type, str):
            try:
                domain_enum = DomainType(domain_type)
                self.log_domain_use(character_id, domain_enum, action, success)
            except ValueError:
                print(f"Warning: Invalid domain type: {domain_type}")
    
    def _handle_skill_check(self, event: GameEvent):
        """
        Handler for skill check events.
        
        Args:
            event: The skill check event
        """
        # Extract relevant information
        character_id = event.actor
        tag_name = event.context.get('tag')
        domain_type = event.context.get('domain')
        success = event.context.get('success', False)
        
        # Add experience to the tag if available
        if tag_name and success:
            self.add_tag_experience(character_id, tag_name, 10)  # Default XP gain
    
    def roll_check(self, 
                  character: Character, 
                  domain_type: DomainType, 
                  tag_name: Optional[str] = None, 
                  difficulty: int = 10) -> Dict[str, Any]:
        """
        Perform a domain check roll.
        
        Args:
            character: The character performing the check
            domain_type: The domain being used
            tag_name: Optional tag/skill name that applies
            difficulty: Difficulty class to beat
            
        Returns:
            Dictionary with roll results
        """
        import random
        
        # Roll a d20
        roll = random.randint(1, 20)
        
        # Get domain value
        domain_value = 0
        if domain_type in character.domains:
            domain_value = character.domains[domain_type].value
            
        # Get tag/skill rank if applicable
        tag_value = 0
        tag_category = None
        if tag_name and tag_name in character.tags:
            tag = character.tags[tag_name]
            tag_value = tag.rank
            tag_category = tag.category
            
        # Calculate total and determine success
        total = roll + domain_value + tag_value
        success = total >= difficulty
        margin = total - difficulty
        
        # Create result dictionary
        result = {
            "roll": roll,
            "domain_value": domain_value,
            "tag_value": tag_value,
            "tag_name": tag_name,
            "tag_category": tag_category.value if tag_category else None,
            "difficulty": difficulty,
            "total": total,
            "success": success,
            "margin": margin,
            "domain": domain_type.value
        }
        
        # Publish domain check event
        event = GameEvent(
            type=EventType.DOMAIN_CHECK,
            actor=str(character.id),
            context={
                "domain": domain_type.value,
                "tag": tag_name,
                "difficulty": difficulty,
                "roll": roll,
                "total": total,
                "success": success,
                "margin": margin
            },
            tags=["check", domain_type.value.lower(), "dice_roll"],
            game_id=getattr(character, "game_id", None)
        )
        event_bus.publish(event)
        
        return result
    
    def log_domain_use(self, 
                      character_id: str, 
                      domain_type: DomainType, 
                      action: str, 
                      success: bool) -> Tuple[bool, bool]:
        """
        Log domain usage and check for growth.
        
        Args:
            character_id: ID of the character
            domain_type: The domain being used
            action: Description of the action
            success: Whether the action was successful
            
        Returns:
            Tuple of (usage_recorded, level_up_occurred)
        """
        from ..storage.character_storage import get_character
        
        # Get character from storage
        character = get_character(character_id)
        if not character:
            print(f"Warning: Character {character_id} not found")
            return False, False
        
        # Get domain or initialize it
        if domain_type not in character.domains:
            print(f"Warning: Domain {domain_type} not found for character {character_id}")
            return False, False
            
        domain = character.domains[domain_type]
        
        # Log the usage and check for level up
        level_up = domain.add_growth_log_entry(action, success)
        
        # Increment usage count and add growth points
        domain.usage_count += 1
        points = 10 if success else 3  # More points for success, fewer for failure
        domain.growth_points += points
        
        # If level up occurred, publish event
        if level_up:
            self._publish_domain_increased_event(character, domain_type, domain.value)
        
        # Save character
        from ..storage.character_storage import save_character
        save_character(character)
        
        return True, level_up
    
    def _publish_domain_increased_event(self, 
                                       character: Character, 
                                       domain_type: DomainType, 
                                       new_value: int):
        """
        Publish a domain increased event.
        
        Args:
            character: The character whose domain increased
            domain_type: The domain that increased
            new_value: The new domain value
        """
        # Get the growth tier for this value
        new_tier = GrowthTier.NOVICE
        if new_value <= 2:
            new_tier = GrowthTier.NOVICE
        elif new_value <= 4:
            new_tier = GrowthTier.SKILLED
        elif new_value <= 7:
            new_tier = GrowthTier.EXPERT
        elif new_value <= 9:
            new_tier = GrowthTier.MASTER
        else:
            new_tier = GrowthTier.PARAGON
            
        event = GameEvent(
            type=EventType.DOMAIN_INCREASED,
            actor=str(character.id),
            context={
                "domain": domain_type.value,
                "old_value": new_value - 1,
                "new_value": new_value,
                "tier": new_tier.value
            },
            tags=["progression", domain_type.value.lower(), "level_up"],
            effects=[
                {"type": "domain_level_up", "domain": domain_type.value, "value": new_value},
                {"type": "notification", "message": f"Your {domain_type.value} domain has increased to {new_value}!"}
            ],
            game_id=getattr(character, "game_id", None)
        )
        event_bus.publish(event)
    
    def add_tag_experience(self, 
                          character_id: str, 
                          tag_name: str, 
                          xp_amount: int) -> bool:
        """
        Add experience to a tag and check for rank up.
        
        Args:
            character_id: ID of the character
            tag_name: Name of the tag
            xp_amount: Amount of XP to add
            
        Returns:
            True if a rank up occurred, False otherwise
        """
        from ..storage.character_storage import get_character, save_character
        
        # Get character from storage
        character = get_character(character_id)
        if not character:
            print(f"Warning: Character {character_id} not found")
            return False
        
        # Get tag or return false
        if tag_name not in character.tags:
            print(f"Warning: Tag {tag_name} not found for character {character_id}")
            return False
            
        tag = character.tags[tag_name]
        
        # Add XP and check for rank up
        rank_up = tag.gain_xp(xp_amount)
        
        # If rank up occurred, publish event
        if rank_up:
            event = GameEvent(
                type=EventType.TAG_INCREASED,
                actor=str(character.id),
                context={
                    "tag": tag_name,
                    "old_rank": tag.rank - 1,
                    "new_rank": tag.rank,
                    "category": tag.category.value
                },
                tags=["progression", "skill", tag.category.value.lower()],
                effects=[
                    {"type": "tag_rank_up", "tag": tag_name, "rank": tag.rank},
                    {"type": "notification", "message": f"Your {tag_name} skill has increased to rank {tag.rank}!"}
                ],
                game_id=getattr(character, "game_id", None)
            )
            event_bus.publish(event)
        
        # Save character
        save_character(character)
        
        return rank_up
    
    def get_growth_log_summary(self, character_id: str, domain_type: DomainType) -> str:
        """
        Get a summary of the growth log for a domain.
        
        Args:
            character_id: ID of the character
            domain_type: The domain to get log for
            
        Returns:
            Summary string of recent growth log entries
        """
        from ..storage.character_storage import get_character
        
        # Get character from storage
        character = get_character(character_id)
        if not character:
            return "Character not found"
        
        # Get domain or return error
        if domain_type not in character.domains:
            return f"Domain {domain_type.value} not found for this character"
            
        domain = character.domains[domain_type]
        
        # Get the last 5 entries
        entries = domain.growth_log[-5:] if domain.growth_log else []
        
        if not entries:
            return f"No growth log entries for {domain_type.value}"
            
        # Format entries
        lines = [f"Recent {domain_type.value} domain growth:"]
        for entry in entries:
            date_str = entry.date.strftime("%Y-%m-%d") if hasattr(entry.date, "strftime") else entry.date
            result = "✓" if entry.success else "✗"
            lines.append(f"• {date_str}: {entry.action} [{result}]")
            
        lines.append(f"Current level: {domain.value} ({self._get_tier_name(domain.value)})")
        lines.append(f"Progress: {len([e for e in domain.growth_log if e.success])}/{domain.level_ups_required} successful actions")
        
        return "\n".join(lines)
    
    def _get_tier_name(self, value: int) -> str:
        """Get the tier name for a domain value."""
        if value <= 2:
            return "Novice"
        elif value <= 4:
            return "Skilled"
        elif value <= 7:
            return "Expert"
        elif value <= 9:
            return "Master"
        else:
            return "Paragon"


# Global domain system instance
domain_system = DomainSystem()
