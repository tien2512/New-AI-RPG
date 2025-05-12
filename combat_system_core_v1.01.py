from enum import Enum, auto
from typing import List, Dict, Optional, Tuple, Set
import random
from dataclasses import dataclass
from collections import defaultdict

# Core Enumerations
class Domain(Enum):
    BODY = "Body"       # Physical prowess, endurance, strength
    MIND = "Mind"       # Intelligence, reasoning, knowledge
    CRAFT = "Craft"     # Creation, technical skills, manipulation of objects
    AWARENESS = "Awareness"  # Perception, intuition, reflexes
    SOCIAL = "Social"   # Charisma, deception, persuasion
    AUTHORITY = "Authority"  # Command, intimidation, willpower
    SPIRIT = "Spirit"   # Faith, connection to otherworldly forces

class MoveType(Enum):
    FORCE = "Force"     # Direct attacks, overwhelming power - beats TRICK
    TRICK = "Trick"     # Deception, evasion, misdirection - beats FOCUS
    FOCUS = "Focus"     # Analysis, blocking, prediction - beats FORCE
    BUFF = "Buff"       # Enhance abilities or stats
    DEBUFF = "Debuff"   # Weaken opponent abilities or stats
    UTILITY = "Utility" # Environmental interaction, movement, etc.

class CombatantType(Enum):
    PLAYER = "Player"
    NPC = "NPC"
    ENEMY = "Enemy"
    ALLY = "Ally"
    OBJECT = "Object"  # For doors, traps, etc.

class Status(Enum):
    WOUNDED = "Wounded"     # Physical damage affecting Body
    CONFUSED = "Confused"   # Mental state affecting Mind
    STUNNED = "Stunned"     # Temporary inability to act
    FRIGHTENED = "Frightened"  # Fear affecting decision-making
    INSPIRED = "Inspired"   # Enhanced performance
    POISONED = "Poisoned"   # Ongoing damage over time
    BLEEDING = "Bleeding"   # Ongoing damage over time
    EXHAUSTED = "Exhausted" # Reduced stamina regeneration

@dataclass
class Consequence:
    """Represents a long-term effect resulting from combat"""
    description: str
    affected_domains: List[Domain]
    duration: int  # In encounters/scenes
    intensity: int  # 1-5 scale
    narrative_hook: str
    affected_stats: Dict[str, int] = None  # Stat modifiers

# Core Classes
class CombatMove:
    def __init__(self, 
                 name: str,
                 move_type: MoveType,
                 domains: List[Domain],
                 description: str,
                 stamina_cost: int = 0,
                 focus_cost: int = 0,
                 spirit_cost: int = 0):
        self.name = name
        self.move_type = move_type
        self.domains = domains
        self.description = description
        self.stamina_cost = stamina_cost
        self.focus_cost = focus_cost
        self.spirit_cost = spirit_cost
        self.target = None
        self.is_desperate = False
        self.is_calculated = False
        self.narrative_hook = None
    
    def set_target(self, target: 'Combatant'):
        self.move.target = target
        return self
    
    def as_desperate(self):
        """Mark move as desperate - higher risk, higher reward"""
        self.is_desperate = True
        return self
    
    def as_calculated(self):
        """Mark move as carefully planned - more likely to succeed but less impact"""
        self.is_calculated = True
        return self
    
    def with_narrative_hook(self, hook: str):
        """Add specific narrative element to influence AI description"""
        self.narrative_hook = hook
        return self
        
    def __str__(self):
        domains_str = ", ".join([d.value for d in self.domains])
        return f"{self.name} ({self.move_type.value}): {domains_str}"


