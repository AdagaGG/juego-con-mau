"""
Sistema de Enfriamiento de Emergencia - UI SCADA minimalista con Rich.
Interfaz tipo panel de control industrial con Dark Mode.
"""

import time
import threading
import queue
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.live import Live

from engine import GameEngine
from interface import VoiceSensor


class SCDAReactorUI:
    """
    Interfaz SCADA para simulador de reactor nuclear.
    Estética industrial minimalista con Dark Mode en Terminal.
    """
    
    def __init__(self):
        """Inicializa la interfaz SCADA."""
        self.console = Console(width=100, legacy_windows=False)
        self.game_engine = GameEngine(difficulty=1)
        self.voice_sensor = VoiceSensor()
        
        # Registro de eventos
        self.events_log = []
        self.game_active = True
        
        # Iniciar sensor de voz
        self.voice_sensor.start()
    
    def _build_layout(self) -> Layout:
        """Construye el layout completo del panel SCADA."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # ========== HEADER ==========
        title = Text("⚛️  REACTOR CENTRAL - SISTEMA DE ENFRIAMIENTO", 
                    style="bold cyan")
        layout["header"].update(Panel(
            Align.center(title),
            style="cyan",
            border_style="cyan"
        ))
        
        # ========== BODY - Dividir en tres secciones ==========
        layout["body"].split_row(
            Layout(name="pressure_section"),
            Layout(name="command_section"),
            Layout(name="telemetry_section")
        )
        
        # ----- PRESIÓN -----
        pressure_percent = (50 - self.game_engine.projectile_position) / 50
        
        # Determinar color y estado
        if pressure_percent > 0.8:
            pressure_color = "red"
            pressure_status = "⚠️  CRÍTICO"
        elif pressure_percent > 0.5:
            pressure_color = "yellow"
            pressure_status = "⚡ ALTO"
        else:
            pressure_color = "green"
            pressure_status = "✓ NORMAL"
        
        pressure_bar_text = f"[{pressure_color}]{'█' * int(pressure_percent * 30)}{' ' * (30 - int(pressure_percent * 30))}[/{pressure_color}]"
        
        pressure_panel = Panel(
            f"{pressure_bar_text}\n\n[{pressure_color} bold]{int(pressure_percent * 100):>3} %[/{pressure_color} bold]  {pressure_status}",
            title="[cyan]PRESIÓN DEL NÚCLEO[/cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        layout["pressure_section"].update(pressure_panel)
        
        # ----- COMANDO -----
        command_text = Text(self.game_engine.current_spell, 
                           style="bold cyan", justify="center")
        command_panel = Panel(
            command_text,
            title="[orange1]SECUENCIA REQUERIDA[/orange1]",
            border_style="orange1",
            padding=(2, 1)
        )
        layout["command_section"].update(command_panel)
        
        # ----- TELEMETRÍA -----
        telemetry_text = "\n".join(self.events_log[-12:])  # Últimos 12 eventos
        if not telemetry_text:
            telemetry_text = "[dim]Esperando entrada de voz...[/dim]"
        
        telemetry_panel = Panel(
            telemetry_text,
            title="[cyan]CONSOLA DE TELEMETRÍA[/cyan]",
            border_style="cyan",
            padding=(0, 1)
        )
        layout["telemetry_section"].update(telemetry_panel)
        
        # ========== FOOTER ==========
        footer_table = Table.grid(padding=(0, 1))
        footer_table.add_row(
            f"[green]🟢 OPERADOR: {self.game_engine.player_hp} HP[/green]",
            f"[red]🔴 REACTOR: {self.game_engine.enemy_hp} HP[/red]",
            f"[yellow]⚡ VELOCIDAD: {self.game_engine.game_speed:.1f}x[/yellow]"
        )
        layout["footer"].update(Panel(
            footer_table,
            border_style="cyan",
            padding=(0, 1)
        ))
        
        return layout
    
    def _add_event(self, message: str) -> None:
        """Agrega un evento al registro."""
        timestamp = time.strftime("%H:%M:%S")
        event = f"[cyan]{timestamp}[/cyan] {message}"
        self.events_log.append(event)
    
    def run(self) -> None:
        """Ejecuta el loop principal del simulador."""
        live = None
        
        try:
            print("\n🎤 Escuchando micrófono. Pronuncia la secuencia de enfriamiento...\n")
            time.sleep(1)
            
            # Crear layout inicial
            layout = self._build_layout()
            live = Live(layout, console=self.console, refresh_per_second=2, screen=True)
            live.start()
            
            while self.game_active:
                # ================================
                # 1. AVANZAR PROYECTIL
                # ================================
                projectile_hit = self.game_engine.advance_projectile()
                if projectile_hit:
                    self._add_event("[red]💥 ¡IMPACTO! El reactor recibió daño[/red]")
                
                # ================================
                # 2. LEER COLA DE VOZ
                # ================================
                try:
                    spoken_word = self.voice_sensor.voice_queue.get_nowait()
                    self._add_event(f"[cyan]🎤 Detectado:[/cyan] '{spoken_word}'")
                    
                    # Validar
                    if self.game_engine.validate_voice(spoken_word):
                        self._add_event(
                            f"[green]✅ ¡CORRECTO![/green] "
                            f"'{spoken_word}' == '{self.game_engine.current_spell}'"
                        )
                    else:
                        self._add_event(
                            f"[red]❌ Error:[/red] "
                            f"'{spoken_word}' ≠ '{self.game_engine.current_spell}'"
                        )
                
                except queue.Empty:
                    pass
                
                # ================================
                # 3. ACTUALIZAR UI
                # ================================
                layout = self._build_layout()
                live.update(layout)
                
                # ================================
                # 4. VERIFICAR GAME OVER
                # ================================
                if self.game_engine.is_game_over():
                    self.game_active = False
                    layout = self._build_layout()
                    live.update(layout)
                    
                    winner = self.game_engine.get_winner()
                    if winner == "player":
                        self._add_event("[green bold]🎉 ¡VICTORIA! Reactor salvado[/green bold]")
                    else:
                        self._add_event("[red bold]💀 ¡DERROTA! Fusión nuclear[/red bold]")
                    
                    layout = self._build_layout()
                    live.update(layout)
                    time.sleep(3)
                
                time.sleep(0.5)  # Control de velocidad
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Simulación interrumpida por usuario")
        
        finally:
            if live is not None:
                live.stop()
            self.voice_sensor.stop()
            print("Simulación finalizada.\n")


def main():
    """Punto de entrada."""
    ui = SCDAReactorUI()
    ui.run()


if __name__ == "__main__":
    main()
