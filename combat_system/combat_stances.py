from enum import Enum
from typing import List, Dict
from combat_system_core_v1_01 import Domain, CombatMove, Combatant

class CombatStance(Enum):
    AGGRESSIVE = "Aggressive"     # Offense-focused, high damage but vulnerable
    DEFENSIVE = "Defensive"       # Defense-focused, reduced damage but more resilient
    BALANCED = "Balanced"         # Balanced approach, no penalties or bonuses
    TACTICAL = "Tactical"         # Focus on planning, increased effect of calculated moves
    RECKLESS = "Reckless"         # High-risk, high-reward stance, boosts desperate moves
    REACTIVE = "Reactive"         # Counter-focused, better at responding to opponent's moves

class StanceEffect:
    def __init__(self, 
                 attack_modifier: int = 0,
                 defense_modifier: int = 0,
                 stamina_usage: float = 1.0,
                 focus_usage: float = 1.0,
                 spirit_usage: float = 1.0,
                 special_effects: List[str] = None):
        self.attack_modifier = attack_modifier    # Modifier to attack rolls
        self.defense_modifier = defense_modifier  # Modifier to defense rolls
        self.stamina_usage = stamina_usage        # Multiplier for stamina costs
        self.focus_usage = focus_usage            # Multiplier for focus costs
        self.spirit_usage = spirit_usage          # Multiplier for spirit costs
        self.special_effects = special_effects or []

# Define stance effects
STANCE_EFFECTS = {
    CombatStance.AGGRESSIVE: StanceEffect(
        attack_modifier=2,
        defense_modifier=-1,
        stamina_usage=1.2,
        special_effects=["Boost Force moves by 1"]
    ),
    CombatStance.DEFENSIVE: StanceEffect(
        attack_modifier=-1,
        defense_modifier=2,
        stamina_usage=0.8,
        special_effects=["Reduce incoming damage by 20%"]
    ),
    CombatStance.BALANCED: StanceEffect(),  # Default values (no modifiers)
    CombatStance.TACTICAL: StanceEffect(
        focus_usage=1.2,
        special_effects=["Calculated moves get +2 instead of usual bonus", 
                        "Can see opponent's next move type with 70% accuracy"]
    ),
    CombatStance.RECKLESS: StanceEffect(
        attack_modifier=3,
        defense_modifier=-2,
        stamina_usage=1.5,
        special_effects=["Desperate moves get +3 max bonus potential", 
                        "Take 20% more damage"]
    ),
    CombatStance.REACTIVE: StanceEffect(
        attack_modifier=-1,
        defense_modifier=1,
        focus_usage=1.1,
        special_effects=["Counter-type moves get +2 bonus", 
                        "Can perform a free counter-attack when successfully defending"]
    )
}

def apply_stance_to_combatant(combatant: Combatant, stance: CombatStance) -> None:
    """Apply stance effects to a combatant"""
    # Store the current stance for reference
    combatant.current_stance = stance
    # Additional effects would be applied during combat resolution