class Combatant:
    def __init__(self, 
                 name: str, 
                 combatant_type: CombatantType,
                 domain_ratings: Dict[Domain, int],
                 max_health: int = 100,
                 max_stamina: int = 100,
                 max_focus: int = 100,
                 max_spirit: int = 100):
        self.name = name
        self.combatant_type = combatant_type
        self.domain_ratings = domain_ratings
        
        # Core stats
        self.max_health = max_health
        self.current_health = max_health
        self.max_stamina = max_stamina  
        self.current_stamina = max_stamina
        self.max_focus = max_focus
        self.current_focus = max_focus
        self.max_spirit = max_spirit
        self.current_spirit = max_spirit
        
        # Combat state
        self.statuses = set()  # Set of Status enums
        self.consequences = []  # List of Consequence objects
        
        # Known moves
        self.available_moves = []  # List of CombatMove objects
        
        # Memory/History
        self.combat_memory = []  # List of past interactions
        self.weak_domains = []  # Domains this combatant is weak against
        self.strong_domains = []  # Domains this combatant is strong with
    
    def add_move(self, move: CombatMove):
        self.available_moves.append(move)
    
    def apply_damage(self, amount: int, domains: List[Domain] = None):
        """Apply damage to health with optional domain context"""
        self.current_health = max(0, self.current_health - amount)
        
        # Domain-specific processing could go here
        wounded = False
        if self.current_health < self.max_health * 0.5 and Status.WOUNDED not in self.statuses:
            self.statuses.add(Status.WOUNDED)
            wounded = True
            
        return {
            "damage_dealt": amount,
            "current_health": self.current_health,
            "wounded": wounded
        }
    
    def apply_status(self, status: Status, duration: int = 3):
        """Apply a status effect"""
        self.statuses.add(status)
        
        # Status-specific logic could go here
        # For example, CONFUSED might reduce Mind domain effectiveness
        
        return {
            "status_applied": status.value,
            "duration": duration
        }
    
    def get_domain_rating(self, domain: Domain) -> int:
        """Get effective domain rating accounting for statuses"""
        base_rating = self.domain_ratings.get(domain, 0)
        
        # Apply modifiers from statuses
        if Status.WOUNDED in self.statuses and domain == Domain.BODY:
            base_rating -= 1
        if Status.CONFUSED in self.statuses and domain == Domain.MIND:
            base_rating -= 1
        # Add more status effects as needed
        
        return max(0, base_rating)  # Can't go below 0
    
    def can_use_move(self, move: CombatMove) -> bool:
        """Check if combatant has resources to use this move"""
        if move.stamina_cost > self.current_stamina:
            return False
        if move.focus_cost > self.current_focus:
            return False
        if move.spirit_cost > self.current_spirit:
            return False
        return True
    
    def pay_move_costs(self, move: CombatMove):
        """Pay the costs to use a move"""
        self.current_stamina -= move.stamina_cost
        self.current_focus -= move.focus_cost
        self.current_spirit -= move.spirit_cost
        
    def is_defeated(self) -> bool:
        """Check if combatant is defeated"""
        return self.current_health <= 0


