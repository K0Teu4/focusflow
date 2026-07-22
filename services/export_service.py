# services/export_service.py
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import os


TYPE_NAMES = {
    'work': 'Работа',
    'short_break': 'Короткий перерыв',
    'long_break': 'Длинный перерыв',
}


class ExportService:
    """Сервис для экспорта данных в CSV."""

    @staticmethod
    def get_default_export_dir() -> Path:
        """Возвращает стандартную папку для экспорта (Downloads или Documents)."""
        # Пробуем Downloads
        downloads = Path.home() / "Downloads"
        if downloads.exists():
            return downloads
        
        # Fallback на Documents
        documents = Path.home() / "Documents"
        if documents.exists():
            return documents
        
        # Последний вариант — домашняя папка
        return Path.home()

    @staticmethod
    def generate_filename() -> str:
        """Генерирует имя файла вида focusflow_export_2026-07-22.csv"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        return f"focusflow_export_{date_str}.csv"

    @staticmethod
    def generate_full_path() -> Path:
        """Генерирует полный путь к файлу экспорта."""
        export_dir = ExportService.get_default_export_dir()
        filename = ExportService.generate_filename()
        
        # Если файл уже существует, добавляем timestamp
        full_path = export_dir / filename
        if full_path.exists():
            timestamp = datetime.now().strftime('%H%M%S')
            filename = f"focusflow_export_{datetime.now().strftime('%Y-%m-%d')}_{timestamp}.csv"
            full_path = export_dir / filename
        
        return full_path

    @staticmethod
    def export_sessions_to_csv(sessions: List[Dict], file_path: Path) -> bool:
        """
        Экспортирует список сессий в CSV файл.
        
        Args:
            sessions: список словарей с ключами:
                - started_at (datetime)
                - type (str): 'work'/'short_break'/'long_break'
                - duration_sec (int)
                - task_title (str|None)
                - is_completed (bool)
            file_path: путь к файлу для сохранения
        
        Returns:
            True если успешно, False при ошибке
        """
        try:
            # Убеждаемся, что папка существует
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                
                # Заголовки
                writer.writerow([
                    'Дата и время',
                    'Тип сессии',
                    'Длительность (мин)',
                    'Задача',
                    'Завершена',
                ])
                
                # Данные
                for s in sessions:
                    started = s.get('started_at')
                    date_str = started.strftime('%Y-%m-%d %H:%M:%S') if started else ''
                    type_name = TYPE_NAMES.get(s.get('type', ''), s.get('type', ''))
                    duration_min = (s.get('duration_sec', 0) or 0) // 60
                    task = s.get('task_title') or 'Без задачи'
                    completed = 'Да' if s.get('is_completed') else 'Нет'
                    
                    writer.writerow([date_str, type_name, duration_min, task, completed])
            
            return True
        except Exception as e:
            print(f"❌ Ошибка экспорта: {e}")
            return False