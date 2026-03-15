import threading
import queue
import time
import speech_recognition as sr
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich.live import Live
from rich.text import Text


class TerminalUI:
    """
    Interfaz de terminal usando rich para renderizar el juego en tiempo real.
    """
    
    def __init__(self, game_engine):
        """
        Inicializa la UI del juego.
        
        Args:
            game_engine: Instancia de GameEngine para acceder al estado del juego
        """
        self.game_engine = game_engine
        self.console = Console()
        self.live = None
        self.feedback = ""
        self.feedback_color = "white"
    
    def _generate_game_art(self) -> str:
        """
        Genera el arte ASCII del campo de batalla.
        
        Returns:
            String con el arte ASCII del juego
        """
        distance = self.game_engine.projectile_position
        total_width = 60
        wizard_pos = 5
        enemy_pos = total_width - 10
        projectile_pos = enemy_pos - (50 - distance)
        
        # Crear líneas del campo
        lines = []
        for i in range(5):
            line = [" "] * total_width
            if i == 2:  # Línea media
                # Mago a la izquierda
                line[wizard_pos:wizard_pos+5] = list("[o_o]")
                # Enemigo a la derecha
                line[enemy_pos:enemy_pos+5] = list("(x_x)")
                # Proyectil en el medio
                if 0 <= projectile_pos < total_width - 5:
                    line[int(projectile_pos)] = "●"
            lines.append("".join(line))
        
        return "\n".join(lines)
    
    def _generate_layout(self) -> Layout:
        """
        Genera el layout actual del juego.
        
        Returns:
            Layout de rich con todos los paneles
        """
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="game", size=10),
            Layout(name="status", size=3),
            Layout(name="feedback", size=3),
            Layout(name="footer", size=2)
        )
        
        # Header con título
        header_text = Text("⚔️  DUELO DE HECHICEROS ⚔️", style="bold cyan")
        layout["header"].update(Panel(header_text, title="Juego"))
        
        # Game area con arte ASCII
        game_art = self._generate_game_art()
        layout["game"].update(Panel(game_art, title="Campo de Batalla"))
        
        # Status con HP
        hp_text = (
            f"🧙 Jugador: {self.game_engine.player_hp} HP | "
            f"👹 Enemigo: {self.game_engine.enemy_hp} HP | "
            f"Velocidad: {self.game_engine.game_speed:.1f}x"
        )
        layout["status"].update(Panel(hp_text, title="Estado"))
        
        # Hechizo actual
        spell_text = f"🔮 Grita: {self.game_engine.current_spell}"
        layout["feedback"].update(Panel(spell_text, title="Hechizo Actual"))
        
        # Feedback de última acción
        if self.feedback:
            layout["footer"].update(Panel(self.feedback, style=self.feedback_color))
        else:
            layout["footer"].update(Panel("Esperando entrada...", style="dim"))
        
        return layout
    
    def render(self) -> None:
        """Renderiza el estado actual del juego en la terminal."""
        if self.live is None:
            layout = self._generate_layout()
            self.live = Live(layout, console=self.console, refresh_per_second=30)
            self.live.start()
        else:
            layout = self._generate_layout()
            self.live.update(layout)
    
    def set_feedback(self, message: str, color: str = "white") -> None:
        """
        Establece el mensaje de feedback a mostrar.
        
        Args:
            message: Mensaje a mostrar
            color: Color del mensaje (white, green, red, yellow, cyan, etc.)
        """
        self.feedback = message
        self.feedback_color = color
        # Limpiar después de 2 segundos
        threading.Timer(2.0, lambda: setattr(self, 'feedback', '')).start()
    
    def stop(self) -> None:
        """Detiene la renderización en vivo."""
        if self.live is not None:
            self.live.stop()


class VoiceSensor:
    """
    Sensor de voz que captura entrada del micrófono en un hilo separado.
    """
    
    def __init__(self):
        """Inicializa el sensor de voz."""
        self.voice_queue = queue.Queue()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self._running = False
        self._thread = None
    
    def start(self) -> None:
        """Inicia el hilo de escucha de voz."""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
    
    def stop(self) -> None:
        """Detiene el hilo de escucha de voz."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
    
    def _listen_loop(self) -> None:
        """Loop principal que escucha el micrófono continuamente."""
        try:
            with self.microphone as source:
                # Ajustar para ruido ambiente
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("🎤 Micrófono inicializado. Listo para escuchar...")
                
                while self._running:
                    try:
                        # Escuchar con timeout de 5 segundos
                        audio = self.recognizer.listen(
                            source, 
                            timeout=5, 
                            phrase_time_limit=3
                        )
                        
                        # Reconocer con Google (requiere internet)
                        text = self.recognizer.recognize_google(
                            audio, 
                            language="es-ES"
                        )
                        
                        # Poner en la cola sin bloquear
                        self.voice_queue.put(text.lower(), block=False)
                    
                    except sr.UnknownValueError:
                        # Micrófono escuchó pero no pudo reconocer
                        pass
                    except sr.RequestError as e:
                        # Error con Google API (sin internet)
                        print(f"⚠️  Error de API: {e}")
                    except sr.WaitTimeoutError:
                        # Timeout esperando audio
                        pass
                    except queue.Full:
                        # Cola llena, descartar
                        pass
        
        except Exception as e:
            print(f"❌ Error en sensor de voz: {e}")