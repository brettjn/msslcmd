#!/usr/bin/env python3
"""
Missile Command Clone
A classic arcade game where you defend cities from incoming missiles.
"""

import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# Game settings
ENEMY_MISSILE_SPEED = 1.5
PLAYER_MISSILE_SPEED = 5
EXPLOSION_MAX_RADIUS = 60
EXPLOSION_GROWTH_RATE = 2
EXPLOSION_DURATION = 45  # frames


class Explosion:
    """Represents an explosion that can destroy enemy missiles"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 0
        self.max_radius = EXPLOSION_MAX_RADIUS
        self.growing = True
        self.timer = EXPLOSION_DURATION
        
    def update(self):
        """Update explosion animation"""
        if self.growing:
            self.radius += EXPLOSION_GROWTH_RATE
            if self.radius >= self.max_radius:
                self.growing = False
        
        self.timer -= 1
        return self.timer > 0  # Return True if explosion is still active
    
    def draw(self, screen):
        """Draw the explosion"""
        if self.radius > 0:
            # Draw multiple circles for better effect
            pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), int(self.radius), 2)
            pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), int(self.radius * 0.7), 2)
            pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), int(self.radius * 0.4), 2)
    
    def collides_with(self, x, y):
        """Check if a point is within the explosion radius"""
        distance = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        return distance <= self.radius


class Missile:
    """Base class for missiles"""
    def __init__(self, start_x, start_y, target_x, target_y, speed, color):
        self.x = start_x
        self.y = start_y
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = speed
        self.color = color
        self.active = True
        
        # Calculate direction
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        
        if distance > 0:
            self.velocity_x = (dx / distance) * speed
            self.velocity_y = (dy / distance) * speed
        else:
            self.velocity_x = 0
            self.velocity_y = 0
    
    def update(self):
        """Update missile position"""
        self.x += self.velocity_x
        self.y += self.velocity_y
    
    def draw(self, screen):
        """Draw the missile and its trail"""
        if self.active:
            # Draw trail
            pygame.draw.line(screen, self.color, (int(self.start_x), int(self.start_y)), 
                           (int(self.x), int(self.y)), 1)
            # Draw missile head
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 2)
    
    def has_reached_target(self):
        """Check if missile has reached its target"""
        distance = math.sqrt((self.x - self.target_x) ** 2 + (self.y - self.target_y) ** 2)
        return distance < self.speed


class PlayerMissile(Missile):
    """Player-controlled missile"""
    def __init__(self, start_x, start_y, target_x, target_y):
        super().__init__(start_x, start_y, target_x, target_y, PLAYER_MISSILE_SPEED, CYAN)


class EnemyMissile(Missile):
    """Enemy missile targeting cities or bases"""
    def __init__(self, start_x, target_x, target_y, color=RED):
        super().__init__(start_x, 0, target_x, target_y, ENEMY_MISSILE_SPEED, color)


class MissileBase:
    """Represents a missile base that can fire missiles"""
    def __init__(self, x, y, side):
        self.x = x
        self.y = y
        self.side = side  # 'left', 'center', or 'right'
        self.active = True
        self.ammo = 10
    
    def draw(self, screen):
        """Draw the missile base"""
        if self.active:
            # Draw base as a triangle
            points = [
                (self.x, self.y),
                (self.x - 15, self.y + 20),
                (self.x + 15, self.y + 20)
            ]
            pygame.draw.polygon(screen, GREEN, points)
            
            # Draw ammo count
            font = pygame.font.Font(None, 20)
            text = font.render(str(self.ammo), True, WHITE)
            screen.blit(text, (self.x - 10, self.y + 25))
        else:
            # Draw destroyed base
            pygame.draw.circle(screen, RED, (self.x, self.y + 10), 15)
    
    def fire(self, target_x, target_y):
        """Fire a missile if ammo is available"""
        if self.active and self.ammo > 0:
            self.ammo -= 1
            return PlayerMissile(self.x, self.y, target_x, target_y)
        return None


class City:
    """Represents a city to defend"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = True
        self.color = BLUE
    
    def draw(self, screen):
        """Draw the city"""
        if self.active:
            # Draw city as simple buildings
            pygame.draw.rect(screen, self.color, (self.x - 10, self.y, 8, 15))
            pygame.draw.rect(screen, self.color, (self.x, self.y + 5, 8, 10))
            pygame.draw.rect(screen, self.color, (self.x + 10, self.y + 2, 6, 13))
        else:
            # Draw destroyed city
            pygame.draw.line(screen, RED, (self.x - 15, self.y + 15), (self.x + 15, self.y + 15), 2)


