import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
from io import BytesIO
from urllib.parse import urljoin
import webbrowser

# Базовый URL страницы со стульями
BASE_URL = "https://www.ex-astris-scientia.org/database/chairs-trek.htm"

def fetch_chairs():
    """Загружает страницу и извлекает данные о стульях."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(BASE_URL, headers=headers)
        response.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Не удалось загрузить страницу: {e}")

    soup = BeautifulSoup(response.text, "html.parser")
    chairs = []

    # Ищем все таблицы, в которых есть заголовок "Chair name"
    for table in soup.find_all("table"):
        if not table.find("th", string="Chair name"):
            continue

        # Пропускаем первую строку с заголовками
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            # 1. Изображение
            img_tag = cols[0].find("img")
            image_url = ""
            if img_tag and img_tag.get("src"):
                image_url = urljoin(BASE_URL, img_tag["src"])

            # 2. Название
            name = cols[1].get_text(strip=True)

            # 3. Где видели
            seen_in = cols[2].get_text(strip=True)

            # 4. Ссылка (ищем в столбце с названием, иначе используем ссылку на фото)
            link_tag = cols[1].find("a")
            if link_tag and link_tag.get("href"):
                link = urljoin(BASE_URL, link_tag["href"])
            else:
                link = image_url

            chairs.append({
                "name": name,
                "seen_in": seen_in,
                "image_url": image_url,
                "link": link
            })

    if not chairs:
        raise RuntimeError("Не удалось найти данные о стульях на странице.")
    return chairs

class ChairApp:
    def __init__(self, root, chairs):
        self.root = root
        self.chairs = chairs
        self.count = len(chairs)

        self.root.title("Какой ты стул из Star Trek?")
        self.root.geometry("550x650")
        self.root.resizable(False, False)

        # Основной фрейм
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Подсказка о диапазоне
        ttk.Label(
            main_frame,
            text=f"Введите число от 1 до {self.count}:",
            font=("Arial", 12)
        ).pack(pady=(0, 5))

        # Поле ввода числа
        self.spinbox = ttk.Spinbox(main_frame, from_=1, to=self.count, width=10, font=("Arial", 12))
        self.spinbox.pack(pady=5)

        # Кнопка запуска
        ttk.Button(
            main_frame,
            text="Узнать стул",
            command=self.show_chair
        ).pack(pady=15)

        # Фрейм для результата
        result_frame = ttk.LabelFrame(main_frame, text="Результат", padding="10")
        result_frame.pack(fill="both", expand=True, pady=10)

        # Место для фото
        self.image_label = ttk.Label(result_frame)
        self.image_label.pack(pady=10)

        # Название
        self.name_label = ttk.Label(result_frame, font=("Arial", 14, "bold"), wraplength=450)
        self.name_label.pack(pady=5)

        # Где видели
        self.seen_label = ttk.Label(result_frame, font=("Arial", 10), wraplength=450, justify="left")
        self.seen_label.pack(pady=5)

        # Ссылка
        self.link_label = ttk.Label(
            result_frame,
            font=("Arial", 10, "underline"),
            foreground="blue",
            cursor="hand2",
            wraplength=450
        )
        self.link_label.pack(pady=5)
        self.link_label.bind("<Button-1>", self.open_link)

        self.current_link = ""

    def show_chair(self):
        """Обрабатывает нажатие кнопки и отображает информацию."""
        try:
            num = int(self.spinbox.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите целое число.")
            return

        if not (1 <= num <= self.count):
            messagebox.showerror("Ошибка", f"Число должно быть от 1 до {self.count}.")
            return

        chair = self.chairs[num - 1]

        # Загрузка и отображение изображения
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(chair["image_url"], headers=headers, timeout=10)
            response.raise_for_status()
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            img.thumbnail((300, 300))  # ограничиваем размер
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo)
            self.image_label.image = photo  # сохраняем ссылку, чтобы изображение не исчезло
        except Exception:
            self.image_label.config(image="")
            self.image_label.image = None
            messagebox.showwarning("Изображение", "Не удалось загрузить фотографию стула.")

        # Отображение текста
        self.name_label.config(text=chair["name"])
        self.seen_label.config(text=f"Где видели: {chair['seen_in']}")
        self.current_link = chair["link"]
        self.link_label.config(text=f"Ссылка: {chair['link']}")

    def open_link(self, event):
        """Открывает ссылку в браузере по клику."""
        if self.current_link:
            webbrowser.open(self.current_link)

def main():
    try:
        chairs = fetch_chairs()
    except Exception as e:
        # Показываем ошибку, если не удалось загрузить данные
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка загрузки", str(e))
        return

    root = tk.Tk()
    app = ChairApp(root, chairs)
    root.mainloop()

if __name__ == "__main__":
    main()