import time
from queue import Empty
from engine import GameEngine
from interface import TerminalUI, VoiceSensor


def main():
    """
    Bucle principal del juego.
    
    Coordina:
    - Lectura de entrada de voz (no bloqueante, desde cola)
    - Lógica del motor (avance de proyectil, validación de hechizos)
    - Renderización en tiempo real (rich.Live)
    """
    
    # Inicializar componentes
    game_engine = GameEngine(difficulty=1)
    terminal_ui = TerminalUI(game_engine)
    voice_sensor = VoiceSensor()
    
    # Iniciar el sensor de voz en un hilo daemon
    voice_sensor.start()
    
    # Control de tick rate (60 FPS = ~16.67 ms por frame)
    TICK_RATE = 60
    frame_time = 1.0 / TICK_RATE
    
    try:
        # Renderizar la primera vez
        terminal_ui.render()
        
        # Bucle principal
        while not game_engine.is_game_over():
            frame_start = time.time()
            
            # ============================================
            # 1. REVISAR COLA DE VOZ (no bloqueante)
            # ============================================
            try:
                spoken_word = voice_sensor.voice_queue.get_nowait()
                
                # Validar la palabra contra el hechizo actual
                if game_engine.validate_voice(spoken_word):
                    # Acierto: se muestra en la UI
                    terminal_ui.set_feedback(f"✓ ¡{spoken_word}! Acertaste.", color="green")
                else:
                    # Error: palabra no coincide
                    terminal_ui.set_feedback(
                        f"✗ {spoken_word} no es {game_engine.current_spell}",
                        color="red"
                    )
            except Empty:
                # No hay palabra en la cola, continuar normalmente
                pass
            
            # ============================================
            # 2. AVANZAR PROYECTIL
            # ============================================
            projectile_hit = game_engine.advance_projectile()
            
            if projectile_hit:
                terminal_ui.set_feedback("💥 ¡Te golpeó!", color="yellow")
            
            # ============================================
            # 3. RENDERIZAR (rich.Live maneja la actualización)
            # ============================================
            terminal_ui.render()
            
            # ============================================
            # 4. MANTENER TICK RATE
            # ============================================
            elapsed = time.time() - frame_start
            sleep_time = frame_time - elapsed
            
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # ============================================
        # GAME OVER
        # ============================================
        winner = game_engine.get_winner()
        terminal_ui.set_feedback(
            f"¡GAME OVER! {'Ganaste 🎉' if winner == 'player' else 'Perdiste 💀'}",
            color="cyan"
        )
        terminal_ui.render()
        
        # Mostrar resultado por 3 segundos antes de cerrar
        time.sleep(3)
    
    except KeyboardInterrupt:
        print("\n⚠️  Juego interrumpido por el usuario.")
    
    finally:
        # Detener el sensor de voz
        voice_sensor.stop()
        print("Juego finalizado.")


if __name__ == "__main__":
    main()
