from typing import Set, Dict, List, Tuple
from enum import Enum
from combat_system_core_v1_01 import Domain, MoveType, CombatMove, Combatant

class EnvironmentElement(Enum):
    WATER = "Water"
    FIRE = "Fire"
    HIGH_GROUND = "High Ground"
    DARKNESS = "Darkness"
    CONFINED_SPACE = "Confined Space"
    OPEN_FIELD = "Open Field"
    MAGICAL_AURA = "Magical Aura"
    RUINS = "Ruins"
    FOREST = "Forest"
    URBAN = "Urban"
    UNSTABLE = "Unstable Ground"

class EnvironmentInteraction:
    def __init__(self, name: str, description: str, requirements: Dict = None, effects: Dict = None):
        self.name = name
        self.description = description
        self.requirements = requirements or {}  # Domain requirements, etc.
        self.effects = effects or {}  # Effects on combat
        
class EnvironmentSystem:
    def __init__(self):
        self.environment_tags: Set[str] = set()
        self.available_interactions: Dict[str, EnvironmentInteraction] = {}
        
    def add_environment_tag(self, tag: str) -> None:
        """Add an environment tag to the current scene"""
        self.environment_tags.add(tag)
        # Update available interactions based on new tag
        self._update_available_interactions()
        
    def remove_environment_tag(self, tag: str) -> None:
        """Remove an environment tag from the current scene"""
        if tag in self.environment_tags:
            self.environment_tags.remove(tag)
            # Update available interactions after removal
            self._update_available_interactions()
    
    def _update_available_interactions(self) -> None:
        """Update available interactions based on current environment tags"""
        self.available_interactions = {}
        
        # Water interactions
        if "Water" in self.environment_tags:
            self.available_interactions["splash_water"] = EnvironmentInteraction(
                name="Splash Water",
                description="Splash water to distract or obscure vision",
                requirements={"domain": Domain.AWARENESS},
                effects={"target_penalty": -1, "narrative": "Water obscures vision"}
            )
        
        # Fire interactions
        if "Fire" in self.environment_tags:
            self.available_interactions["use_flames"] = EnvironmentInteraction(
                name="Use Flames",
                description="Use nearby flames as a weapon or distraction",
                requirements={"domain": Domain.CRAFT},
                effects={"damage_bonus": 3, "narrative": "Flames burn the target"}
            )
        
        # High Ground interactions
        if "High Ground" in self.environment_tags:
            self.available_interactions["tactical_advantage"] = EnvironmentInteraction(
                name="Tactical Advantage",
                description="Use high ground for combat advantage",
                requirements={"domain": Domain.AWARENESS},
                effects={"roll_bonus": 2, "narrative": "The high ground provides advantage"}
            )
            
        # Add more environment-specific interactions here
        
    def get_available_interactions(self) -> List[EnvironmentInteraction]:
        """Get list of available environmental interactions"""
        return list(self.available_interactions.values())
    
    def apply_environment_modifiers(self, move: CombatMove, actor: Combatant) -> Tuple[int, List[str]]:
        """Calculate environment-based modifiers for a move
        
        Returns:
            Tuple containing (roll_modifier, narrative_hooks)
        """
        roll_modifier = 0
        narrative_hooks = []
        
        # Apply modifiers based on environment tags and domains
        for domain in move.domains:
            # Awareness in darkness
            if domain == Domain.AWARENESS and "Darkness" in self.environment_tags:
                if "Darkness" in actor.strong_domains:
                    roll_modifier += 2
                    narrative_hooks.append("Expertly navigates the darkness")
                else:
                    roll_modifier -= 1
                    narrative_hooks.append("Struggles to perceive in darkness")
            
            # Body in confined spaces
            if domain == Domain.BODY and "Confined Space" in self.environment_tags:
                roll_modifier -= 1
                narrative_hooks.append("Limited movement in the confined space")
            
            # Mind in magical aura
            if domain == Domain.MIND and "Magical Aura" in self.environment_tags:
                if Domain.SPIRIT in move.domains:
                    roll_modifier += 2
                    narrative_hooks.append("Channels the ambient magical energy")
                
            # Authority in open field
            if domain == Domain.AUTHORITY and "Open Field" in self.environment_tags:
                roll_modifier += 1
                narrative_hooks.append("Voice carries powerfully across the field")
                
            # Craft in ruins
            if domain == Domain.CRAFT and "Ruins" in self.environment_tags:
                roll_modifier += 1
                narrative_hooks.append("Uses scattered debris as improvised tools")
                
            # Add more environment-domain interactions
                
        return roll_modifier, narrative_hooks