class Game:
    """Main game class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Missile Command")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        
        self.score = 0
        self.level = 1
        self.enemy_spawn_timer = 0
        self.enemy_spawn_rate = 60  # frames between spawns
        self.starting_ammo = 10
        self.missiles_spawned_this_level = 0
        self.enemy_missile_color = RED
        self.flash_timer = 0
        self.flash_color = WHITE
        
        # Initialize game objects
        self.setup_game()
        
        # Set missiles per level based on total ammo
        self.missiles_per_level = sum(base.ammo for base in self.bases)
    
    def randomize_colors(self):
        """Randomize enemy missile and city colors"""
        # Generate random enemy missile color (avoid too dark)
        self.enemy_missile_color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        
        # Generate random city colors
        for city in self.cities:
            if city.active:
                city.color = (
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255)
                )
    
    def setup_game(self):
        """Setup or reset the game"""
        # Create missile bases
        self.bases = [
            MissileBase(100, SCREEN_HEIGHT - 40, 'left'),
            MissileBase(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40, 'center'),
            MissileBase(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 40, 'right')
        ]
        
        # Set starting ammo
        for base in self.bases:
            base.ammo = self.starting_ammo
        
        # Create cities
        self.cities = [
            City(200, SCREEN_HEIGHT - 35),
            City(250, SCREEN_HEIGHT - 35),
            City(300, SCREEN_HEIGHT - 35),
            City(SCREEN_WIDTH - 300, SCREEN_HEIGHT - 35),
            City(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 35),
            City(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 35)
        ]
        
        self.player_missiles = []
        self.enemy_missiles = []
        self.explosions = []
    
    def spawn_enemy_missile(self):
        """Spawn an enemy missile targeting a random city or base"""
        start_x = random.randint(50, SCREEN_WIDTH - 50)
        
        # Choose a target
        possible_targets = []
        
        # Add active cities as targets
        for city in self.cities:
            if city.active:
                possible_targets.append((city.x, city.y))
        
        # Add active bases as targets
        for base in self.bases:
            if base.active:
                possible_targets.append((base.x, base.y))
        
        if possible_targets:
            target_x, target_y = random.choice(possible_targets)
            self.enemy_missiles.append(EnemyMissile(start_x, target_x, target_y, self.enemy_missile_color))
            self.missiles_spawned_this_level += 1
    
    def handle_events(self):
        """Handle user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                if event.button == 1:  # Left mouse button - fire from left base
                    missile = self.bases[0].fire(mouse_x, mouse_y)
                    if missile:
                        self.player_missiles.append(missile)
                
                elif event.button == 2:  # Middle mouse button - fire from center base
                    missile = self.bases[1].fire(mouse_x, mouse_y)
                    if missile:
                        self.player_missiles.append(missile)
                
                elif event.button == 3:  # Right mouse button - fire from right base
                    missile = self.bases[2].fire(mouse_x, mouse_y)
                    if missile:
                        self.player_missiles.append(missile)
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.game_over:
                    # Restart game
                    self.game_over = False
                    self.score = 0
                    self.level = 1
                    self.setup_game()
    
    def update(self):
        """Update game state"""
        if self.game_over:
            return
        
        # Update flash timer
        if self.flash_timer > 0:
            self.flash_timer -= 1
        
        # Spawn enemy missiles (only if we haven't reached the limit for this level)
        self.enemy_spawn_timer += 1
        
        if (self.enemy_spawn_timer >= self.enemy_spawn_rate and 
            self.missiles_spawned_this_level < self.missiles_per_level):
            self.spawn_enemy_missile()
            self.enemy_spawn_timer = 0
        
        # Update player missiles
        for missile in self.player_missiles[:]:
            missile.update()
            
            # Check if missile reached target
            if missile.has_reached_target():
                self.explosions.append(Explosion(missile.target_x, missile.target_y))
                self.player_missiles.remove(missile)
            
            # Remove missiles that go off screen
            elif missile.y < 0 or missile.x < 0 or missile.x > SCREEN_WIDTH:
                self.player_missiles.remove(missile)
        
        # Update enemy missiles
        for missile in self.enemy_missiles[:]:
            missile.update()
            
            # Check collision with explosions
            destroyed = False
            for explosion in self.explosions:
                if explosion.collides_with(missile.x, missile.y):
                    self.enemy_missiles.remove(missile)
                    self.score += 25
                    destroyed = True
                    break
            
            # Check if missile hit ground
            if not destroyed and missile.y >= SCREEN_HEIGHT - 50:
                self.enemy_missiles.remove(missile)
                
                # Check if it hit a city
                for city in self.cities:
                    if city.active and abs(city.x - missile.x) < 20:
                        city.active = False
                        self.explosions.append(Explosion(city.x, city.y))
                        break
                
                # Check if it hit a base
                for base in self.bases:
                    if base.active and abs(base.x - missile.x) < 20:
                        base.active = False
                        self.explosions.append(Explosion(base.x, base.y))
                        break
        
        # Update explosions
        for explosion in self.explosions[:]:
            if not explosion.update():
                self.explosions.remove(explosion)
        
        # Check game over conditions
        all_cities_destroyed = all(not city.active for city in self.cities)
        
        if all_cities_destroyed:
            self.game_over = True
        
        # Check for level completion (all missiles spawned and cleared)
        any_city_alive = any(city.active for city in self.cities)
        if (len(self.enemy_missiles) == 0 and 
            self.missiles_spawned_this_level >= self.missiles_per_level and
            any_city_alive):
            
            # Bonus for remaining cities and bases
            for city in self.cities:
                if city.active:
                    self.score += 100
            
            # Regenerate and refill all bases
            for base in self.bases:
                base.active = True  # Regenerate destroyed bases
                base.ammo = self.starting_ammo
                if base.active:
                    self.score += 50
            
            # Calculate missiles for next level based on total ammo
            self.missiles_per_level = sum(base.ammo for base in self.bases)
            
            # Flash effect
            self.flash_timer = 20
            self.flash_color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            
            # Randomize colors for next level
            self.randomize_colors()
            
            # Next level
            self.level += 1
            self.enemy_spawn_rate = max(30, self.enemy_spawn_rate - 5)
            self.enemy_spawn_timer = 0
            self.missiles_spawned_this_level = 0
    
    def draw(self):
        """Draw everything"""
        # Apply flash effect if active
        if self.flash_timer > 0:
            flash_intensity = int((self.flash_timer / 20) * 100)
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surface.fill(self.flash_color)
            flash_surface.set_alpha(flash_intensity)
            self.screen.fill(BLACK)
            self.screen.blit(flash_surface, (0, 0))
        else:
            self.screen.fill(BLACK)
        
        # Draw ground line
        pygame.draw.line(self.screen, WHITE, (0, SCREEN_HEIGHT - 50), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT - 50), 2)
        
        # Draw cities
        for city in self.cities:
            city.draw(self.screen)
        
        # Draw bases
        for base in self.bases:
            base.draw(self.screen)
        
        # Draw missiles
        for missile in self.enemy_missiles:
            missile.draw(self.screen)
        
        for missile in self.player_missiles:
            missile.draw(self.screen)
        
        # Draw explosions
        for explosion in self.explosions:
            explosion.draw(self.screen)
        
        # Draw crosshair at mouse position
        if not self.game_over:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            pygame.draw.line(self.screen, GREEN, (mouse_x - 10, mouse_y), 
                           (mouse_x + 10, mouse_y), 1)
            pygame.draw.line(self.screen, GREEN, (mouse_x, mouse_y - 10), 
                           (mouse_x, mouse_y + 10), 1)
            pygame.draw.circle(self.screen, GREEN, (mouse_x, mouse_y), 15, 1)
        
        # Draw UI
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        level_text = font.render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(level_text, (SCREEN_WIDTH - 150, 10))
        
        # Draw game over message
        if self.game_over:
            game_over_font = pygame.font.Font(None, 72)
            game_over_text = game_over_font.render("GAME OVER", True, RED)
            restart_font = pygame.font.Font(None, 36)
            restart_text = restart_font.render("Press SPACE to restart", True, WHITE)
            
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            
            self.screen.blit(game_over_text, text_rect)
            self.screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
