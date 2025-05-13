from typing import List, Dict, Optional, Tuple
from combat_system_core_v1_01 import MoveType, Domain, CombatMove, Combatant

class ComboMove:
    def __init__(self, 
                 name: str,
                 description: str,
                 required_sequence: List[MoveType],
                 domains: List[Domain],
                 bonus_effect: Dict = None):
        self.name = name
        self.description = description
        self.required_sequence = required_sequence  # Sequence of move types required
        self.domains = domains
        self.bonus_effect = bonus_effect or {}
        
class ComboSystem:
    def __init__(self):
        # Track recent moves for each combatant
        self.combatant_move_history = {}
        # Available combos
        self.available_combos = self._initialize_combos()
        
    def _initialize_combos(self) -> List[ComboMove]:
        """Initialize available combo moves"""
        combos = []
        
        # Create some sample combo moves
        combos.append(ComboMove(
            name="Force-Trick-Force",
            description="A powerful opening followed by a feint, then a devastating blow",
            required_sequence=[MoveType.FORCE, MoveType.TRICK, MoveType.FORCE],
            domains=[Domain.BODY, Domain.AWARENESS],
            bonus_effect={"damage_bonus": 10, "momentum_bonus": 1}
        ))
        
        combos.append(ComboMove(
            name="Focus-Focus-Force",
            description="Carefully analyze the opponent's defenses, then strike with precision",
            required_sequence=[MoveType.FOCUS, MoveType.FOCUS, MoveType.FORCE],
            domains=[Domain.MIND, Domain.BODY],
            bonus_effect={"critical_chance": 0.2, "ignore_defense": True}
        ))
        
        # Add more predefined combos
        
        return combos
    
    def record_move(self, combatant: Combatant, move_type: MoveType) -> None:
        """Record a move for a combatant to track potential combos"""
        if combatant.name not in self.combatant_move_history:
            self.combatant_move_history[combatant.name] = []
            
        # Add the move to history
        self.combatant_move_history[combatant.name].append(move_type)
        
        # Limit history length to prevent memory bloat
        if len(self.combatant_move_history[combatant.name]) > 5:
            self.combatant_move_history[combatant.name].pop(0)
    
    def check_for_combo(self, combatant: Combatant) -> Optional[Tuple[ComboMove, List[str]]]:
        """Check if the combatant's recent moves form a combo
        
        Returns:
            Tuple of (combo_move, narrative_hooks) if a combo is found, None otherwise
        """
        if combatant.name not in self.combatant_move_history:
            return None
            
        move_history = self.combatant_move_history[combatant.name]
        
        # Check each combo
        for combo in self.available_combos:
            combo_length = len(combo.required_sequence)
            
            # Make sure we have enough history
            if len(move_history) >= combo_length:
                # Check if the most recent moves match the combo
                recent_moves = move_history[-combo_length:]
                
                if recent_moves == combo.required_sequence:
                    # Combo found!
                    narrative_hooks = [
                        f"Executes the {combo.name} combo!",
                        combo.description
                    ]
                    
                    # Add special effect narratives
                    if "damage_bonus" in combo.bonus_effect:
                        narrative_hooks.append(f"The combo deals extra damage!")
                    if "critical_chance" in combo.bonus_effect:
                        narrative_hooks.append(f"The combo targets a critical weakness!")
                    if "ignore_defense" in combo.bonus_effect:
                        narrative_hooks.append(f"The combo bypasses defenses!")
                        
                    return combo, narrative_hooks
                    
        # No combo found
        return None
        
    def apply_combo_effects(self, combo: ComboMove, result: dict) -> dict:
        """Apply the effects of a combo to a combat result"""
        # Make a copy of the result to modify
        modified_result = result.copy()
        
        # Apply combo effects
        if "damage_bonus" in combo.bonus_effect:
            if "damage_dealt" in modified_result:
                modified_result["damage_dealt"] += combo.bonus_effect["damage_bonus"]
                
        if "momentum_bonus" in combo.bonus_effect:
            if "actor_momentum" in modified_result:
                modified_result["actor_momentum"] += combo.bonus_effect["momentum_bonus"]
                
        # Add the combo to the result
        if "combo_used" not in modified_result:
            modified_result["combo_used"] = combo.name
            
        return modified_result