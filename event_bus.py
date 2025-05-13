"""
Event bus system for game events.

This module provides the core event infrastructure for the game engine,
allowing different systems to communicate via a publish-subscribe pattern.
It is designed to handle long campaigns with detailed event tracking.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional, Union, Set
from collections import defaultdict
from enum import Enum, auto


class EventType(Enum):
    """Event types for the game engine."""
    # Character events
    CHARACTER_CREATED = auto()
    CHARACTER_UPDATED = auto()
    CHARACTER_DELETED = auto()
    LEVEL_UP = auto()
    DOMAIN_INCREASED = auto()
    TAG_INCREASED = auto()
    
    # Action events
    ACTION_PERFORMED = auto()
    SKILL_CHECK = auto()
    DOMAIN_CHECK = auto()
    
    # Inventory events
    ITEM_ACQUIRED = auto()
    ITEM_USED = auto()
    ITEM_CRAFTED = auto()
    ITEM_SOLD = auto()
    
    # Combat events
    COMBAT_STARTED = auto()
    COMBAT_ENDED = auto()
    ATTACK_PERFORMED = auto()
    DAMAGE_DEALT = auto()
    DAMAGE_TAKEN = auto()
    ENEMY_DEFEATED = auto()
    CHARACTER_DEFEATED = auto()
    
    # NPC events
    NPC_INTERACTION = auto()
    NPC_RELATIONSHIP_CHANGED = auto()
    
    # Location events
    LOCATION_DISCOVERED = auto()
    LOCATION_ENTERED = auto()
    LOCATION_EXITED = auto()
    
    # Quest events
    QUEST_STARTED = auto()
    QUEST_UPDATED = auto()
    QUEST_COMPLETED = auto()
    QUEST_FAILED = auto()
    
    # Game session events
    GAME_STARTED = auto()
    GAME_SAVED = auto()
    GAME_LOADED = auto()
    GAME_ENDED = auto()
    
    # Economy events
    TRANSACTION_COMPLETED = auto()
    ITEM_PRICE_CHANGED = auto()
    SHOP_INVENTORY_UPDATED = auto()
    
    # Basebuilding events
    STRUCTURE_BUILT = auto()
    STRUCTURE_UPGRADED = auto()
    RESOURCE_GATHERED = auto()
    
    # Kingdom management events
    TERRITORY_ACQUIRED = auto()
    LAW_ENACTED = auto()
    DIPLOMATIC_RELATION_CHANGED = auto()
    
    # Crafting events
    RECIPE_LEARNED = auto()
    ITEM_CRAFTED_SUCCESS = auto()
    ITEM_CRAFTED_FAILURE = auto()
    MATERIAL_GATHERED = auto()
    
    # System events
    ERROR = auto()
    WARNING = auto()
    INFO = auto()
    
    # Wildcard for all events
    WILDCARD = "*"
    
    @classmethod
    def from_string(cls, event_type_str: str) -> 'EventType':
        """
        Convert a string to an EventType.
        
        Args:
            event_type_str: The string to convert
            
        Returns:
            The corresponding EventType, or WILDCARD if the string is "*"
            
        Raises:
            ValueError: If the string is not a valid EventType
        """
        if event_type_str == "*":
            return cls.WILDCARD
            
        for event_type in cls:
            if event_type.name == event_type_str:
                return event_type
                
        raise ValueError(f"Invalid event type: {event_type_str}")


class GameEvent:
    """
    Game event object that encapsulates event information.
    
    Attributes:
        id: Unique identifier for the event
        type: The type of the event
        actor: The entity that triggered the event (character, NPC, system, etc.)
        context: Additional contextual information about the event
        metadata: Additional metadata about the event
        tags: List of tags for categorizing the event
        effects: List of effects resulting from the event
        timestamp: The time when the event occurred
    """
    def __init__(self, 
                 type: Union[EventType, str], 
                 actor: str, 
                 context: Optional[Dict[str, Any]] = None, 
                 metadata: Optional[Dict[str, Any]] = None,
                 tags: Optional[List[str]] = None,
                 effects: Optional[List[Dict[str, Any]]] = None,
                 game_id: Optional[str] = None):
        """
        Initialize a new game event.
        
        Args:
            type: The type of the event (EventType enum or string)
            actor: The entity that triggered the event
            context: Additional contextual information about the event
            metadata: Additional metadata about the event
            tags: List of tags for categorizing the event
            effects: List of effects resulting from the event
            game_id: ID of the game this event belongs to (for multi-game support)
        """
        self.id = str(uuid.uuid4())
        
        # Handle string event types for flexibility
        if isinstance(type, str):
            try:
                self.type = EventType.from_string(type)
            except ValueError:
                # If not a valid enum name, store as string but print warning
                print(f"Warning: Unknown event type '{type}', treating as custom event type")
                self.type = type
        else:
            self.type = type
            
        self.actor = actor
        self.context = context or {}
        self.metadata = metadata or {}
        self.tags = tags or []
        self.effects = effects or []
        self.game_id = game_id
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary representation.
        
        Returns:
            Dictionary representation of the event
        """
        type_repr = self.type.name if isinstance(self.type, EventType) else str(self.type)
        
        return {
            "id": self.id,
            "type": type_repr,
            "actor": self.actor,
            "context": self.context,
            "metadata": self.metadata,
            "tags": self.tags,
            "effects": self.effects,
            "game_id": self.game_id,
            "timestamp": self.timestamp
        }
    
    def summarize(self) -> Dict[str, Any]:
        """
        Create a condensed summary of this event.
        
        Returns:
            A summary dictionary with essential information
        """
        type_repr = self.type.name if isinstance(self.type, EventType) else str(self.type)
        
        # Create a basic summary string based on type and context
        if "location" in self.context:
            summary = f"{self.actor} {type_repr} at {self.context['location']}"
        elif "target" in self.context:
            summary = f"{self.actor} {type_repr} on {self.context['target']}"
        else:
            summary = f"{self.actor} triggered {type_repr}"
            
        # Add key context details
        context_summary = ", ".join(f"{k}={v}" for k, v in self.context.items() 
                                   if k in ['result', 'success', 'amount', 'duration'])
        if context_summary:
            summary += f" with {context_summary}"
            
        return {
            "id": self.id,
            "type": type_repr,
            "actor": self.actor,
            "summary": summary,
            "tags": self.tags[:3],  # Limit to 3 tags for brevity
            "timestamp": self.timestamp
        }
    
    def __str__(self) -> str:
        """String representation of the event."""
        type_repr = self.type.name if isinstance(self.type, EventType) else str(self.type)
        return (f"GameEvent({type_repr}, actor={self.actor}, "
                f"context={self.context}, tags={self.tags}, timestamp={self.timestamp})")


