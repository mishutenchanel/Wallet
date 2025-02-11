# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения в контейнер
COPY . /app

# Указываем порт, который будет использовать приложение
EXPOSE 5000

# Команда для запуска приложения
CMD ["waitress-serve", "--call", "app:create_app"]