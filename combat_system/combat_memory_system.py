from typing import List, Dict, Any, Optional
import json
from datetime import datetime

class CombatMemory:
    def __init__(self):
        self.encounters = []  # List of combat encounters
        self.opponent_history = {}  # History with specific opponents
        self.move_usage_stats = {}  # Stats on move usage and effectiveness
        
    def record_encounter(self, encounter_data: Dict[str, Any]) -> None:
        """Record a full combat encounter"""
        # Add timestamp
        encounter_data["timestamp"] = datetime.now().isoformat()
        
        # Add to encounters list
        self.encounters.append(encounter_data)
        
        # Update opponent histories
        for opponent in encounter_data.get("opponents", []):
            self._update_opponent_history(opponent, encounter_data)
            
        # Update move usage stats
        for move_record in encounter_data.get("moves_used", []):
            self._update_move_stats(move_record)
    
    def _update_opponent_history(self, opponent: Dict, encounter_data: Dict) -> None:
        """Update history with a specific opponent"""
        opponent_name = opponent.get("name")
        if not opponent_name:
            return
            
        if opponent_name not in self.opponent_history:
            self.opponent_history[opponent_name] = {
                "encounters": 0,
                "victories": 0,
                "defeats": 0,
                "last_encounter": None,
                "known_moves": set(),
                "known_weaknesses": set(),
                "known_strengths": set(),
                "narrative_moments": []
            }
            
        # Update stats
        history = self.opponent_history[opponent_name]
        history["encounters"] += 1
        history["last_encounter"] = encounter_data["timestamp"]
        
        # Record outcome
        if encounter_data.get("outcome") == "victory":
            history["victories"] += 1
        elif encounter_data.get("outcome") == "defeat":
            history["defeats"] += 1
            
        # Record moves used by opponent
        for move in opponent.get("moves_used", []):
            history["known_moves"].add(move["name"])
            
        # Record any discovered weaknesses/strengths
        for weakness in opponent.get("weaknesses_shown", []):
            history["known_weaknesses"].add(weakness)
        for strength in opponent.get("strengths_shown", []):
            history["known_strengths"].add(strength)
            
        # Record narrative moments
        if "notable_moments" in encounter_data:
            for moment in encounter_data["notable_moments"]:
                if moment.get("involves", "") == opponent_name:
                    history["narrative_moments"].append(moment)
    
    def _update_move_stats(self, move_record: Dict) -> None:
        """Update statistics for a specific move"""
        move_name = move_record.get("name")
        if not move_name:
            return
            
        if move_name not in self.move_usage_stats:
            self.move_usage_stats[move_name] = {
                "times_used": 0,
                "successful_uses": 0,
                "total_damage": 0,
                "average_damage": 0,
                "effectiveness_rating": 0
            }
            
        stats = self.move_usage_stats[move_name]
        stats["times_used"] += 1
        
        if move_record.get("success", False):
            stats["successful_uses"] += 1
            
        # Update damage stats if applicable
        if "damage" in move_record:
            stats["total_damage"] += move_record["damage"]
            stats["average_damage"] = stats["total_damage"] / stats["times_used"]
            
        # Calculate overall effectiveness rating (success rate * avg damage)
        success_rate = stats["successful_uses"] / stats["times_used"]
        stats["effectiveness_rating"] = success_rate * stats["average_damage"] if stats["average_damage"] else success_rate * 5
    
    def get_opponent_insights(self, opponent_name: str) -> Dict[str, Any]:
        """Get tactical insights about a specific opponent"""
        if opponent_name not in self.opponent_history:
            return {"known": False, "message": "No history with this opponent"}
            
        history = self.opponent_history[opponent_name]
        
        insights = {
            "known": True,
            "encounters": history["encounters"],
            "victory_rate": history["victories"] / history["encounters"] if history["encounters"] > 0 else 0,
            "known_moves": list(history["known_moves"]),
            "known_weaknesses": list(history["known_weaknesses"]),
            "known_strengths": list(history["known_strengths"]),
            "suggested_approaches": []
        }
        
        # Generate tactical suggestions based on history
        if history["known_weaknesses"]:
            insights["suggested_approaches"].append(
                f"Target their known weaknesses: {', '.join(history['known_weaknesses'])}"
            )
            
        if history["known_moves"]:
            # Suggest counters to their most common moves
            insights["suggested_approaches"].append(
                f"Prepare counters for their typical moves: {', '.join(list(history['known_moves'])[:3])}"
            )
            
        # Add narrative callback if there's history
        if history["narrative_moments"]:
            recent_moment = history["narrative_moments"][-1]
            insights["narrative_callback"] = recent_moment.get("description", "You've faced this opponent before.")
            
        return insights
    
    def save_to_file(self, filename: str) -> bool:
        """Save combat memory to a JSON file"""
        try:
            # Convert sets to lists for JSON serialization
            serializable_data = self._prepare_for_serialization()
            
            with open(filename, 'w') as f:
                json.dump(serializable_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving combat memory: {e}")
            return False
    
    def load_from_file(self, filename: str) -> bool:
        """Load combat memory from a JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            # Restore data structures
            self.encounters = data.get("encounters", [])
            
            # Restore opponent history with sets
            self.opponent_history = {}
            for opponent, history in data.get("opponent_history", {}).items():
                self.opponent_history[opponent] = history
                # Convert lists back to sets
                self.opponent_history[opponent]["known_moves"] = set(history.get("known_moves", []))
                self.opponent_history[opponent]["known_weaknesses"] = set(history.get("known_weaknesses", []))
                self.opponent_history[opponent]["known_strengths"] = set(history.get("known_strengths", []))
                
            self.move_usage_stats = data.get("move_usage_stats", {})
            return True
        except Exception as e:
            print(f"Error loading combat memory: {e}")
            return False
    
    def _prepare_for_serialization(self) -> Dict:
        """Prepare data for JSON serialization (convert sets to lists)"""
        serializable_data = {
            "encounters": self.encounters,
            "opponent_history": {},
            "move_usage_stats": self.move_usage_stats
        }
        
        # Convert sets to lists in opponent history
        for opponent, history in self.opponent_history.items():
            serializable_data["opponent_history"][opponent] = {
                **history,
                "known_moves": list(history["known_moves"]),
                "known_weaknesses": list(history["known_weaknesses"]),
                "known_strengths": list(history["known_strengths"])
            }
            
        return serializable_data

# Example integration with Langchain memory
def create_langchain_memory_integration(combat_memory: CombatMemory) -> Dict[str, Any]:
    """Create a dictionary of memory elements for Langchain integration"""
    memory_elements = {
        "recent_encounters": combat_memory.encounters[-3:] if combat_memory.encounters else [],
        "opponent_records": {},
        "most_effective_moves": _get_top_moves(combat_memory, 3),
        "narrative_hooks": _extract_narrative_hooks(combat_memory)
    }
    
    # Add opponent records for recently encountered opponents
    recent_opponents = set()
    for encounter in memory_elements["recent_encounters"]:
        for opponent in encounter.get("opponents", []):
            opponent_name = opponent.get("name")
            if opponent_name:
                recent_opponents.add(opponent_name)
                
    for opponent_name in recent_opponents:
        if opponent_name in combat_memory.opponent_history:
            memory_elements["opponent_records"][opponent_name] = combat_memory.opponent_history[opponent_name]
            
    return memory_elements

def _get_top_moves(combat_memory: CombatMemory, count: int) -> List[Dict]:
    """Get the most effective moves based on effectiveness rating"""
    move_stats = list(combat_memory.move_usage_stats.items())
    # Sort by effectiveness rating
    move_stats.sort(key=lambda x: x[1]["effectiveness_rating"], reverse=True)
    
    top_moves = []
    for move_name, stats in move_stats[:count]:
        top_moves.append({
            "name": move_name,
            "success_rate": stats["successful_uses"] / stats["times_used"] if stats["times_used"] > 0 else 0,
            "average_damage": stats["average_damage"],
            "effectiveness": stats["effectiveness_rating"]
        })
        
    return top_moves

def _extract_narrative_hooks(combat_memory: CombatMemory) -> List[str]:
    """Extract interesting narrative hooks from combat history"""
    hooks = []
    
    # Look for recurring opponents
    for opponent, history in combat_memory.opponent_history.items():
        if history["encounters"] > 1:
            hooks.append(f"You've faced {opponent} {history['encounters']} times before.")
            
        # Add victorious or defeat narratives
        if history["victories"] > 0 and history["defeats"] == 0:
            hooks.append(f"You've always emerged victorious against {opponent}.")
        elif history["defeats"] > 0 and history["victories"] == 0:
            hooks.append(f"{opponent} has bested you every time you've met.")
            
        # Add memorable moments
        if history["narrative_moments"]:
            recent_moment = history["narrative_moments"][-1]
            hooks.append(recent_moment.get("description", ""))
            
    return hooks
