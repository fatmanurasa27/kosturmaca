# -*- coding: utf-8 -*-
import pygame
import sys
import math
import random
import json
import os

# Pygame'i başlat
pygame.init()

# Ekran boyutları ve FPS
WIDTH, HEIGHT = 800, 600
FPS = 60

# Renkler
BG_COLOR = (170, 220, 150)
MONSTER_COLOR = (231, 76, 60)
TEXT_COLOR = (44, 62, 80)

# Oyuncu Renk Seçenekleri
PLAYER_COLORS = [
    (41, 128, 185),   # Mavi
    (192, 57, 43),    # Kırmızı
    (39, 174, 96),    # Yeşil
    (241, 196, 15),   # Sarı
    (142, 68, 173)    # Mor
]
PLAYER_COLOR_NAMES = ["Mavi", "Kırmızı", "Yeşil", "Sarı", "Mor"]

SCORES_FILE = "scores.json"

def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_scores(scores):
    try:
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=4)
    except:
        pass

# Ekran kurulumu
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Koşturmaca")
clock = pygame.time.Clock()

# Fontlar
try:
    font_large = pygame.font.SysFont("comicsansms", 64, bold=True)
    font_small = pygame.font.SysFont("comicsansms", 32)
except:
    font_large = pygame.font.Font(None, 64)
    font_small = pygame.font.Font(None, 32)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.radius = random.uniform(3, 6)
        self.color = color
        self.life = 255
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(0, 2)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 15
        self.radius -= 0.1

    def draw(self, surface):
        if self.life > 0 and self.radius > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius))

class PowerUp:
    def __init__(self):
        self.x = random.randint(50, WIDTH - 50)
        self.y = random.randint(100, HEIGHT - 100)
        self.radius = 12
        self.active = True
        self.anim_offset = 0

    def draw(self, surface):
        if not self.active: return
        self.anim_offset += 0.1
        oy = math.sin(self.anim_offset) * 5
        
        # Altın sarısı dış çember
        pygame.draw.circle(surface, (255, 215, 0), (int(self.x), int(self.y + oy)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y + oy)), self.radius, 2)
        
        # Şimşek ikonu
        points = [
            (self.x, self.y + oy - 6),
            (self.x - 4, self.y + oy),
            (self.x, self.y + oy),
            (self.x - 2, self.y + oy + 6),
            (self.x + 4, self.y + oy - 1),
            (self.x, self.y + oy - 1)
        ]
        pygame.draw.polygon(surface, (0, 0, 0), points)

