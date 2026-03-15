from interface import TerminalUI, VoiceSensor
from rich.console import Console
import queue
import time

# Prueba de TerminalUI
console = Console()
ui = TerminalUI(console)

# Simular actualización de display
ui.update_display(player_hp=100, enemy_hp=80, distance=20)
layout = ui.get_layout()
console.print(layout)

# Prueba de VoiceSensor
voice_queue = queue.Queue()
sensor = VoiceSensor(voice_queue)

# Esperar un poco y ver si hay algo en la cola (habla al micrófono)
print("Habla al micrófono para probar el reconocimiento de voz...")
time.sleep(10)  # Espera 10 segundos

if not voice_queue.empty():
    recognized_text = voice_queue.get()
    print(f"Texto reconocido: {recognized_text}")
else:
    print("No se reconoció nada en 10 segundos.")

# Nota: El hilo daemon continúa corriendo en segundo plano