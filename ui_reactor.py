"""
Sistema de Enfriamiento de Emergencia - UI usando PySimpleGUI.
Interfaz SCADA minimalista con Dark Mode para el simulador de reactor.
"""

import PySimpleGUI as sg
import threading
import queue
import time
from engine import GameEngine, normalize_text
from interface import VoiceSensor


class ReactorControlUI:
    """
    Interfaz gráfica tipo SCADA para el simulador de sobrecarga de reactor.
    Dark Mode minimalista, estética de panel de control industrial.
    """
    
    def __init__(self):
        """Inicializa la interfaz gráfica."""
        # Tema oscuro
        sg.theme('DarkBlue1')
        sg.set_options(font=('Courier', 11))
        
        # Inicializar motor del juego
        self.game_engine = GameEngine(difficulty=1)
        self.voice_sensor = VoiceSensor()
        
        # Variables de UI
        self.game_active = True
        self.telemetry_logs = []
        
        # Construir la ventana
        self.window = self._build_window()
        
        # Iniciar sensor de voz
        self.voice_sensor.start()
    
    def _build_window(self):
        """Construye la ventana principal de la interfaz."""
        
        # Define the layout
        layout = [
            # ========== HEADER ==========
            [sg.Text('⚛️  REACTOR CENTRAL - MONITOR DE PRESIÓN', 
                    font=('Courier', 16, 'bold'), 
                    text_color='cyan', 
                    justification='center')],
            [sg.Text('_' * 80, text_color='cyan')],
            
            # ========== PRESSURE BAR ==========
            [sg.Text('PRESIÓN DEL NÚCLEO', font=('Courier', 12, 'bold'), text_color='cyan')],
            [sg.Text('', size=(3, 1), key='-PRESSURE-NUM-', 
                    font=('Courier', 18, 'bold'), text_color='lime')],
            [sg.ProgressBar(100, size=(70, 25), key='-PRESSURE-BAR-', 
                           bar_color=('lime green', '#1a1a1a'))],
            
            [sg.Text('_' * 80, text_color='cyan')],
            
            # ========== COMMAND SEQUENCE ==========
            [sg.Text('SECUENCIA DE ENFRIAMIENTO REQUERIDA:', 
                    font=('Courier', 10, 'bold'), text_color='orange')],
            [sg.Text('ESPERANDO...', size=(60, 1), key='-SEQUENCE-', 
                    font=('Courier New', 20, 'bold'), 
                    text_color='cyan',
                    background_color='#1a1a1a',
                    justification='center')],
            
            [sg.Text('_' * 80, text_color='cyan')],
            
            # ========== TELEMETRY BOX ==========
            [sg.Text('CONSOLA DE TELEMETRÍA - ENTRADA DE VOZ:', 
                    font=('Courier', 10, 'bold'), text_color='cyan')],
            [sg.Multiline(size=(80, 12), key='-TELEMETRY-', 
                         font=('Courier New', 9),
                         text_color='lime',
                         background_color='#0a0a0a',
                         disabled=True)],
            
            # ========== STATUS BAR ==========
            [sg.Text('_' * 80, text_color='cyan')],
            [sg.Text('🟢 SISTEMA OPERATIVO', key='-STATUS-', 
                    font=('Courier', 11, 'bold'), text_color='lime')],
            [sg.Text('', key='-HP-STATUS-', 
                    font=('Courier', 10), text_color='orange')],
        ]
        
        window = sg.Window('SISTEMA DE ENFRIAMIENTO DE EMERGENCIA', 
                          layout,
                          size=(900, 700),
                          finalize=True,
                          background_color='#0a0e27')
        
        return window
    
    def _add_telemetry(self, message: str) -> None:
        """Agrega un mensaje al registro de telemetría."""
        self.telemetry_logs.append(message)
        # Mantener solo los últimos 100 logs
        if len(self.telemetry_logs) > 100:
            self.telemetry_logs = self.telemetry_logs[-100:]
        
        full_text = '\n'.join(self.telemetry_logs)
        self.window['-TELEMETRY-'].update(full_text)
        self.window['-TELEMETRY-'].set_ibeam_cursor_location(len(full_text))
    
    def _update_pressure_bar(self) -> None:
        """Actualiza la barra de presión y su color."""
        pressure_percent = (50 - self.game_engine.projectile_position) / 50
        pressure_value = int(pressure_percent * 100)
        
        # Actualizar barra
        self.window['-PRESSURE-BAR-'].update(pressure_value)
        
        # Cambiar color y texto según presión
        if pressure_percent > 0.8:
            color = 'red'
            pressure_text = f"{pressure_value} % - ⚠️  CRÍTICO"
        elif pressure_percent > 0.5:
            color = 'orange'
            pressure_text = f"{pressure_value} % - ⚡ ALTO"
        else:
            color = 'lime green'
            pressure_text = f"{pressure_value} %"
        
        self.window['-PRESSURE-NUM-'].update(pressure_text, text_color=color)
        self.window['-PRESSURE-BAR-'].update(pressure_value, bar_color=(color, '#1a1a1a'))
    
    def _update_hud(self) -> None:
        """Actualiza los HUD de estado y HP."""
        self.window['-SEQUENCE-'].update(self.game_engine.current_spell)
        self.window['-HP-STATUS-'].update(
            f"Operador: {self.game_engine.player_hp} HP | "
            f"Reactor: {self.game_engine.enemy_hp} HP | "
            f"Velocidad: {self.game_engine.game_speed:.1f}x"
        )
    
    def run(self) -> None:
        """Ejecuta el loop principal de la aplicación."""
        
        while True:
            event, values = self.window.read(timeout=100)
            
            # Manejar cierre de ventana
            if event == sg.WINDOW_CLOSED:
                break
            
            # Si el juego ya terminó, esperamos cierre
            if not self.game_active:
                continue
            
            # ================================
            # 1. AVANZAR PROYECTIL
            # ================================
            projectile_hit = self.game_engine.advance_projectile()
            if projectile_hit:
                self._add_telemetry("💥 [ALERTA] ¡EL REACTOR SUFRIÓ UN IMPACTO!")
            
            # ================================
            # 2. LEER COLA DE VOZ
            # ================================
            try:
                spoken_word = self.voice_sensor.voice_queue.get_nowait()
                
                # Mostrar en telemetría
                self._add_telemetry(f"🎤 Detectado: {spoken_word}")
                
                # Validar contra hechizo
                if self.game_engine.validate_voice(spoken_word):
                    self._add_telemetry(
                        f"✅ ¡SECUENCIA CORRECTA! '{spoken_word}' == '{self.game_engine.current_spell}'"
                    )
                    self.window['-STATUS-'].update(
                        "🟢 ENFRIAMIENTO EXITOSO",
                        text_color='lime'
                    )
                else:
                    self._add_telemetry(
                        f"❌ Secuencia incorrecta: '{spoken_word}' ≠ '{self.game_engine.current_spell}'"
                    )
                    self.window['-STATUS-'].update(
                        "🔴 ERROR DE SECUENCIA",
                        text_color='red'
                    )
            
            except queue.Empty:
                pass
            
            # ================================
            # 3. ACTUALIZAR UI
            # ================================
            self._update_pressure_bar()
            self._update_hud()
            
            # ================================
            # 4. VERIFICAR GAME OVER
            # ================================
            if self.game_engine.is_game_over():
                self.game_active = False
                winner = self.game_engine.get_winner()
                
                if winner == "player":
                    self.window['-STATUS-'].update(
                        "🟢 ¡REACTOR SALVADO! (VICTORIA)",
                        text_color='lime'
                    )
                    self._add_telemetry("\n🎉 ¡NIVEL COMPLETADO! Cierre la ventana para salir.")
                else:
                    self.window['-STATUS-'].update(
                        "🔴 ¡MELTDOWN! (DERROTA)",
                        text_color='red'
                    )
                    self._add_telemetry("\n💀 ¡REACTOR EN FUSIÓN! Cierre la ventana para salir.")
    
    def cleanup(self) -> None:
        """Limpia recursos antes de cerrar."""
        self.voice_sensor.stop()
        self.window.close()


def main():
    """Punto de entrada de la aplicación."""
    ui = ReactorControlUI()
    
    try:
        ui.run()
    finally:
        ui.cleanup()


if __name__ == "__main__":
    main()

