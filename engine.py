import random
import unicodedata
from typing import Optional


# Base de datos de hechizos por nivel de dificultad
SPELLS_DB = {
    1: [
        "Resistencia",
        "Plasticidad",
        "Cristalografía",
        "Aerodinamica",
        "Electrolito",
    ],
    2: [
        "Austenita",
        "Martensita",
        "Ferromagnetismo",
        "Piezoelectricidad",
        "Hiperboloid",
        "Tribología",
    ],
    3: [
        "Politetrafluoroetileno",
        "Bicompartimentado",
        "Fotorresistencia",
        "Estocasticidad",
        "Topología",
        "Magnetorresistencia",
    ],
}


def normalize_text(text: str) -> str:
    """
    Normaliza un texto removiendo acentos y convirtiéndolo a minúsculas.
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado sin acentos y en minúsculas
    """
    # Descomponer caracteres acentuados
    nfd = unicodedata.normalize("NFD", text)
    # Filtrar caracteres de combinación (acentos)
    sin_acentos = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return sin_acentos.lower()


class GameEngine:
    """
    Motor del juego que maneja la lógica de combate, proyectiles y hechizos.
    
    Attributes:
        player_hp: Puntos de salud del jugador (0-100)
        enemy_hp: Puntos de salud del enemigo (0-100)
        projectile_position: Distancia del proyectil (0-50)
        current_spell: Hechizo actual que el jugador debe gritar
        difficulty: Nivel de dificultad actual (1-3)
        game_speed: Multiplicador de velocidad (afecta cuánto avanza el proyectil)
    """
    
    def __init__(self, difficulty: int = 1):
        """
        Inicializa el motor del juego.
        
        Args:
            difficulty: Nivel de dificultad (1-3). Default: 1
        """
        if difficulty not in [1, 2, 3]:
            raise ValueError("La dificultad debe ser 1, 2 o 3")
        
        self.player_hp = 100
        self.enemy_hp = 100
        self.projectile_position = 50
        self.difficulty = difficulty
        self.game_speed = 1.0
        self.current_spell = self._generate_new_spell()
    
    def _generate_new_spell(self) -> str:
        """
        Genera un nuevo hechizo aleatorio del nivel de dificultad actual.
        
        Returns:
            Una palabra de hechizo aleatoria de SPELLS_DB
        """
        spells = SPELLS_DB[self.difficulty]
        return random.choice(spells)
    
    def advance_projectile(self) -> bool:
        """
        Avanza el proyectil hacia el jugador.
        
        Returns:
            True si el proyectil impactó al jugador, False en caso contrario
        """
        # Restar la velocidad actual (puede ser > 1 si se aumentó)
        self.projectile_position -= self.game_speed
        
        # Si el proyectil llega a 0 o menos, impacta al jugador
        if self.projectile_position <= 0:
            self.player_hp -= 10
            self.projectile_position = 50
            self.current_spell = self._generate_new_spell()
            return True
        
        return False
    
    def validate_voice(self, spoken_word: str) -> bool:
        """
        Valida la palabra hablada contra el hechizo actual.
        
        Si la palabra coincide (ignorando mayúsculas y acentos):
        - Resta 10 HP al enemigo
        - Resetea la posición del proyectil a 50
        - Genera un nuevo hechizo
        - Aumenta la velocidad del juego en 0.2
        
        Args:
            spoken_word: Palabra capturada del micrófono
            
        Returns:
            True si la palabra coincidió, False en caso contrario
        """
        # Normalizar ambas palabras para comparación
        spoken_normalized = normalize_text(spoken_word)
        current_spell_normalized = normalize_text(self.current_spell)
        
        if spoken_normalized == current_spell_normalized:
            # Acierto: daña al enemigo
            self.enemy_hp -= 10
            self.projectile_position = 50
            self.current_spell = self._generate_new_spell()
            self.game_speed += 0.2
            return True
        
        return False
    
    def is_game_over(self) -> bool:
        """
        Verifica si el juego ha terminado.
        
        Returns:
            True si algún participante tiene 0 o menos HP
        """
        return self.player_hp <= 0 or self.enemy_hp <= 0
    
    def get_winner(self) -> Optional[str]:
        """
        Determina el ganador del juego.
        
        Returns:
            "player" si el jugador ganó, "enemy" si el enemigo ganó, None si aún está en curso
        """
        if self.player_hp <= 0:
            return "enemy"
        elif self.enemy_hp <= 0:
            return "player"
        return None
    
    def reset(self, difficulty: int = 1) -> None:
        """
        Reinicia el juego.
        
        Args:
            difficulty: Nuevo nivel de dificultad (1-3). Default: 1
        """
        self.__init__(difficulty)
