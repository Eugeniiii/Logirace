from pygame import *
from Python.ui import *
from Python.plants import Plant

import json
import pandas as pd
import os

init()
mixer.init()

root = display.set_mode((1280, 900))
display.set_caption("Mars Farm Simulator")
display.set_icon(image.load("Assets/Sprites/icon.png"))
clock = time.Clock()

standart_font = font.SysFont("comicsans", 25)

game_logo = transform.scale(image.load("Assets/Sprites/logo.png"), (700, 400))
button_image = transform.scale(image.load("Assets/Sprites/button.png"), (300, 70))
panel_image = transform.scale(image.load("Assets/Sprites/panel.png"), (1100, 700))
dialogue_image = image.load("Assets/Sprites/dialogue.png")

room_texture = transform.scale(image.load("Assets/Sprites/room.png"), (1280, 900))
farm_texture = transform.scale(image.load("Assets/Sprites/Farm background.jpg"), (1280, 900))
truck_backyard = transform.scale(image.load("Assets/Sprites/Truck backyard.jpg"), (1280, 900))
door_texture = transform.scale(image.load("Assets/Sprites/door.png"), (200, 450))
door_texture_v2 = transform.scale(door_texture, (150, 250))

def load_plant_stages(plant_name, max_stage=4):
    sprites = []
    folder = "Assets/Sprites/Spritesheets"
    for i in range(1, max_stage + 1):
        path = f"{folder}/{plant_name}{i}.png"
        try:
            sprite = image.load(path).convert_alpha()
            sprites.append(sprite)
        except FileNotFoundError:
            print(f"Не знайдено: {path}")
    return sprites

tomato_sprites = load_plant_stages("tomato")
carrot_sprites = load_plant_stages("carrot")
potato_sprites = load_plant_stages("potato")

plant_sprites = {
    "tomato": tomato_sprites,
    "carrot": carrot_sprites,
    "potato": potato_sprites
}

scenes = ["Menu", "Lobby", "Farm", "Truck"]
current_scene = scenes[0]

SAVE_FILE = "save.json"
PLANTS_CSV = "plants_data.csv"

about_panel_opened = False
setting_panel_opened = False
auto_save = True

farm_slots = [None] * 9
current_day = 1
max_days = 10
total_delivered = 0
mission_failed = False
mission_completed = False
selected_seed = None
cargo = {"tomato": 0, "carrot": 0, "potato": 0}

try:
    with open("Assets/AboutGame.txt", "r", encoding="utf-8") as f:
        about_text = f.readlines()
except FileNotFoundError:
    about_text = "File not found"

def exit_game():
    quit()

def toggle_auto_save():
    global auto_save
    auto_save = not auto_save
    print(f"Автозбереження: {'Увімкнено' if auto_save else 'Вимкнено'}")

def toggle_setting_panel():
    global setting_panel_opened
    setting_panel_opened = not setting_panel_opened

def reset_save():
    global current_day, total_delivered, mission_failed, mission_completed, selected_seed, farm_slots, cargo
    current_day = 1
    total_delivered = 0
    mission_failed = False
    mission_completed = False
    selected_seed = None
    cargo = {"tomato": 0, "carrot": 0, "potato": 0}
    farm_slots = [None] * 9
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
    if os.path.exists(PLANTS_CSV):
        os.remove(PLANTS_CSV)
    print("Збереження скинуто!")

def open_about_panel():
    global about_panel_opened
    about_panel_opened = not about_panel_opened

def goto_farm():
    global current_scene
    current_scene = "Farm"

def goto_truck():
    global current_scene
    current_scene = "Truck"

def goto_game():
    global current_scene
    current_scene = "Lobby"
    mixer.music.stop()

def plant_seed(slot_index, plant_type):
    global farm_slots
    if farm_slots[slot_index] is None and plant_type:
        farm_slots[slot_index] = Plant(plant_type, plant_sprites)

def water_plant(slot_index):
    if farm_slots[slot_index]:
        farm_slots[slot_index].water()

def harvest_plant(slot_index):
    global farm_slots
    plant = farm_slots[slot_index]
    if plant and plant.is_ready():
        print(f"Зібрано {plant.name}!")
        add_to_cargo(plant.plant_type)
        farm_slots[slot_index] = None
        return plant.value
    return 0

