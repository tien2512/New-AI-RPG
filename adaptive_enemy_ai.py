from typing import List, Dict, Any, Optional, Tuple
import random
from combat_system_core_v1_01 import Domain, MoveType, CombatMove, Combatant, Status

class EnemyPersonality:
    def __init__(self, 
                 aggression: float = 0.5,      # 0.0 to 1.0, how aggressive the enemy is
                 adaptability: float = 0.5,     # How quickly they learn from combat
                 risk_taking: float = 0.5,      # Willingness to use desperate moves
                 calculation: float = 0.5,      # Tendency to plan and use calculated moves
                 specialization: List[Domain] = None,  # Domains they favor
                 preferred_moves: List[MoveType] = None):  # Move types they prefer
        self.aggression = aggression
        self.adaptability = adaptability  
        self.risk_taking = risk_taking
        self.calculation = calculation
        self.specialization = specialization or []
        self.preferred_moves = preferred_moves or []
        
class CombatMemento:
    """Tracks what happened in previous rounds for AI decision making"""
    def __init__(self):
        self.player_moves_used = []
        self.successful_player_moves = []
        self.successful_enemy_moves = []
        self.player_patterns = {}  # Track patterns in player behavior
        
    def record_round(self, player_move: CombatMove, enemy_move: CombatMove, player_success: bool) -> None:
        """Record the results of a combat round"""
        # Track move types used
        self.player_moves_used.append(player_move.move_type)
        
        # Track successful moves
        if player_success:
            self.successful_player_moves.append(player_move.move_type)
        else:
            self.successful_enemy_moves.append(enemy_move.move_type)
            
        # Update pattern recognition
        self._update_player_patterns()
    
    def _update_player_patterns(self) -> None:
        """Analyze player's moves for patterns"""
        # Only analyze if we have enough history
        if len(self.player_moves_used) < 3:
            return
            
        # Look for sequences of 2 moves
        for i in range(len(self.player_moves_used) - 2):
            pattern = (self.player_moves_used[i], self.player_moves_used[i+1])
            follow_up = self.player_moves_used[i+2]
            
            pattern_key = f"{pattern[0].name}-{pattern[1].name}"
            if pattern_key not in self.player_patterns:
                self.player_patterns[pattern_key] = {}
                
            if follow_up.name not in self.player_patterns[pattern_key]:
                self.player_patterns[pattern_key][follow_up.name] = 0
                
            self.player_patterns[pattern_key][follow_up.name] += 1
    
    def predict_next_move(self) -> Optional[MoveType]:
        """Try to predict player's next move based on patterns"""
        if len(self.player_moves_used) < 2:
            return None
            
        # Get the last two moves
        last_moves = (self.player_moves_used[-2], self.player_moves_used[-1])
        pattern_key = f"{last_moves[0].name}-{last_moves[1].name}"
        
        if pattern_key in self.player_patterns:
            # Find the most common follow-up
            predictions = self.player_patterns[pattern_key]
            if predictions:
                # Get the move type with highest count
                most_common = max(predictions.items(), key=lambda x: x[1])
                for move_type in MoveType:
                    if move_type.name == most_common[0]:
                        return move_type
                        
        return None
        
