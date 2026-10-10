"""
Base UI components.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class UIComponent:
    """Base UI component."""
    id: str
    type: str
    props: Dict[str, Any]
    children: List['UIComponent']


class ComponentRegistry:
    """Registry for UI components."""
    
    def __init__(self):
        self.components: Dict[str, UIComponent] = {}
    
    def register(self, component: UIComponent):
        """Register a component."""
        self.components[component.id] = component
    
    def get(self, component_id: str) -> Optional[UIComponent]:
        """Get component by ID."""
        return self.components.get(component_id)
    
    def render(self, component_id: str) -> str:
        """Render component to HTML."""
        component = self.get(component_id)
        if not component:
            return ""
        return f"<{component.type}>{component.id}</{component.type}>"


class ThemeManager:
    """Manages UI themes."""
    
    def __init__(self):
        self.themes: Dict[str, Dict[str, str]] = {
            "light": {"bg": "#ffffff", "text": "#000000", "primary": "#007bff"},
            "dark": {"bg": "#1a1a1a", "text": "#ffffff", "primary": "#4dabf7"}
        }
        self.current_theme = "light"
    
    def get_theme(self) -> Dict[str, str]:
        """Get current theme colors."""
        return self.themes.get(self.current_theme, self.themes["light"])
    
    def set_theme(self, theme_name: str):
        """Set current theme."""
        if theme_name in self.themes:
            self.current_theme = theme_name