class Player:
    def __init__(self, x, y, color=(41, 128, 185)):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.base_speed = 5.0
        self.speed = self.base_speed
        self.radius = 15
        self.is_moving = False
        self.anim_counter = 0
        self.rect = pygame.Rect(0, 0, 30, 60)
        self.update_rect()
        self.boost_timer = 0
        self.particles = []

    def update_rect(self):
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y) + 15

    def move(self, keys, target_pos=None):
        self.is_moving = False
        
        if self.boost_timer > 0:
            self.boost_timer -= 1
            self.speed = self.base_speed * 1.6
        else:
            self.speed = self.base_speed
        
        if target_pos:
            tx, ty = target_pos
            dx = tx - self.x
            dy = ty - self.y
            dist = math.hypot(dx, dy)
            if dist > self.speed:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
                self.is_moving = True
            else:
                self.x = tx
                self.y = ty
                self.is_moving = False
                
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
            self.is_moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
            self.is_moving = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
            self.is_moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
            self.is_moving = True

        if self.is_moving:
            self.anim_counter += 0.3
            if random.random() < 0.4:
                # Ayak hizasından toz çıkar
                p_color = (255, 215, 0) if self.boost_timer > 0 else (200, 200, 200)
                self.particles.append(Particle(self.x, self.y + 45, p_color))
        else:
            self.anim_counter = 0

        # Partikülleri güncelle
        for p in self.particles[:]:
            p.update()
            if p.life <= 0 or p.radius <= 0:
                self.particles.remove(p)

        self.x = max(15, min(WIDTH - 15, self.x))
        self.y = max(5, min(HEIGHT - 45, self.y))
        
        self.update_rect()

    def draw(self, surface, is_scared=False, is_dead=False):
        # Partikülleri karakterin arkasında çiz
        for p in self.particles:
            p.draw(surface)
            
        if is_dead:
            temp_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
            ix, iy = 60, 40
            self._draw_character(temp_surf, ix, iy, is_scared)
            rotated_surf = pygame.transform.rotate(temp_surf, -90)
            rect = rotated_surf.get_rect(center=(int(self.x), int(self.y) + 20))
            surface.blit(rotated_surf, rect)
        else:
            ix, iy = int(self.x), int(self.y)
            self._draw_character(surface, ix, iy, is_scared)

    def _draw_character(self, surface, ix, iy, is_scared):
        # Kafa
        pygame.draw.circle(surface, (255, 228, 196), (ix, iy), self.radius)
        pygame.draw.circle(surface, self.color, (ix, iy), self.radius, 4)
        
        # Yüz
        if is_scared:
            pygame.draw.circle(surface, (0, 0, 0), (ix - 5, iy - 3), 4)
            pygame.draw.circle(surface, (0, 0, 0), (ix + 5, iy - 3), 4)
            pygame.draw.line(surface, (0, 0, 0), (ix - 9, iy - 10), (ix - 3, iy - 7), 2)
            pygame.draw.line(surface, (0, 0, 0), (ix + 9, iy - 10), (ix + 3, iy - 7), 2)
            pygame.draw.circle(surface, (0, 0, 0), (ix, iy + 6), 4)
        else:
            pygame.draw.circle(surface, (0, 0, 0), (ix - 5, iy - 3), 2)
            pygame.draw.circle(surface, (0, 0, 0), (ix + 5, iy - 3), 2)
            pygame.draw.line(surface, (0, 0, 0), (ix - 8, iy - 7), (ix - 2, iy - 7), 2)
            pygame.draw.line(surface, (0, 0, 0), (ix + 8, iy - 7), (ix + 2, iy - 7), 2)
            pygame.draw.arc(surface, (0, 0, 0), (ix - 6, iy, 12, 8), math.pi, 2 * math.pi, 2)

        # Gövde (Daha kalın)
        pygame.draw.line(surface, self.color, (ix, iy + self.radius), (ix, iy + self.radius + 25), 8)
        
        swing = math.sin(self.anim_counter) * 15
        
        # Kollar & Bacaklar (Daha kalın)
        pygame.draw.line(surface, self.color, (ix, iy + self.radius + 5), (ix - 15 + swing, iy + self.radius + 20), 8)
        pygame.draw.line(surface, self.color, (ix, iy + self.radius + 5), (ix + 15 - swing, iy + self.radius + 20), 8)
        pygame.draw.line(surface, self.color, (ix, iy + self.radius + 25), (ix - 15 - swing, iy + self.radius + 50), 8)
        pygame.draw.line(surface, self.color, (ix, iy + self.radius + 25), (ix + 15 + swing, iy + self.radius + 50), 8)

