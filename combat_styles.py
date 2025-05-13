from typing import List, Dict, Tuple
from enum import Enum
from combat_system_core_v1_01 import Domain, CombatMove, MoveType, Combatant

class CombatStyle(Enum):
    BERSERKER = "Berserker"           # Aggressive, strength-based style
    DUELIST = "Duelist"               # Precision, technical fighting
    TACTICIAN = "Tactician"           # Planning and strategy-focused
    MYSTIC = "Mystic"                 # Spirit and mind powers
    TRICKSTER = "Trickster"           # Deception and misdirection
    COMMANDER = "Commander"           # Leadership and authority
    SURVIVALIST = "Survivalist"       # Adaptability and resourcefulness

class StyleTier(Enum):
    NOVICE = "Novice"
    ADEPT = "Adept"
    EXPERT = "Expert"
    MASTER = "Master"
    
class StyleProgression:
    def __init__(self, style: CombatStyle):
        self.style = style
        self.tier = StyleTier.NOVICE
        self.experience = 0
        self.unlocked_moves = []
        self.mastery_abilities = []
        
    def add_experience(self, amount: int):
        """Add experience to the style progression"""
        self.experience += amount
        self._check_tier_up()
        
    def _check_tier_up(self):
        """Check if the style has reached a new tier"""
        if self.tier == StyleTier.NOVICE and self.experience >= 100:
            self.tier = StyleTier.ADEPT
            self._unlock_adept_abilities()
        elif self.tier == StyleTier.ADEPT and self.experience >= 300:
            self.tier = StyleTier.EXPERT
            self._unlock_expert_abilities()
        elif self.tier == StyleTier.EXPERT and self.experience >= 700:
            self.tier = StyleTier.MASTER
            self._unlock_master_abilities()
    
    def _unlock_adept_abilities(self):
        """Unlock abilities for the Adept tier"""
        new_abilities = STYLE_PROGRESSION_TREE[self.style][StyleTier.ADEPT]
        self.mastery_abilities.extend(new_abilities)
        # Here you would add new moves to the combatant based on the style
        
    def _unlock_expert_abilities(self):
        """Unlock abilities for the Expert tier"""
        new_abilities = STYLE_PROGRESSION_TREE[self.style][StyleTier.EXPERT]
        self.mastery_abilities.extend(new_abilities)
        
    def _unlock_master_abilities(self):
        """Unlock abilities for the Master tier"""
        new_abilities = STYLE_PROGRESSION_TREE[self.style][StyleTier.MASTER]
        self.mastery_abilities.extend(new_abilities)

# Sample progression tree for styles
STYLE_PROGRESSION_TREE = {
    CombatStyle.BERSERKER: {
        StyleTier.ADEPT: ["Rage: When health drops below 50%, gain +2 to Force moves"],
        StyleTier.EXPERT: ["Intimidating Presence: Start combat with 1 momentum"],
        StyleTier.MASTER: ["Unstoppable: Ignore the first defeating blow in each combat"]
    },
    CombatStyle.DUELIST: {
        StyleTier.ADEPT: ["Riposte: After a successful defense, gain advantage on next attack"],
        StyleTier.EXPERT: ["Precision: Critical hits on rolls 5 above opponent"],
        StyleTier.MASTER: ["Perfect Technique: Once per combat, automatically win a contested roll"]
    },
    # Add other styles here
}

# Extend the Combatant class to include styles
def add_combat_style(combatant: Combatant, style: CombatStyle) -> None:
    """Add a combat style to a combatant"""
    if not hasattr(combatant, 'combat_styles'):
        combatant.combat_styles = {}
    
    # Create a new style progression if not already present
    if style not in combatant.combat_styles:
        combatant.combat_styles[style] = StyleProgression(style)
        
def get_style_moves(style: CombatStyle) -> List[CombatMove]:
    """Get moves associated with a specific combat style"""
    # This would be populated with style-specific moves
    style_moves = {
        CombatStyle.BERSERKER: [
            CombatMove(
                name="Raging Strike",
                move_type=MoveType.FORCE,
                domains=[Domain.BODY],
                description="A powerful strike fueled by rage",
                stamina_cost=2
            ),
            CombatMove(
                name="Intimidating Roar",
                move_type=MoveType.FORCE,
                domains=[Domain.AUTHORITY, Domain.BODY],
                description="A terrifying roar that frightens enemies",
                stamina_cost=1,
                spirit_cost=1
            ),
        ],
        # Add more styles and their moves
    }
    
    return style_moves.get(style, [])