class EventLogger:
    """
    Logger for game events with persistence capabilities.
    
    Attributes:
        history: List of events that have been logged
        max_history: Maximum number of events to keep in memory
        log_to_file: Whether to log events to a file
        log_dir: Directory for log files
    """
    def __init__(self, 
                 max_history: int = 1000, 
                 log_to_file: bool = True,
                 log_dir: str = "logs/events"):
        """
        Initialize a new event logger.
        
        Args:
            max_history: Maximum number of events to keep in memory
            log_to_file: Whether to log events to a file
            log_dir: Directory for log files
        """
        self.history: List[Dict[str, Any]] = []
        self.max_history = max_history
        self.log_to_file = log_to_file
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        if self.log_to_file and not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

    def log(self, event: GameEvent) -> None:
        """
        Log an event.
        
        Args:
            event: The event to log
        """
        event_dict = event.to_dict()
        self.history.append(event_dict)
        
        # Trim history if it exceeds max size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Write to file if enabled
        if self.log_to_file:
            self._write_to_file(event)
    
    def _write_to_file(self, event: GameEvent) -> None:
        """
        Write an event to a log file.
        
        Args:
            event: The event to write
        """
        try:
            # Determine file path based on game_id if available
            if event.game_id:
                log_file = os.path.join(self.log_dir, f"game_{event.game_id}.jsonl")
            else:
                log_file = os.path.join(self.log_dir, "events.jsonl")
                
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            print(f"Error writing event to log file: {e}")
        
    def get_history(self, 
                    event_types: Optional[List[Union[EventType, str]]] = None, 
                    actor: Optional[str] = None,
                    game_id: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get filtered event history.
        
        Args:
            event_types: Optional filter for event types
            actor: Optional filter for actor
            game_id: Optional filter for game ID
            tags: Optional filter for tags (event must have at least one of these tags)
            limit: Optional limit on number of events returned
            
        Returns:
            Filtered list of events
        """
        filtered_history = self.history
        
        if event_types:
            event_type_names = [
                et.name if isinstance(et, EventType) else str(et) 
                for et in event_types
            ]
            filtered_history = [
                e for e in filtered_history 
                if e["type"] in event_type_names
            ]
            
        if actor:
            filtered_history = [
                e for e in filtered_history 
                if e["actor"] == actor
            ]
            
        if game_id:
            filtered_history = [
                e for e in filtered_history 
                if e.get("game_id") == game_id
            ]
            
        if tags:
            filtered_history = [
                e for e in filtered_history 
                if any(tag in e.get("tags", []) for tag in tags)
            ]
            
        if limit and limit > 0:
            filtered_history = filtered_history[-limit:]
            
        return filtered_history
    
    def get_summary(self, 
                   event_types: Optional[List[Union[EventType, str]]] = None,
                   actor: Optional[str] = None,
                   game_id: Optional[str] = None,
                   limit: int = 10) -> str:
        """
        Get a narrative summary of recent events.
        
        Args:
            event_types: Optional filter for event types
            actor: Optional filter for actor
            game_id: Optional filter for game ID
            limit: Maximum number of events to include
            
        Returns:
            A narrative summary of the events
        """
        events = self.get_history(event_types, actor, game_id, limit=limit)
        
        if not events:
            return "No notable events have occurred."
        
        # Create a narrative summary
        summary_lines = []
        for event in events:
            # Convert timestamp to relative time (like "2 hours ago")
            timestamp = datetime.fromisoformat(event["timestamp"])
            now = datetime.utcnow()
            delta = now - timestamp
            
            if delta.days > 0:
                time_str = f"{delta.days} days ago"
            elif delta.seconds > 3600:
                time_str = f"{delta.seconds // 3600} hours ago"
            elif delta.seconds > 60:
                time_str = f"{delta.seconds // 60} minutes ago"
            else:
                time_str = "moments ago"
                
            # Create a summary line
            type_str = event["type"]
            actor_str = event["actor"]
            
            if "context" in event:
                context_items = []
                for key, value in event["context"].items():
                    if key in ["location", "target", "result", "amount"]:
                        context_items.append(f"{key}={value}")
                
                context_str = ", ".join(context_items)
                if context_str:
                    summary_line = f"{time_str}: {actor_str} {type_str} ({context_str})"
                else:
                    summary_line = f"{time_str}: {actor_str} {type_str}"
            else:
                summary_line = f"{time_str}: {actor_str} {type_str}"
                
            summary_lines.append(summary_line)
        
        return "\n".join(summary_lines)
    
    def load_from_file(self, game_id: Optional[str] = None) -> int:
        """
        Load events from a log file into memory.
        
        Args:
            game_id: Optional game ID to load
            
        Returns:
            Number of events loaded
        """
        if game_id:
            log_file = os.path.join(self.log_dir, f"game_{game_id}.jsonl")
        else:
            log_file = os.path.join(self.log_dir, "events.jsonl")
            
        if not os.path.exists(log_file):
            return 0
            
        loaded_events = []
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        loaded_events.append(json.loads(line))
        except Exception as e:
            print(f"Error loading events from log file: {e}")
            return 0
            
        # Replace current history with loaded events (up to max_history)
        if len(loaded_events) > self.max_history:
            self.history = loaded_events[-self.max_history:]
        else:
            self.history = loaded_events
            
        return len(loaded_events)
    
    def clear(self) -> None:
        """Clear all event history in memory."""
        self.history = []


class GameEventBus:
    """
    Event bus for game events using a publish-subscribe pattern.
    
    Attributes:
        subscribers: Dictionary mapping event types to callbacks
        logger: Logger for events published to the bus
    """
    def __init__(self, 
                max_history: int = 1000, 
                log_to_file: bool = True,
                log_dir: str = "logs/events"):
        """
        Initialize a new game event bus.
        
        Args:
            max_history: Maximum number of events to keep in memory
            log_to_file: Whether to log events to a file
            log_dir: Directory for log files
        """
        self.subscribers = defaultdict(list)
        self.logger = EventLogger(max_history, log_to_file, log_dir)
        
        # Set of event types to explicitly not log (for high-frequency events)
        self.excluded_from_logging: Set[EventType] = set()

    def subscribe(self, 
                 event_type: Union[EventType, str], 
                 callback: Callable[[GameEvent], None]) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The event type to subscribe to (EventType enum or string)
            callback: The callback to invoke when an event of this type is published
        """
        # Convert string event types to enum if possible
        if isinstance(event_type, str):
            try:
                event_type = EventType.from_string(event_type)
            except ValueError:
                # Keep as string for custom event types
                pass
                
        self.subscribers[event_type].append(callback)
        
    def unsubscribe(self, 
                   event_type: Union[EventType, str], 
                   callback: Callable[[GameEvent], None]) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: The event type to unsubscribe from
            callback: The callback to remove
            
        Returns:
            True if the callback was removed, False otherwise
        """
        # Convert string event types to enum if possible
        if isinstance(event_type, str):
            try:
                event_type = EventType.from_string(event_type)
            except ValueError:
                # Keep as string for custom event types
                pass
                
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            return True
        return False
        
    def exclude_from_logging(self, event_type: EventType) -> None:
        """
        Exclude an event type from logging.
        
        Args:
            event_type: The event type to exclude from logging
        """
        self.excluded_from_logging.add(event_type)
        
    def include_in_logging(self, event_type: EventType) -> None:
        """
        Include an event type in logging (reverses exclude_from_logging).
        
        Args:
            event_type: The event type to include in logging
        """
        if event_type in self.excluded_from_logging:
            self.excluded_from_logging.remove(event_type)

    def publish(self, event: GameEvent) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
        """
        # Log the event if it's not excluded
        if not (isinstance(event.type, EventType) and event.type in self.excluded_from_logging):
            self.logger.log(event)
        
        # Get actual type for lookup
        event_type = event.type
        
        # Notify type-specific subscribers
        for callback in self.subscribers[event_type]:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in event subscriber: {e}")
                
        # Notify wildcard subscribers if we have any
        wildcard = EventType.WILDCARD if isinstance(event_type, EventType) else "*"
        for callback in self.subscribers[wildcard]:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in wildcard event subscriber: {e}")
                
    def get_history(self, 
                    event_types: Optional[List[Union[EventType, str]]] = None, 
                    actor: Optional[str] = None,
                    game_id: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get filtered event history.
        
        Args:
            event_types: Optional filter for event types
            actor: Optional filter for actor
            game_id: Optional filter for game ID
            tags: Optional filter for tags
            limit: Optional limit on number of events returned
            
        Returns:
            Filtered list of events from the logger
        """
        return self.logger.get_history(event_types, actor, game_id, tags, limit)
    
    def get_summary(self, 
                   event_types: Optional[List[Union[EventType, str]]] = None,
                   actor: Optional[str] = None,
                   game_id: Optional[str] = None,
                   limit: int = 10) -> str:
        """
        Get a narrative summary of recent events.
        
        Args:
            event_types: Optional filter for event types
            actor: Optional filter for actor
            game_id: Optional filter for game ID
            limit: Maximum number of events to include
            
        Returns:
            A narrative summary of the events
        """
        return self.logger.get_summary(event_types, actor, game_id, limit)
    
    def load_history(self, game_id: Optional[str] = None) -> int:
        """
        Load event history from file.
        
        Args:
            game_id: Optional game ID to load
            
        Returns:
            Number of events loaded
        """
        return self.logger.load_from_file(game_id)


# Global event bus instance
event_bus = GameEventBus()