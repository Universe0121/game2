import pygame

from config import settings


def draw_panel(surface, rect, selected=False):
    color = settings.PANEL_LIGHT if selected else settings.PANEL
    border = settings.GOLD if selected else settings.GRAY
    pygame.draw.rect(surface, color, rect, border_radius=6)
    pygame.draw.rect(surface, border, rect, 2, border_radius=6)


def draw_bar(surface, rect, ratio, fill_color, border_color=settings.WHITE):
    ratio = max(0, min(1, ratio))
    pygame.draw.rect(surface, settings.PANEL, rect, border_radius=5)
    fill_rect = rect.copy()
    fill_rect.width = int(rect.width * ratio)
    if fill_rect.width > 0:
        pygame.draw.rect(surface, fill_color, fill_rect, border_radius=5)
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=5)