def next_day():
    global current_day, mission_failed, mission_completed
    current_day += 1

    for plant in farm_slots:
        if plant:
            plant.update()

    if current_day > max_days:
        if total_delivered <= 0:
            mission_failed = True
        else:
            mission_completed = True

    if auto_save:
        save_game()

def select_tomato():
    global selected_seed
    selected_seed = "tomato"

def select_carrot():
    global selected_seed
    selected_seed = "carrot"

def select_potato():
    global selected_seed
    selected_seed = "potato"

def clear_selection():
    global selected_seed
    selected_seed = None


def add_to_cargo(plant_type, amount=1):
    global cargo
    if plant_type in cargo:
        cargo[plant_type] += amount
        print(f"Додано до вантажу: {plant_type} x{amount}")


def send_delivery():
    global total_delivered, cargo
    delivered_now = sum(cargo.values())

    if delivered_now > 0:
        total_delivered += delivered_now
        print(f"✅ Відправлено {delivered_now} одиниць врожаю! Загалом: {total_delivered}")
        cargo = {"tomato": 0, "carrot": 0, "potato": 0}  # очищаємо вантаж
    else:
        print("Вантаж порожній!")

SAVE_FILE = "save.json"
PLANTS_CSV = "plants_data.csv"


def save_game():
    game_data = {
        "current_day": current_day,
        "max_days": max_days,
        "total_delivered": total_delivered,
        "mission_failed": mission_failed,
        "mission_completed": mission_completed,
        "selected_seed": selected_seed,
        "auto_save": auto_save  # ← додаємо
    }

    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(game_data, f, ensure_ascii=False, indent=4)

    # Збереження рослин (pandas)
    plants_list = []
    for i, plant in enumerate(farm_slots):
        if plant:
            plants_list.append({
                "slot": i,
                "type": plant.plant_type,
                "stage": plant.stage,
                "days_grown": plant.days_grown,
                "is_watered": plant.is_watered,
                "is_dead": plant.is_dead,
                "name": plant.name
            })

    if plants_list:
        pd.DataFrame(plants_list).to_csv(PLANTS_CSV, index=False, encoding="utf-8")
    else:
        pd.DataFrame(columns=["slot", "type", "stage", "days_grown", "is_watered", "is_dead", "name"]).to_csv(
            PLANTS_CSV, index=False)

    print("Гра збережена!")


def load_game():
    global current_day, total_delivered, mission_failed, mission_completed, selected_seed, auto_save, farm_slots

    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                current_day = data.get("current_day", 1)
                total_delivered = data.get("total_delivered", 0)
                mission_failed = data.get("mission_failed", False)
                mission_completed = data.get("mission_completed", False)
                selected_seed = data.get("selected_seed", None)
                auto_save = data.get("auto_save", True)  # ← завантажуємо
        except:
            print("Помилка читання save.json")

    # Завантаження рослин
    farm_slots = [None] * 9
    if os.path.exists(PLANTS_CSV):
        try:
            df = pd.read_csv(PLANTS_CSV)
            for _, row in df.iterrows():
                slot = int(row["slot"])
                plant = Plant(row["type"], plant_sprites)
                plant.stage = int(row.get("stage", 0))
                plant.days_grown = int(row.get("days_grown", 0))
                plant.is_watered = bool(row.get("is_watered", False))
                plant.is_dead = bool(row.get("is_dead", False))
                farm_slots[slot] = plant
        except Exception as e:
            print("Помилка завантаження рослин:", e)

    print(f"Гра завантажена! (Автозбереження: {'Увімкнено' if auto_save else 'Вимкнено'})")

load_game()

def quick_save():
    save_game()

def quick_load():
    load_game()

save_button = StandartButton(root, 650, 780, 180, 50, "Зберегти", "Comic Sans MS", (0, 100, 200), quick_save)
load_button = StandartButton(root, 850, 780, 180, 50, "Завантажити", "Comic Sans MS", (0, 150, 100), quick_load)

def send_delivery_command():
    send_delivery()