class CombatSystem:
    def __init__(self):
        self.combat_log = []  # List of combat events for memory
        self.momentum = defaultdict(int)  # Track momentum per combatant
        self.environment_tags = set()  # Current environment properties
        self.round_counter = 0
    
    def resolve_opposed_moves(self, 
                              actor: Combatant, 
                              actor_move: CombatMove,
                              target: Combatant, 
                              target_move: CombatMove) -> dict:
        """Resolve two opposed moves against each other"""
        # Check if actors can use their moves
        if not actor.can_use_move(actor_move):
            return {"success": False, "reason": f"{actor.name} lacks resources for {actor_move.name}"}
        
        if not target.can_use_move(target_move):
            return {"success": False, "reason": f"{target.name} lacks resources for {target_move.name}"}
        
        # Pay costs
        actor.pay_move_costs(actor_move)
        target.pay_move_costs(target_move)
        
        # Type advantage (rock-paper-scissors)
        type_advantage = self._calculate_type_advantage(actor_move.move_type, target_move.move_type)
        
        # Calculate base rolls (domain + d6)
        actor_roll = self._calculate_move_roll(actor, actor_move)
        target_roll = self._calculate_move_roll(target, target_move)
        
        # Apply type advantage
        if type_advantage > 0:  # Actor has advantage
            actor_roll += 2
        elif type_advantage < 0:  # Target has advantage
            target_roll += 2
        
        # Apply momentum
        actor_roll += self.momentum[actor.name]
        target_roll += self.momentum[target.name]
        
        # Apply desperate/calculated modifiers
        if actor_move.is_desperate:
            actor_roll += random.randint(-3, 5)  # High variance
        if actor_move.is_calculated:
            actor_roll = max(actor_roll, actor_roll - 1 + random.randint(0, 2))  # More consistent
            
        # Apply target modifiers
        if target_move.is_desperate:
            target_roll += random.randint(-3, 5)
        if target_move.is_calculated:
            target_roll = max(target_roll, target_roll - 1 + random.randint(0, 2))
        
        # Determine winner
        actor_success = actor_roll > target_roll
        
        # Update momentum - winner gains, loser loses
        if actor_success:
            self.momentum[actor.name] = min(3, self.momentum[actor.name] + 1)
            self.momentum[target.name] = max(0, self.momentum[target.name] - 1)
        else:
            self.momentum[target.name] = min(3, self.momentum[target.name] + 1)
            self.momentum[actor.name] = max(0, self.momentum[actor.name] - 1)
        
        # Calculate effect magnitude based on difference in rolls
        effect_magnitude = abs(actor_roll - target_roll)
        
        # Process damage or effects
        result = {
            "actor": actor.name,
            "target": target.name,
            "actor_move": actor_move.name,
            "target_move": target_move.name,
            "actor_roll": actor_roll,
            "target_roll": target_roll,
            "actor_success": actor_success,
            "effect_magnitude": effect_magnitude,
            "type_advantage": type_advantage,
            "actor_momentum": self.momentum[actor.name],
            "target_momentum": self.momentum[target.name],
            "narrative_hooks": []
        }
        
        # Apply effects based on move type and success
        if actor_success:
            # Actor's move succeeds
            damage = effect_magnitude * 5
            
            # Add domain bonuses to damage
            for domain in actor_move.domains:
                if domain in target.weak_domains:
                    damage += 5
                    result["narrative_hooks"].append(f"Exploits {domain.value} weakness")
            
            if actor_move.is_desperate:
                damage *= 1.5  # Desperate moves hit harder
                
            # Apply damage
            if actor_move.move_type in [MoveType.FORCE, MoveType.TRICK]:
                damage_result = target.apply_damage(int(damage), actor_move.domains)
                result.update(damage_result)
            
            # Apply status effects based on move type
            if actor_move.move_type == MoveType.FOCUS:
                # Focus moves might apply mental statuses
                if Domain.MIND in actor_move.domains:
                    status_result = target.apply_status(Status.CONFUSED)
                    result.update(status_result)
                    result["narrative_hooks"].append("Creates mental confusion")
                
            if MoveType.DEBUFF:
                # Generic debuff effect
                status_to_apply = random.choice([Status.STUNNED, Status.FRIGHTENED])
                status_result = target.apply_status(status_to_apply)
                result.update(status_result)
            
        else:
            # Target successfully defends/counters
            if target_move.move_type == MoveType.FOCUS:
                result["narrative_hooks"].append("Perfectly reads the situation")
            
            if type_advantage < 0:
                result["narrative_hooks"].append("Counter-move was perfectly chosen")
            
        # Add narrative hooks
        if actor_move.narrative_hook:
            result["narrative_hooks"].append(actor_move.narrative_hook)
        if target_move.narrative_hook:
            result["narrative_hooks"].append(target_move.narrative_hook)
        
        # Log combat event for memory
        self.combat_log.append(result)
        self.round_counter += 1
        
        return result
    
    def _calculate_type_advantage(self, actor_type: MoveType, target_type: MoveType) -> int:
        """Calculate type advantage using the rock-paper-scissors system
        Returns: 1 if actor has advantage, -1 if target has advantage, 0 if neutral
        """
        # Basic RPS: Force > Trick > Focus > Force
        if actor_type == MoveType.FORCE and target_type == MoveType.TRICK:
            return 1
        elif actor_type == MoveType.TRICK and target_type == MoveType.FOCUS:
            return 1
        elif actor_type == MoveType.FOCUS and target_type == MoveType.FORCE:
            return 1
        elif target_type == MoveType.FORCE and actor_type == MoveType.TRICK:
            return -1
        elif target_type == MoveType.TRICK and actor_type == MoveType.FOCUS:
            return -1
        elif target_type == MoveType.FOCUS and actor_type == MoveType.FORCE:
            return -1
        else:
            return 0
    
    def _calculate_move_roll(self, combatant: Combatant, move: CombatMove) -> int:
        """Calculate the effectiveness roll for a move"""
        # Base roll is d6
        roll = random.randint(1, 6)
        
        # Add highest relevant domain rating
        best_domain_rating = 0
        for domain in move.domains:
            domain_rating = combatant.get_domain_rating(domain)
            best_domain_rating = max(best_domain_rating, domain_rating)
        
        roll += best_domain_rating
        
        # Apply environmental modifiers
        for domain in move.domains:
            if domain == Domain.AWARENESS and "Shadowy" in self.environment_tags:
                roll += 1
            if domain == Domain.BODY and "Confined" in self.environment_tags:
                roll -= 1
            # Add more environmental interactions
        
        return roll
    
    def create_consequence(self, result: dict, target: Combatant) -> Optional[Consequence]:
        """Create a lasting consequence based on combat result"""
        if not result["actor_success"] or result["effect_magnitude"] < 3:
            return None  # No significant consequence
            
        # Determine affected domains based on the move
        actor_move = next((m for m in self.combat_log if m["actor_move"] == result["actor_move"]), None)
        if not actor_move:
            return None
            
        affected_domains = []
        for domain_str in actor_move["domains"]:
            try:
                affected_domains.append(Domain[domain_str.upper()])
            except KeyError:
                continue
                
        # Create appropriate consequence based on domains and move type
        if result["effect_magnitude"] >= 5:
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