class AdaptiveEnemyAI:
    def __init__(self, 
                 enemy: Combatant,
                 personality: EnemyPersonality = None,
                 available_moves: List[CombatMove] = None,
                 difficulty: float = 0.5):  # 0.0 to 1.0
        self.enemy = enemy
        self.personality = personality or EnemyPersonality()
        self.available_moves = available_moves or []
        self.difficulty = difficulty
        self.memento = CombatMemento()
        self.rounds_played = 0
        
        # Key elements that influence decision making
        self.desperation_threshold = 0.3  # Health % where enemy gets desperate
        
    def choose_move(self, 
                    player: Combatant, 
                    player_last_move: Optional[CombatMove] = None) -> CombatMove:
        """Choose the enemy's next move based on AI logic"""
        self.rounds_played += 1
        
        # Filter to moves the enemy can use
        usable_moves = [move for move in self.available_moves 
                      if self.enemy.can_use_move(move)]
        
        if not usable_moves:
            # If no usable moves, create a basic one with no cost
            return CombatMove(
                name="Desperate Action",
                move_type=MoveType.FORCE,
                domains=[Domain.BODY],
                description="A last-resort action",
                stamina_cost=0,
                focus_cost=0,
                spirit_cost=0
            )
        
        # Different selection strategies based on state and personality
        if self._is_desperate():
            return self._choose_desperate_move(usable_moves)
        elif self._should_counter(player_last_move):
            return self._choose_counter_move(usable_moves, player_last_move)
        elif self._should_exploit_weakness(player):
            return self._choose_weakness_targeting_move(usable_moves, player)
        else:
            return self._choose_standard_move(usable_moves, player)
    
    def _is_desperate(self) -> bool:
        """Determine if the enemy is in a desperate state"""
        health_ratio = self.enemy.current_health / self.enemy.max_health
        # More likely to get desperate if risk-taking is high
        adjusted_threshold = self.desperation_threshold - (self.personality.risk_taking * 0.15)
        return health_ratio <= adjusted_threshold
    
    def _should_counter(self, player_last_move: Optional[CombatMove]) -> bool:
        """Determine if the enemy should try to counter the player's last move"""
        if not player_last_move:
            return False
            
        # Higher adaptability means more likely to counter
        counter_chance = 0.2 + (self.personality.adaptability * 0.4)
        
        # If we've seen this move before and failed against it, more likely to counter
        if player_last_move.move_type in self.memento.successful_player_moves:
            counter_chance += 0.2
            
        return random.random() < counter_chance
    
    def _should_exploit_weakness(self, player: Combatant) -> bool:
        """Determine if the enemy should try to exploit player weaknesses"""
        # Check if player has any statuses that can be exploited
        has_exploitable_status = False
        for status in player.statuses:
            if status in [Status.WOUNDED, Status.CONFUSED, Status.STUNNED]:
                has_exploitable_status = True
                break
                
        # Higher aggression means more likely to exploit weaknesses
        exploit_chance = 0.3 + (self.personality.aggression * 0.4)
        if has_exploitable_status:
            exploit_chance += 0.2
            
        return random.random() < exploit_chance
    
    def _choose_desperate_move(self, usable_moves: List[CombatMove]) -> CombatMove:
        """Choose a move when in a desperate state"""
        # Prefer high damage moves, especially Force type
        force_moves = [move for move in usable_moves if move.move_type == MoveType.FORCE]
        
        if force_moves:
            chosen_move = random.choice(force_moves)
        else:
            chosen_move = random.choice(usable_moves)
            
        # Make it desperate for higher risk/reward
        chosen_move.is_desperate = True
        chosen_move.with_narrative_hook("Fights with desperate fury")
        return chosen_move
    
    def _choose_counter_move(self, usable_moves: List[CombatMove], 
                            player_move: CombatMove) -> CombatMove:
        """Choose a move that counters the player's move"""
        # Get the move type that counters the player's move
        counter_type = self._get_counter_move_type(player_move.move_type)
        
        # Find moves of the counter type
        counter_moves = [move for move in usable_moves if move.move_type == counter_type]
        
        if counter_moves:
            chosen_move = random.choice(counter_moves)
            # If enemy is calculating, use calculated approach
            if random.random() < self.personality.calculation:
                chosen_move.as_calculated()
                chosen_move.with_narrative_hook("Analyzes and counters your strategy")
            return chosen_move
        else:
            # No direct counter available, choose standard move
            return self._choose_standard_move(usable_moves, None)
    
    def _choose_weakness_targeting_move(self, usable_moves: List[CombatMove], 
                                      player: Combatant) -> CombatMove:
        """Choose a move that targets player weaknesses"""
        # Check for status-specific targeting
        if Status.WOUNDED in player.statuses:
            # Target physical weakness
            body_moves = [move for move in usable_moves 
                        if Domain.BODY in move.domains 
                        and move.move_type == MoveType.FORCE]
            if body_moves:
                chosen_move = random.choice(body_moves)
                chosen_move.with_narrative_hook("Targets your wounds")
                return chosen_move
                
        if Status.CONFUSED in player.statuses:
            # Target mental weakness
            mind_moves = [move for move in usable_moves 
                        if Domain.MIND in move.domains 
                        and move.move_type == MoveType.FOCUS]
            if mind_moves:
                chosen_move = random.choice(mind_moves)
                chosen_move.with_narrative_hook("Exploits your confusion")
                return chosen_move
        
        # Default to standard move if no specific weaknesses to target
        return self._choose_standard_move(usable_moves, player)
    
    def _choose_standard_move(self, usable_moves: List[CombatMove], 
                            player: Optional[Combatant]) -> CombatMove:
        """Choose a standard move based on personality and situation"""
        # Apply personality preferences
        preferred_moves = []
        
        # Filter by preferred move types if specified
        if self.personality.preferred_moves:
            type_filtered = [move for move in usable_moves 
                           if move.move_type in self.personality.preferred_moves]
            if type_filtered:
                preferred_moves = type_filtered
                
        # Filter by specialization domains if specified
        if not preferred_moves and self.personality.specialization:
            domain_filtered = [move for move in usable_moves 
                             if any(domain in move.domains 
                                  for domain in self.personality.specialization)]
            if domain_filtered:
                preferred_moves = domain_filtered
                
        # Use preferred moves if available, otherwise use all usable moves
        move_pool = preferred_moves if preferred_moves else usable_moves
        
        # Apply personality traits to move selection
        if random.random() < self.personality.aggression:
            # Aggressive: prefer Force moves
            force_moves = [move for move in move_pool if move.move_type == MoveType.FORCE]
            if force_moves:
                return random.choice(force_moves)
                
        if random.random() < self.personality.calculation:
            # Calculating: use a calculated approach
            chosen_move = random.choice(move_pool)
            return chosen_move.as_calculated()
            
        if random.random() < self.personality.risk_taking:
            # Risk taker: possibly use a desperate move
            chosen_move = random.choice(move_pool)
            return chosen_move.as_desperate()
            
        # Default: random selection from move pool
        return random.choice(move_pool)
    
    def _get_counter_move_type(self, move_type: MoveType) -> MoveType:
        """Get the move type that counters a given move type"""
        if move_type == MoveType.FORCE:
            return MoveType.FOCUS
        elif move_type == MoveType.TRICK:
            return MoveType.FORCE
        elif move_type == MoveType.FOCUS:
            return MoveType.TRICK
        else:
            # For other move types, default to the most appropriate counter
            if self.personality.preferred_moves:
                return self.personality.preferred_moves[0]
            else:
                return MoveType.FOCUS  # Default to Focus as a general counter
    
    def update_from_combat_result(self, result: dict) -> None:
        """Update AI behavior based on combat result"""
        # Extract relevant information
        player_move_type = None
        enemy_move_type = None
        
        for move_type in MoveType:
            if move_type.value == result.get("actor_move"):
                player_move_type = move_type
            if move_type.value == result.get("target_move"):
                enemy_move_type = move_type
                
        if not player_move_type or not enemy_move_type:
            return
            
        # Create dummy move objects for record keeping
        player_move = CombatMove("", player_move_type, [], "")
        enemy_move = CombatMove("", enemy_move_type, [], "")
        
        # Record the round
        self.memento.record_round(player_move, enemy_move, result.get("actor_success", False))
        
        # Adjust personality traits based on combat results
        self._adapt_personality(result)
    
    def _adapt_personality(self, result: dict) -> None:
        """Adjust personality traits based on combat results"""
        # Only adapt if adaptability is significant
        if self.personality.adaptability < 0.3:
            return
            
        # Get result info
        success = not result.get("actor_success", True)  # Enemy succeeded if player failed
        effect_magnitude = result.get("effect_magnitude", 0)
        
        # Adjust aggression
        if success and self.personality.aggression > 0.3:
            # If successful with current strategy, slightly reinforce it
            self.personality.aggression *= 1.05
            self.personality.aggression = min(1.0, self.personality.aggression)
        elif not success and self.personality.aggression > 0.3:
            # If unsuccessful, consider changing strategy
            self.personality.aggression *= 0.95
            
        # Adjust risk taking based on health and success
        health_ratio = self.enemy.current_health / self.enemy.max_health
        if health_ratio < 0.5 and not success:
            # Getting desperate, increase risk taking
            self.personality.risk_taking = min(1.0, self.personality.risk_taking * 1.1)
        elif success and effect_magnitude > 3:
            # Successful with big effect, reinforce current risk level
            pass
        else:
            # Gradually normalize risk taking
            self.personality.risk_taking = 0.5 + (self.personality.risk_taking - 0.5) * 0.95