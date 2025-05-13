from typing import List, Dict, Set, Optional
from enum import Enum, auto
from dataclasses import dataclass
import random
from combat_system_core_v1_01 import Domain, Status, Consequence, Combatant

class StatusTier(Enum):
    MINOR = auto()
    MODERATE = auto()
    SEVERE = auto()
    CRITICAL = auto()

class StatusSource(Enum):
    PHYSICAL = auto()
    MENTAL = auto()
    SPIRITUAL = auto()
    ENVIRONMENTAL = auto()
    MAGICAL = auto()
    SOCIAL = auto()

@dataclass
class EnhancedStatus:
    name: str
    base_status: Status
    tier: StatusTier
    source: StatusSource
    duration: int  # In rounds
    description: str
    affected_domains: List[Domain]
    stat_modifiers: Dict[str, int]
    domain_modifiers: Dict[Domain, int]
    special_effects: List[str]
    
    def apply_to_combatant(self, combatant: Combatant):
        """Apply this status to a combatant"""
        # Add base status
        combatant.statuses.add(self.base_status)
        
        # Apply stat modifiers if tracking enhanced statuses
        if not hasattr(combatant, 'enhanced_statuses'):
            combatant.enhanced_statuses = []
        
        # Add to enhanced statuses list
        combatant.enhanced_statuses.append(self)
        
        # Apply immediate effects
        self._apply_stat_modifiers(combatant)
        
    def _apply_stat_modifiers(self, combatant: Combatant):
        """Apply stat modifiers from this status"""
        for stat, modifier in self.stat_modifiers.items():
            if stat == "stamina_regen":
                # Would be applied during stamina regeneration
                pass
            elif stat == "max_stamina":
                # Temporarily modify max stamina
                combatant.max_stamina = max(1, combatant.max_stamina + modifier)
            # Add other stat modifications as needed
    
    def get_domain_modifier(self, domain: Domain) -> int:
        """Get modifier for a specific domain from this status"""
        return self.domain_modifiers.get(domain, 0)

class StatusFactory:
    """Factory for creating standard enhanced statuses"""
    
    @staticmethod
    def create_wounded(tier: StatusTier = StatusTier.MODERATE) -> EnhancedStatus:
        """Create a wounded status with appropriate tier"""
        if tier == StatusTier.MINOR:
            return EnhancedStatus(
                name="Lightly Wounded",
                base_status=Status.WOUNDED,
                tier=tier,
                source=StatusSource.PHYSICAL,
                duration=3,
                description="A minor wound that hampers physical activity",
                affected_domains=[Domain.BODY],
                stat_modifiers={"stamina_regen": -1},
                domain_modifiers={Domain.BODY: -1},
                special_effects=[]
            )
        elif tier == StatusTier.MODERATE:
            return EnhancedStatus(
                name="Wounded",
                base_status=Status.WOUNDED,
                tier=tier,
                source=StatusSource.PHYSICAL,
                duration=4,
                description="A significant wound that limits movement",
                affected_domains=[Domain.BODY, Domain.AWARENESS],
                stat_modifiers={"stamina_regen": -1, "max_stamina": -10},
                domain_modifiers={Domain.BODY: -1, Domain.AWARENESS: -1},
                special_effects=["May leave blood trail"]
            )
        elif tier == StatusTier.SEVERE:
            return EnhancedStatus(
                name="Severely Wounded",
                base_status=Status.WOUNDED,
                tier=tier,
                source=StatusSource.PHYSICAL,
                duration=6,
                description="A severe wound that greatly impairs function",
                affected_domains=[Domain.BODY, Domain.AWARENESS, Domain.CRAFT],
                stat_modifiers={"stamina_regen": -2, "max_stamina": -20},
                domain_modifiers={Domain.BODY: -2, Domain.AWARENESS: -1, Domain.CRAFT: -1},
                special_effects=["Bleeding: Take 3 damage each round", "Visible weakness: Enemies target you more"]
            )
        else:  # CRITICAL
            return EnhancedStatus(
                name="Critically Wounded",
                base_status=Status.WOUNDED,
                tier=tier,
                source=StatusSource.PHYSICAL,
                duration=8,
                description="A life-threatening wound that severely impairs all function",
                affected_domains=[Domain.BODY, Domain.AWARENESS, Domain.CRAFT, Domain.MIND],
                stat_modifiers={"stamina_regen": -3, "max_stamina": -30, "max_focus": -20},
                domain_modifiers={Domain.BODY: -3, Domain.AWARENESS: -2, Domain.CRAFT: -2, Domain.MIND: -1},
                special_effects=["Heavy Bleeding: Take 5 damage each round", 
                                "Shock: 20% chance to lose a turn",
                                "Requires immediate medical attention"]
            )
    
    # Add more factory methods for other status types
    
class ConsequenceSystem:
    """Enhanced system for handling long-term consequences"""
    
    @staticmethod
    def create_consequence_from_combat(result: dict, target: Combatant, 
                                       status: EnhancedStatus = None) -> Optional[Consequence]:
        """Create a lasting consequence based on combat result and status"""
        if not result["actor_success"] or result["effect_magnitude"] < 3:
            return None
            
        # Base consequence severity on effect magnitude and status
        severity = result["effect_magnitude"]
        if status and status.tier == StatusTier.SEVERE:
            severity += 2
        elif status and status.tier == StatusTier.CRITICAL:
            severity += 4
            
        # Determine affected domains
        affected_domains = []
        if status:
            affected_domains = status.affected_domains.copy()
        
        # Generate appropriate consequence
        if severity >= 8:
            # Major permanent consequence
            desc = f"Permanent injury from {result['actor_move']}"
            hook = f"The {result['actor_move']} left a permanent scar, both physically and mentally"
            return Consequence(
                description=desc,
                affected_domains=affected_domains,
                duration=-1,  # Permanent
                intensity=4,
                narrative_hook=hook,
                affected_stats={"max_health": -10, "stamina_regen": -1}
            )
        elif severity >= 5:
            # Major consequence
            desc = f"Serious injury from {result['actor_move']}"
            hook = f"The {result['actor_move']} left a lasting mark"
            return Consequence(
                description=desc,
                affected_domains=affected_domains,
                duration=5,
                intensity=3,
                narrative_hook=hook,
                affected_stats={"stamina_regen": -1}
            )
        else:
            # Minor consequence
            desc = f"Minor injury from {result['actor_move']}"
            hook = f"Still feeling the effects of the {result['actor_move']}"
            return Consequence(
                description=desc,
                affected_domains=affected_domains,
                duration=2,
                intensity=1,
                narrative_hook=hook
            )