# Example Move Library
def create_move_library() -> Dict[str, CombatMove]:
    """Create a library of example moves"""
    moves = {}
    
    # Force moves
    moves["hammer_blow"] = CombatMove(
        name="Hammer Blow",
        move_type=MoveType.FORCE,
        domains=[Domain.BODY, Domain.CRAFT],
        description="A powerful overhead strike",
        stamina_cost=2
    )
    
    moves["commanding_shout"] = CombatMove(
        name="Commanding Shout",
        move_type=MoveType.FORCE,
        domains=[Domain.AUTHORITY, Domain.SOCIAL],
        description="A forceful command that stuns opponents",
        focus_cost=1,
        spirit_cost=1
    )
    
    # Trick moves
    moves["feinting_strike"] = CombatMove(
        name="Feinting Strike",
        move_type=MoveType.TRICK,
        domains=[Domain.AWARENESS, Domain.BODY],
        description="A deceptive attack that misdirects",
        stamina_cost=1,
        focus_cost=1
    )
    
    moves["shadow_step"] = CombatMove(
        name="Shadow Step",
        move_type=MoveType.TRICK,
        domains=[Domain.AWARENESS],
        description="A quick, evasive maneuver",
        stamina_cost=2
    )
    
    # Focus moves
    moves["analytical_defense"] = CombatMove(
        name="Analytical Defense",
        move_type=MoveType.FOCUS,
        domains=[Domain.MIND],
        description="Carefully analyze and counter opponent's strategy",
        focus_cost=2
    )
    
    moves["spiritual_insight"] = CombatMove(
        name="Spiritual Insight",
        move_type=MoveType.FOCUS,
        domains=[Domain.SPIRIT, Domain.AWARENESS],
        description="Call upon spiritual powers to predict attacks",
        spirit_cost=2
    )
    
    # Buff moves
    moves["inspiring_speech"] = CombatMove(
        name="Inspiring Speech",
        move_type=MoveType.BUFF,
        domains=[Domain.SOCIAL, Domain.AUTHORITY],
        description="Rally allies with inspiring words",
        focus_cost=1,
        spirit_cost=1
    )
    
    # Utility moves
    moves["improvised_trap"] = CombatMove(
        name="Improvised Trap",
        move_type=MoveType.UTILITY,
        domains=[Domain.CRAFT, Domain.AWARENESS],
        description="Quickly fashion a trap from available materials",
        stamina_cost=1,
        focus_cost=1
    )
    
    return moves


