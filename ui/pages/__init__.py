"""UI page renderers package."""

from ui.pages.landing import render_landing_page
from ui.pages.overview import render_overview
from ui.pages.practice import render_practice, show_result
from ui.pages.skills_cv import render_skills_cv
from ui.pages.roadmap import render_roadmap
from ui.pages.history import render_history
from ui.pages.model_lab import render_model_lab

__all__ = [
    "render_landing_page",
    "render_overview",
    "render_practice",
    "show_result",
    "render_skills_cv",
    "render_roadmap",
    "render_history",
    "render_model_lab",
]
