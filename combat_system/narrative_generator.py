from typing import List, Dict, Any
import json

class CombatNarrativeGenerator:
    def __init__(self, openrouter_api_key: str = None):
        self.api_key = openrouter_api_key
        self.narrative_templates = self._load_narrative_templates()
        self.descriptive_cache = {}  # Cache for common descriptions
        
    def _load_narrative_templates(self) -> Dict:
        """Load narrative templates for different combat situations"""
        # In a real implementation, these would be loaded from a file
        return {
            "move_success": [
                "{actor} executes {move} with precision. {target} {reaction}.",
                "With skillful application of {domain}, {actor}'s {move} lands true. {target} {reaction}.",
                "{actor} channels their {domain} expertise into a powerful {move}. {target} {reaction}."
            ],
            "move_failure": [
                "{target} anticipates {actor}'s {move} and {counter}.",
                "{actor}'s {move} fails to connect as {target} {counter}.",
                "Despite drawing on {domain}, {actor}'s {move} is thwarted when {target} {counter}."
            ],
            "status_applied": [
                "{target} is now {status} from the effects of {move}.",
                "The {move} leaves {target} {status}.",
                "{actor}'s {move} results in {target} becoming {status}."
            ],
            "critical_success": [
                "In a display of extraordinary skill, {actor}'s {move} strikes a critical weakness!",
                "{actor} executes {move} with uncanny precision, finding the perfect opening!",
                "A moment of perfect execution! {actor}'s {move} lands with devastating effect!"
            ],
            "environment_interaction": [
                "{actor} uses the {environment} to their advantage, {interaction_effect}.",
                "The {environment} becomes a weapon in {actor}'s hands, {interaction_effect}.",
                "Drawing on the surroundings, {actor} {interaction_effect} using the {environment}."
            ]
        }
    
    async def generate_combat_narrative(self, combat_result: Dict[str, Any],
                                      actor: Dict, target: Dict,
                                      environment_tags: List[str],
                                      memory_context: Dict = None) -> Dict[str, str]:
        """Generate narrative descriptions for a combat round
        
        Returns a dictionary with different narrative elements:
            - action_description: The main action narrative
            - environment_description: How the environment affected the action
            - consequence_description: Description of any lasting consequences
            - emotion_description: The emotional impact of the action
            - memory_callback: Reference to past encounters if relevant
        """
        # Prepare the base context from combat result
        context = self._prepare_narrative_context(combat_result, actor, target, environment_tags)
        
        # Add memory context if available
        if memory_context:
            context.update(self._prepare_memory_context(memory_context))
            
        # If no API key, use template-based generation
        if not self.api_key:
            return self._generate_from_templates(context)
            
        # Otherwise, use LLM via OpenRouter
        return await self._generate_from_llm(context)
    
    def _prepare_narrative_context(self, combat_result: Dict, actor: Dict, 
                                 target: Dict, environment_tags: List[str]) -> Dict:
        """Prepare context for narrative generation"""
        context = {
            "actor_name": actor.get("name", "The attacker"),
            "target_name": target.get("name", "The defender"),
            "move_name": combat_result.get("actor_move", "attack"),
            "move_type": self._get_move_type_description(combat_result.get("actor_move_type")),
            "success": combat_result.get("actor_success", False),
            "effect_magnitude": combat_result.get("effect_magnitude", 0),
            "environment": environment_tags,
            "narrative_hooks": combat_result.get("narrative_hooks", []),
            "combo_used": combat_result.get("combo_used"),
            "status_applied": combat_result.get("status_applied"),
            "actor_domains": actor.get("domains", []),
            "target_domains": target.get("domains", []),
            "desperation": combat_result.get("actor_desperate", False),
            "calculation": combat_result.get("actor_calculated", False),
        }
        
        # Add reaction based on success
        if context["success"]:
            damage = combat_result.get("damage_dealt", 0)
            if damage > 20:
                context["target_reaction"] = "staggers backward, severely wounded"
            elif damage > 10:
                context["target_reaction"] = "winces in pain"
            else:
                context["target_reaction"] = "absorbs the blow"
        else:
            counter_type = combat_result.get("target_move_type")
            if counter_type == "FORCE":
                context["target_counter"] = "responds with overwhelming force"
            elif counter_type == "TRICK":
                context["target_counter"] = "deftly evades"
            elif counter_type == "FOCUS":
                context["target_counter"] = "perfectly anticipates the attack"
            else:
                context["target_counter"] = "defends effectively"
                
        return context
    
    def _prepare_memory_context(self, memory_context: Dict) -> Dict:
        """Prepare memory-related context for narrative generation"""
        memory_elements = {}
        
        # Add history with this opponent if available
        opponent_name = memory_context.get("current_opponent_name")
        if opponent_name and opponent_name in memory_context.get("opponent_records", {}):
            record = memory_context["opponent_records"][opponent_name]
            memory_elements["previous_encounters"] = record["encounters"]
            memory_elements["victory_record"] = f"{record['victories']} wins, {record['defeats']} losses"
            
            # Add narrative callbacks if available
            if record.get("narrative_moments"):
                memory_elements["past_moment"] = record["narrative_moments"][-1].get("description")
                
        # Add recently used effective moves if available
        if "most_effective_moves" in memory_context:
            memory_elements["effective_move"] = memory_context["most_effective_moves"][0]["name"]
            
        return {"memory": memory_elements}
    
    def _get_move_type_description(self, move_type: str) -> str:
        """Get a descriptive phrase for a move type"""
        if not move_type:
            return "skillful attack"
            
        descriptions = {
            "FORCE": ["powerful", "forceful", "mighty", "overwhelming"],
            "TRICK": ["deceptive", "cunning", "tricky", "clever"],
            "FOCUS": ["precise", "calculated", "focused", "analytical"],
            "BUFF": ["supportive", "enhancing", "empowering", "strengthening"],
            "DEBUFF": ["weakening", "hindering", "disabling", "hampering"],
            "UTILITY": ["versatile", "resourceful", "adaptive", "practical"]
        }
        
        move_type_upper = move_type.upper() if isinstance(move_type, str) else ""
        options = descriptions.get(move_type_upper, ["skillful"])
        
        # Cache common descriptions
        cache_key = f"{move_type_upper}_desc"
        if cache_key not in self.descriptive_cache:
            import random
            self.descriptive_cache[cache_key] = random.choice(options)
            
        return self.descriptive_cache[cache_key]
    
    def _generate_from_templates(self, context: Dict) -> Dict[str, str]:
        """Generate narrative using templates"""
        import random
        
        narratives = {}
        
        # Select the right template category
        if context["success"]:
            if context["effect_magnitude"] > 5:
                template_category = "critical_success"
            else:
                template_category = "move_success"
        else:
            template_category = "move_failure"
            
        # Select and fill a template for the main action
        templates = self.narrative_templates[template_category]
        template = random.choice(templates)
        
        # Basic replacements
        filled_template = template.replace("{actor}", context["actor_name"])
        filled_template = filled_template.replace("{target}", context["target_name"])
        filled_template = filled_template.replace("{move}", context["move_name"])
        
        # More complex replacements
        if "{domain}" in filled_template:
            if context["actor_domains"]:
                domain = random.choice(context["actor_domains"])
                filled_template = filled_template.replace("{domain}", domain)
            else:
                filled_template = filled_template.replace("{domain}", "skill")
                
        if "{reaction}" in filled_template and "target_reaction" in context:
            filled_template = filled_template.replace("{reaction}", context["target_reaction"])
            
        if "{counter}" in filled_template and "target_counter" in context:
            filled_template = filled_template.replace("{counter}", context["target_counter"])
            
        narratives["action_description"] = filled_template
        
        # Add environment description if available
        if context["environment"]:
            env = random.choice(context["environment"])
            env_template = random.choice(self.narrative_templates["environment_interaction"])
            
            # Generate a random interaction effect
            effects = [
                "gains an advantage",
                "creates an opening",
                "improves their position",
                "finds a tactical opportunity"
            ]
            
            env_narrative = env_template.replace("{actor}", context["actor_name"])
            env_narrative = env_narrative.replace("{environment}", env)
            env_narrative = env_narrative.replace("{interaction_effect}", random.choice(effects))
            
            narratives["environment_description"] = env_narrative
        else:
            narratives["environment_description"] = ""
            
        # Add memory callback if available
        if "memory" in context and "past_moment" in context["memory"]:
            narratives["memory_callback"] = context["memory"]["past_moment"]
        else:
            narratives["memory_callback"] = ""
            
        # Generate a basic consequence description
        if context["success"] and context["effect_magnitude"] > 3:
            consequence = f"This powerful strike might leave lasting damage on {context['target_name']}."
            narratives["consequence_description"] = consequence
        else:
            narratives["consequence_description"] = ""
            
        # Generate a basic emotion description
        if context["success"]:
            emotion = f"{context['actor_name']} feels a surge of confidence."
            if "memory" in context and context["memory"].get("previous_encounters", 0) > 1:
                emotion += f" There's history between these combatants that fuels the intensity."
        else:
            emotion = f"{context['actor_name']} feels frustrated by the failed attempt