send_button = StandartButton(root, 900, 700, 300, 80, "Відправити вантаж", "Comic Sans MS", (0, 180, 0), send_delivery_command)
clear_cargo_button = StandartButton(root, 900, 800, 300, 60, "Очистити вантаж", "Comic Sans MS", (180, 0, 0), lambda: globals().update(cargo={"tomato":0,"carrot":0,"potato":0}))

tomato_btn = StandartButton(root, 50, 700, 180, 60, "Помідор", "Comic Sans MS", (200, 50, 50), select_tomato)
carrot_btn = StandartButton(root, 250, 700, 180, 60, "Морква", "Comic Sans MS", (255, 140, 0), select_carrot)
potato_btn = StandartButton(root, 450, 700, 180, 60, "Картопля", "Comic Sans MS", (139, 69, 19), select_potato)
clear_selection_btn = StandartButton(root, 50, 780, 200, 50, "Скасувати вибір", "Comic Sans MS", (100, 100, 100), clear_selection)

next_day_button = StandartButton(root, 900, 750, 280, 70, "Наступний день", "Comic Sans MS", (50, 150, 50), next_day)

exit_button = Button(root, 500, 760, 200, 70, image=button_image, text="Exit", command=exit_game, font="Comic Sans MS")
about_game_button = Button(root, 500, 670, 200, 70, image=button_image, text="About game", command=open_about_panel, font="Comic Sans MS")
play_button = Button(root, 500, 490, 200, 70, image=button_image, text="Play", font="Comic Sans MS", command=goto_game)
settings_button = Button(root, 500, 580, 200, 70, image=button_image, text="Settings", font="Comic Sans MS", command=toggle_setting_panel)

back_button = StandartButton(root, 150, 100, 50, 50, bg_color=(233, 232, 10), text="<=", font="Arial", command=open_about_panel)
back_from_setting_button = StandartButton(root, 150, 100, 50, 50, bg_color=(233, 232, 10), text="<=", font="Arial", command=toggle_setting_panel)

day_one_dialogue = Dialogue_menu(440, 650, 400, 200, "Congratulations on your first day.", "Comic Sans MS", bg_image=dialogue_image)

backyard_door = ImageButton(100, 200, 200, 450, image=door_texture, command=goto_farm)
truck_door = ImageButton(570, 400, 100, 250, image=door_texture_v2, command=goto_truck)
goto_farm_truck_button = StandartButton(root, 10, 10, 50, 50, "<=", "Arial", (233, 232, 10), goto_farm)

from_farm_to_menu_button = StandartButton(root, 10, 10, 100, 50, "В меню", "Comic Sans MS", (200, 50, 50), goto_game)
from_farm_to_truck_button = StandartButton(root, 10, 850, 100, 50, "До вантажівки", "Comic Sans MS", (200, 50, 50), goto_truck)

auto_save_btn = StandartButton(root, 400, 300, 500, 70, "Автозбереження: УВІМК", "Comic Sans MS", (0, 180, 0), toggle_auto_save)
reset_save_btn = StandartButton(root, 400, 400, 500, 70, "СКИНУТИ ЗБЕРЕЖЕННЯ", "Comic Sans MS", (180, 0, 0), reset_save)

running = True
mixer.music.load("Assets/Sounds/SAVS Soundtrack.mp3")
mixer.music.play(-1)