# Helper function for intent parsing
def parse_player_intent(intent_text: str, move_library: Dict[str, CombatMove]) -> CombatMove:
    """
    Placeholder for Langchain-based intent parsing
    In reality, this would use LLM to interpret player's natural language intent
    """
    # This is where you would integrate with Langchain
    # For demonstration, we'll do simple keyword matching
    intent_lower = intent_text.lower()
    
    # Check for move types
    move_type = None
    if any(word in intent_lower for word in ["attack", "strike", "hit", "smash", "bash"]):
        move_type = MoveType.FORCE
    elif any(word in intent_lower for word in ["trick", "feint", "deceive", "distract"]):
        move_type = MoveType.TRICK
    elif any(word in intent_lower for word in ["analyze", "watch", "predict", "focus"]):
        move_type = MoveType.FOCUS
    
    # Check for domains
    domains = []
    if any(word in intent_lower for word in ["strength", "muscle", "physical", "body"]):
        domains.append(Domain.BODY)
    if any(word in intent_lower for word in ["smart", "mind", "think", "intellect"]):
        domains.append(Domain.MIND)
    if any(word in intent_lower for word in ["craft", "make", "build", "create"]):
        domains.append(Domain.CRAFT)
    if any(word in intent_lower for word in ["see", "hear", "sense", "aware"]):
        domains.append(Domain.AWARENESS)
    if any(word in intent_lower for word in ["talk", "charm", "persuade", "social"]):
        domains.append(Domain.SOCIAL)
    if any(word in intent_lower for word in ["command", "intimidate", "authority"]):
        domains.append(Domain.AUTHORITY)
    if any(word in intent_lower for word in ["faith", "spirit", "divine", "mystical"]):
        domains.append(Domain.SPIRIT)
    
    # If no domains detected, default to BODY
    if not domains:
        domains = [Domain.BODY]
    
    # Find matching move from library or create custom one
    for move in move_library.values():
        if move.move_type == move_type and all(d in move.domains for d in domains):
            return move
    
    # Create a custom move if no match found
    return CombatMove(
        name="Custom Move",
        move_type=move_type or MoveType.FORCE,  # Default to FORCE if no type detected
        domains=domains,
        description=intent_text,
        stamina_cost=1  # Default cost
    )


# Example usage
if __name__ == "__main__":
    # Create combat system
    combat_system = CombatSystem()
    
    # Set up environment
    combat_system.environment_tags = {"Shadowy", "Confined"}
    
    # Create move library
    move_library = create_move_library()
    
    # Create player
    player = Combatant(
        name="Hero",
        combatant_type=CombatantType.PLAYER,
        domain_ratings={
            Domain.BODY: 3,
            Domain.MIND: 2,
            Domain.CRAFT: 2,
            Domain.AWARENESS: 3,
            Domain.SOCIAL: 1,
            Domain.AUTHORITY: 2,
            Domain.SPIRIT: 1
        }
    )
    
    # Create enemy
    bandit = Combatant(
        name="Bandit",
        combatant_type=CombatantType.ENEMY,
        domain_ratings={
            Domain.BODY: 2,
            Domain.MIND: 1,
            Domain.CRAFT: 1,
            Domain.AWARENESS: 2,
            Domain.SOCIAL: 1,
            Domain.AUTHORITY: 1,
            Domain.SPIRIT: 0
        },
        max_health=50
    )
    bandit.weak_domains = [Domain.MIND]
    
    # Parse player intent
    player_intent = "I want to fake a lunge and then strike from below"
    player_move = parse_player_intent(player_intent, move_library)
    
    # Choose enemy move (would be handled by AI in real system)
    bandit_move = move_library["analytical_defense"]
    
    # Resolve combat
    result = combat_system.resolve_opposed_moves(player, player_move, bandit, bandit_move)
    
    # Generate narrative (would be handled by LLM in real system)
    print(f"Combat Result: {result}")
    
    # Create consequence if applicable
    if result["actor_success"]:
        consequence = combat_system.create_consequence(result, bandit)
        if consequence:
            print(f"Consequence: {consequence}")