class Monster:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.base_speed = 2.5
        self.speed = self.base_speed
        self.size = 46
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.update_rect()

    def update_rect(self):
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

    def chase(self, target_x, target_y, time_survived):
        self.speed = self.base_speed + (time_survived * 0.1)
        
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        if dist != 0:
            dx /= dist
            dy /= dist
        
        self.x += dx * self.speed
        self.y += dy * self.speed
        
        self.update_rect()

    def draw(self, surface, bg_index=0):
        ix, iy = int(self.x), int(self.y)
        half = self.size // 2
        
        themes = [
            MONSTER_COLOR,               # 0: Bahçe (Kırmızı)
            (211, 84, 0),                # 1: Çöl (Turuncu)
            (142, 68, 173),              # 2: Uzay (Mor)
            (52, 152, 219),              # 3: Kış (Buz Mavisi)
            (44, 62, 80),                # 4: Volkan (Koyu Gri)
            (46, 204, 113)               # 5: Siberpunk (Neon Yeşil)
        ]
        color = themes[bg_index % len(themes)]
        
        # Tematik Şekiller
        if bg_index == 1:
            pygame.draw.polygon(surface, color, [(ix, iy - half - 10), (ix + half, iy), (ix, iy + half + 10), (ix - half, iy)])
        elif bg_index == 2:
            pygame.draw.circle(surface, color, (ix, iy), half)
            pygame.draw.circle(surface, color, (ix - half, iy + half), 10)
            pygame.draw.circle(surface, color, (ix + half, iy + half), 10)
        elif bg_index == 3:
            pygame.draw.rect(surface, color, (ix - half, iy - half, self.size, self.size))
            pygame.draw.rect(surface, (255,255,255), (ix - half, iy - half, self.size, self.size), 3)
        elif bg_index == 4:
            pygame.draw.rect(surface, color, (ix - half, iy - half, self.size, self.size), border_radius=5)
            pygame.draw.line(surface, (231, 76, 60), (ix - half, iy), (ix + half, iy), 2)
            pygame.draw.line(surface, (231, 76, 60), (ix, iy - half), (ix, iy + half), 2)
        elif bg_index == 5:
            pygame.draw.rect(surface, (20, 20, 20), (ix - half, iy - half, self.size, self.size))
            pygame.draw.rect(surface, color, (ix - half, iy - half, self.size, self.size), 4)
        else:
            pygame.draw.rect(surface, color, (ix - half, iy - half, self.size, self.size), border_radius=10)
        
        eye_color = (255, 255, 255) if bg_index != 4 else (231, 76, 60)
        pupil_color = (0, 0, 0)
        
        # Gözler
        pygame.draw.circle(surface, eye_color, (ix - 10, iy - 8), 7)
        pygame.draw.circle(surface, pupil_color, (ix - 10, iy - 8), 3)
        pygame.draw.line(surface, pupil_color, (ix - 18, iy - 16), (ix - 2, iy - 6), 3)
        
        pygame.draw.circle(surface, eye_color, (ix + 10, iy - 8), 7)
        pygame.draw.circle(surface, pupil_color, (ix + 10, iy - 8), 3)
        pygame.draw.line(surface, pupil_color, (ix + 2, iy - 6), (ix + 18, iy - 16), 3)

        # Ağız
        is_mouth_open = (pygame.time.get_ticks() // 200) % 2 == 0
        mouth_y = iy + 8
        mouth_w = 24
        start_x = ix - mouth_w // 2
        
        if is_mouth_open:
            pygame.draw.rect(surface, (0, 0, 0), (start_x, mouth_y, mouth_w, 14))
            for i in range(4):
                tx = start_x + (i * 6)
                pygame.draw.polygon(surface, (255, 255, 255), [(tx, mouth_y), (tx + 3, mouth_y + 5), (tx + 6, mouth_y)])
            for i in range(4):
                tx = start_x + (i * 6)
                pygame.draw.polygon(surface, (255, 255, 255), [(tx, mouth_y + 14), (tx + 3, mouth_y + 9), (tx + 6, mouth_y + 14)])
        else:
            pygame.draw.line(surface, (0, 0, 0), (start_x, mouth_y), (start_x + mouth_w, mouth_y), 2)
            for i in range(4):
                tx = start_x + (i * 6)
                points = [(tx, mouth_y), (tx + 3, mouth_y + 8), (tx + 6, mouth_y)]
                pygame.draw.polygon(surface, (255, 255, 255), points)
                pygame.draw.polygon(surface, (0, 0, 0), points, 1)

def main():
    scores_dict = load_scores()
    player_name = ""
    
    bg_images = []
    bg_names = ["Bahçe", "Çöl", "Uzay", "Kış", "Volkan", "Siberpunk"]
    img_files = ["bg_garden.png", "bg_desert.png", "bg_space.png", "bg_snow.png", "bg_lava.png", "bg_cyber.png"]
    
    for img_name in img_files:
        try:
            img = pygame.image.load(img_name).convert()
            img = pygame.transform.scale(img, (WIDTH, HEIGHT))
            bg_images.append(img)
        except:
            img = pygame.Surface((WIDTH, HEIGHT))
            img.fill(BG_COLOR)
            bg_images.append(img)

    bg_index = 0
    p_color_index = 0

    player = Player(WIDTH // 2, HEIGHT // 2, PLAYER_COLORS[p_color_index])
    monster = Monster(50, 50)
    
    start_ticks = 0
    state = "NAME_INPUT"
    score = 0
    target_pos = None
    transition_y = 0
    next_bg_index = 0
    
    powerup = None
    powerup_spawn_timer = 0

    # Dokunmatik UI alanları
    ok_btn_rect = pygame.Rect(WIDTH//2 - 60, HEIGHT//2 + 100, 120, 40)
    bg_prev_rect = pygame.Rect(WIDTH//2 - 180, HEIGHT//2 - 65, 40, 40)
    bg_next_rect = pygame.Rect(WIDTH//2 + 140, HEIGHT//2 - 65, 40, 40)
    col_prev_rect = pygame.Rect(WIDTH//2 - 180, HEIGHT//2 - 15, 40, 40)
    col_next_rect = pygame.Rect(WIDTH//2 + 140, HEIGHT//2 - 15, 40, 40)
    start_btn_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 40, 200, 50)
    
    while True:
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if state == "NAME_INPUT":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        if len(player_name.strip()) > 0:
                            player_name = player_name.strip()
                        else:
                            player_name = "Oyuncu"
                        state = "MENU"
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    else:
                        if len(player_name) < 15 and event.unicode.isprintable():
                            player_name += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if ok_btn_rect.collidepoint(event.pos):
                        if len(player_name.strip()) > 0:
                            player_name = player_name.strip()
                        else:
                            player_name = "Oyuncu"
                        state = "MENU"

            elif state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        bg_index = (bg_index - 1) % len(bg_images)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        bg_index = (bg_index + 1) % len(bg_images)
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        p_color_index = (p_color_index - 1) % len(PLAYER_COLORS)
                        player.color = PLAYER_COLORS[p_color_index]
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        p_color_index = (p_color_index + 1) % len(PLAYER_COLORS)
                        player.color = PLAYER_COLORS[p_color_index]
                    elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        state = "PLAYING"
                        start_ticks = pygame.time.get_ticks()
                        powerup = None
                        powerup_spawn_timer = 0
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if bg_prev_rect.collidepoint((mx, my)):
                        bg_index = (bg_index - 1) % len(bg_images)
                    elif bg_next_rect.collidepoint((mx, my)):
                        bg_index = (bg_index + 1) % len(bg_images)
                    elif col_prev_rect.collidepoint((mx, my)):
                        p_color_index = (p_color_index - 1) % len(PLAYER_COLORS)
                        player.color = PLAYER_COLORS[p_color_index]
                    elif col_next_rect.collidepoint((mx, my)):
                        p_color_index = (p_color_index + 1) % len(PLAYER_COLORS)
                        player.color = PLAYER_COLORS[p_color_index]
                    elif start_btn_rect.collidepoint((mx, my)):
                        state = "PLAYING"
                        start_ticks = pygame.time.get_ticks()
                        powerup = None
                        powerup_spawn_timer = 0

            elif state == "PLAYING":
                if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.MOUSEMOTION and event.buttons[0]):
                    target_pos = event.pos
                if event.type == pygame.MOUSEBUTTONUP:
                    target_pos = None
                
            elif state == "GAME_OVER":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    state = "MENU"
                    player = Player(WIDTH // 2, HEIGHT // 2, PLAYER_COLORS[p_color_index])
                    monster = Monster(50, 50)
                    target_pos = None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    state = "MENU"
                    player = Player(WIDTH // 2, HEIGHT // 2, PLAYER_COLORS[p_color_index])
                    monster = Monster(50, 50)
                    target_pos = None

        if state != "TRANSITION" and state != "NAME_INPUT":
            screen.blit(bg_images[bg_index], (0, 0))

        if state == "NAME_INPUT":
            screen.blit(bg_images[0], (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 200))
            screen.blit(overlay, (0, 0))

            title = font_large.render("Koşturmaca", True, TEXT_COLOR)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))

            prompt = font_small.render("Lütfen İsminizi Girin:", True, TEXT_COLOR)
            screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 - 40))

            # İsim kutusu
            input_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 10, 300, 50)
            pygame.draw.rect(screen, (200, 200, 200), input_rect)
            pygame.draw.rect(screen, TEXT_COLOR, input_rect, 2)
            
            cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
            name_surf = font_small.render(player_name + cursor, True, TEXT_COLOR)
            screen.blit(name_surf, (input_rect.x + 10, input_rect.y + 5))
            
            # TAMAM Butonu (Mobil için)
            pygame.draw.rect(screen, (46, 204, 113), ok_btn_rect, border_radius=10)
            ok_text = font_small.render("TAMAM", True, (255, 255, 255))
            screen.blit(ok_text, (ok_btn_rect.centerx - ok_text.get_width()//2, ok_btn_rect.centery - ok_text.get_height()//2))
            
            info = font_small.render("veya devam etmek için ENTER'a basın", True, (100, 100, 100))
            screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2 + 160))

        elif state == "MENU":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 180))
            screen.blit(overlay, (0, 0))
            
            title_text = font_large.render("Koşturmaca", True, TEXT_COLOR)
            screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//6))
            
            personal_best = scores_dict.get(player_name, 0)
            welcome_text = font_small.render(f"Hoş geldin, {player_name}! (Rekorun: {personal_best})", True, (41, 128, 185))
            screen.blit(welcome_text, (WIDTH//2 - welcome_text.get_width()//2, HEIGHT//6 + 80))
            
            # Tema (Arka Plan) Seçimi Dokunmatik Butonları
            pygame.draw.rect(screen, (200, 200, 200), bg_prev_rect, border_radius=5)
            left_arrow = font_small.render("<", True, (0,0,0))
            screen.blit(left_arrow, (bg_prev_rect.centerx - left_arrow.get_width()//2, bg_prev_rect.centery - left_arrow.get_height()//2))
            
            bg_text = font_small.render(f"Tema: {bg_names[bg_index]}", True, TEXT_COLOR)
            screen.blit(bg_text, (WIDTH//2 - bg_text.get_width()//2, bg_prev_rect.centery - bg_text.get_height()//2))
            
            pygame.draw.rect(screen, (200, 200, 200), bg_next_rect, border_radius=5)
            right_arrow = font_small.render(">", True, (0,0,0))
            screen.blit(right_arrow, (bg_next_rect.centerx - right_arrow.get_width()//2, bg_next_rect.centery - right_arrow.get_height()//2))

            # Renk Seçimi Dokunmatik Butonları
            pygame.draw.rect(screen, (200, 200, 200), col_prev_rect, border_radius=5)
            left_c_arrow = font_small.render("<", True, (0,0,0))
            screen.blit(left_c_arrow, (col_prev_rect.centerx - left_c_arrow.get_width()//2, col_prev_rect.centery - left_c_arrow.get_height()//2))
            
            color_text = font_small.render(f"Renk: {PLAYER_COLOR_NAMES[p_color_index]}", True, PLAYER_COLORS[p_color_index])
            screen.blit(color_text, (WIDTH//2 - color_text.get_width()//2, col_prev_rect.centery - color_text.get_height()//2))
            
            pygame.draw.rect(screen, (200, 200, 200), col_next_rect, border_radius=5)
            right_c_arrow = font_small.render(">", True, (0,0,0))
            screen.blit(right_c_arrow, (col_next_rect.centerx - right_c_arrow.get_width()//2, col_next_rect.centery - right_c_arrow.get_height()//2))

            # Başla Butonu (Dokunmatik)
            pygame.draw.rect(screen, (46, 204, 113), start_btn_rect, border_radius=10)
            start_text = font_small.render("BAŞLA", True, (255, 255, 255))
            screen.blit(start_text, (start_btn_rect.centerx - start_text.get_width()//2, start_btn_rect.centery - start_text.get_height()//2))

            # Karakteri örnek olarak çiz
            player.x, player.y = WIDTH//2, HEIGHT//2 + 100
            player.update_rect()
            player.draw(screen)

            # Liderlik tablosu
            sorted_scores = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)[:3]
            if sorted_scores:
                leader_y = HEIGHT//2 + 160
                lb_title = font_small.render("--- En İyiler ---", True, (231, 76, 60))
                screen.blit(lb_title, (WIDTH//2 - lb_title.get_width()//2, leader_y))
                for i, (name, sc) in enumerate(sorted_scores):
                    lb_text = font_small.render(f"{i+1}. {name}: {sc}", True, TEXT_COLOR)
                    screen.blit(lb_text, (WIDTH//2 - lb_text.get_width()//2, leader_y + 35 + (i * 30)))

        elif state == "PLAYING":
            player.move(keys, target_pos)
            
            if player.y < 10:
                state = "TRANSITION"
                transition_y = 0
                next_bg_index = (bg_index + 1) % len(bg_images)
            else:
                seconds = (pygame.time.get_ticks() - start_ticks) // 1000
                score = seconds
                
                monster.chase(player.x, player.y, score)
                
                # Power-up Mantığı
                powerup_spawn_timer += 1
                if powerup is None and powerup_spawn_timer > FPS * 10:
                    if random.random() < 0.05:
                        powerup = PowerUp()
                        powerup_spawn_timer = 0
                        
                if powerup and powerup.active:
                    dist_to_powerup = math.hypot(player.x - powerup.x, player.y - powerup.y)
                    if dist_to_powerup < player.radius + powerup.radius:
                        powerup.active = False
                        player.boost_timer = FPS * 5
                        powerup = None

                dist_to_monster = math.hypot(player.x - monster.x, player.y - monster.y)
                is_scared = dist_to_monster < 150

                if player.rect.inflate(-10, -10).colliderect(monster.rect.inflate(-10, -10)):
                    state = "GAME_OVER"
                    # Skor Kaydetme Mantığı
                    if score > scores_dict.get(player_name, 0):
                        scores_dict[player_name] = score
                        save_scores(scores_dict)

                player.draw(screen, is_scared=is_scared)
                
                if powerup and powerup.active:
                    powerup.draw(screen)
                    
                monster.draw(screen, bg_index)

                # Skor UI
                score_text_shadow = font_small.render(f"Skor: {score}", True, (100, 150, 100))
                score_text = font_small.render(f"Skor: {score}", True, TEXT_COLOR)
                screen.blit(score_text_shadow, (22, 22))
                screen.blit(score_text, (20, 20))

        elif state == "TRANSITION":
            transition_speed = 15
            transition_y += transition_speed
            
            screen.blit(bg_images[bg_index], (0, transition_y))
            screen.blit(bg_images[next_bg_index], (0, transition_y - HEIGHT))
            
            player.y = (transition_y / HEIGHT) * (HEIGHT - 60) + 10
            player.draw(screen, is_scared=False)
            
            if transition_y >= HEIGHT:
                state = "PLAYING"
                bg_index = next_bg_index
                player.y = HEIGHT - 50
                monster.base_speed += 0.15
                target_pos = None

        elif state == "GAME_OVER":
            player.draw(screen, is_scared=True, is_dead=True)
            monster.draw(screen, bg_index)
            
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 180))
            screen.blit(overlay, (0, 0))

            game_over_text = font_large.render("Oyun Bitti", True, (200, 50, 50))
            
            if score >= scores_dict.get(player_name, 0) and score > 0:
                score_info = font_small.render(f"YENİ REKOR! Skor: {score} saniye", True, (46, 204, 113))
            else:
                score_info = font_small.render(f"Hayatta kalınan süre: {score} saniye", True, TEXT_COLOR)
                
            restart_text = font_small.render("Menüye dönmek için ekrana dokun / SPACE", True, TEXT_COLOR)
            
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 100))
            screen.blit(score_info, (WIDTH//2 - score_info.get_width()//2, HEIGHT//2 - 10))
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 50))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