while running:
    for e in event.get():
        if e.type == QUIT:
            running = False

    root.fill((0, 0, 0))

    if current_scene == "Menu":
        if not about_panel_opened:
            root.blit(game_logo, (300, 0))
            exit_button.draw(root)
            about_game_button.draw(root)
            play_button.draw(root)
            settings_button.draw(root)

        if about_panel_opened:
            root.blit(panel_image, (100, 50))
            back_button.draw(root)
            y_offset = 200
            for line in about_text:
                text_surf = standart_font.render(line.strip(), True, (0, 0, 0))
                root.blit(text_surf, (150, y_offset))
                y_offset += 30

        if setting_panel_opened:
            root.blit(panel_image, (100, 50))
            back_from_setting_button.draw(root)

            title = pygame.font.SysFont("Comic Sans MS", 50).render("НАЛАШТУВАННЯ", True, (0, 0, 0))
            auto_save_btn.text = f"Автозбереження: {'УВІМК' if auto_save else 'ВИМК'}"
            auto_save_btn.update_text()

            auto_save_btn.draw(root)
            reset_save_btn.draw(root)

    elif current_scene == "Lobby":
        root.blit(room_texture, (0, 0))
        backyard_door.draw(root)
        next_day_button.draw(root)

        day_text = standart_font.render(f"День: {current_day} / {max_days}", True, (255, 255, 100))
        root.blit(day_text, (50, 50))

        if mission_failed:
            fail_text = font.SysFont("Comic Sans MS", 60).render("МІСІЯ ПРОВАЛЕНА!", True, (200, 0, 0))
            root.blit(fail_text, (280, 300))
        if mission_completed:
            win_text = font.SysFont("Comic Sans MS", 60).render("МІСІЯ ВИКОНАНА!", True, (0, 200, 0))
            root.blit(win_text, (280, 300))

        day_one_dialogue.draw(root)

    elif current_scene == "Farm":
        root.blit(farm_texture, (0, 0))

        # Слоти рослин
        for i in range(9):
            row = i // 3
            col = i % 3
            x = 180 + col * 280
            y = 120 + row * 220

            color = (80, 80, 80) if farm_slots[i] is None else (40, 140, 40)
            draw.rect(root, color, (x, y, 220, 200), border_radius=15, width=4)

            plant = farm_slots[i]
            if plant:
                sprite = plant.get_sprite()
                if sprite:
                    scaled = transform.scale(sprite, (160, 160))
                    root.blit(scaled, (x + 30, y + 20))

                stage_text = standart_font.render(f"Стадія: {plant.stage + 1}/4", True, (255, 255, 255))
                root.blit(stage_text, (x + 40, y + 170))

                if plant.is_dead:
                    dead_text = standart_font.render("ЗІВ'ЯЛА!", True, (200, 0, 0))
                    root.blit(dead_text, (x + 50, y + 10))

        # UI
        day_text = standart_font.render(f"День: {current_day}/{max_days}", True, (255, 220, 100))
        root.blit(day_text, (50, 30))

        tomato_btn.draw(root)
        carrot_btn.draw(root)
        potato_btn.draw(root)
        clear_selection_btn.draw(root)

        save_button.draw(root)
        load_button.draw(root)

        from_farm_to_menu_button.draw(root)
        from_farm_to_truck_button.draw(root)

        if selected_seed:
            seed_text = standart_font.render(f"Вибрано: {selected_seed.upper()}", True, (255, 255, 100))
            root.blit(seed_text, (700, 720))

    if current_scene == "Farm":
        if e.type == MOUSEBUTTONDOWN:
            pos = e.pos

            for i in range(9):
                row = i // 3
                col = i % 3
                x = 180 + col * 280
                y = 120 + row * 220
                slot_rect = Rect(x, y, 220, 200)

                if slot_rect.collidepoint(pos):
                    plant = farm_slots[i]

                    if e.button == 1:  # ЛІВА кнопка
                        if plant is None and selected_seed:
                            plant_seed(i, selected_seed)
                        elif plant:
                            water_plant(i)  # полив

                    elif e.button == 3:
                        if plant:
                            if plant.is_dead:
                                farm_slots[i] = None
                            elif plant.is_ready():
                                harvest_plant(i)
                    break

    elif current_scene == "Truck":
        root.blit(truck_backyard, (0, 0))
        goto_farm_truck_button.draw(root)
        send_button.draw(root)
        clear_cargo_button.draw(root)

        y = 150
        for plant_type, amount in cargo.items():
            if amount > 0:
                name = {"tomato": "Помідори", "carrot": "Морква", "potato": "Картопля"}.get(plant_type, plant_type)
                text = standart_font.render(f"{name}: {amount}", True, (255, 255, 100))
                root.blit(text, (100, y))
                y += 50

        total_text = standart_font.render(f"Загалом відправлено: {total_delivered}", True, (255, 220, 0))
        root.blit(total_text, (100, 50))

    display.flip()
    clock.tick(100)

quit()