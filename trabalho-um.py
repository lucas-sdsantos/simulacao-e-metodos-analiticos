import random
import sys
from typing import Dict, List, Tuple, Set

# Constante para representar saída da rede
EXIT_NODE = "__EXIT__"

rndnumbers = [
    0.2176, 0.0103, 0.1109, 0.3456, 0.9910, 0.2323, 0.9211, 0.0322,
    0.1211, 0.5131, 0.7208, 0.9172, 0.9922, 0.8324, 0.5011, 0.2931
]

# Função para gerar valores aleatórios a partir da lista rndnumbers
def generate_random(min_value, max_value):
    """
    Generates a random value within the range [min_value, max_value]
    using the next value from the rndnumbers list.

    Parameters:
    min_value (float): The minimum value of the range.
    max_value (float): The maximum value of the range.

    Returns:
    float: A value within the range [min_value, max_value], or None if the list is empty.
    """
    if not rndnumbers:
        return None  # Indica que a lista está vazia

    # Pega o próximo valor da lista e remove-o
    normalized_value = rndnumbers.pop(0)
    return denormalize_value(normalized_value, min_value, max_value)

# Função de desnormalização para um único valor
def denormalize_value(value, min_value, max_value):
    """
    Transforms a normalized value (0 to 1) into a specified range.

    Parameters:
    value (float): A value between 0 and 1 to be transformed.
    min_value (float): The minimum value of the target range.
    max_value (float): The maximum value of the target range.

    Returns:
    float: The value transformed to the range [min_value, max_value].
    """
    return min_value + value * (max_value - min_value)

class Evento:
    def __init__(self, tipo, tempo, cliente=None, origem=None, destino=None):
        self.tipo = tipo
        self.tempo = tempo
        self.cliente = cliente
        self.origem = origem
        self.destino = destino

    def __str__(self):
        return f"Evento: {self.tipo} | Tempo: {self.tempo} | Cliente: {self.cliente} | Origem: {self.origem} | Destino: {self.destino}"

class Fila:
    def __init__(self, name, servidores, limite, servico_min, servico_max, chegada_min=None, chegada_max=None):
        self.name = name
        self.servidores = servidores
        self.limite = limite
        self.servico_min = servico_min
        self.servico_max = servico_max
        self.chegada_min = chegada_min
        self.chegada_max = chegada_max
        self.total_clientes = 0
        self.ocupacao = [0] * limite  # Tempo acumulado em cada estado
        self.perdas = 0
        self.instante = 0
        self.possible_destinations = {}
        self.saidas = 0

    def add_possible_destination(self, dest, prob):
        self.possible_destinations[dest] = prob

    def get_next_destination(self):
        rand = generate_random(0, 1)
        cumulative = 0
        for dest, prob in self.possible_destinations.items():
            cumulative += prob
            if rand <= cumulative:
                return dest
        return EXIT_NODE

    def chegada(self, momento, controlador, cliente):
        # Atualizar tempo acumulado no estado atual
        self.ocupacao[self.total_clientes] += momento - self.instante
        self.instante = momento

        if self.total_clientes < self.limite:
            self.total_clientes += 1

            if self.total_clientes <= self.servidores:
                tempo_servico = generate_random(self.servico_min, self.servico_max)
                controlador.agendar_evento(Evento('saida', momento + tempo_servico, cliente=cliente, origem=self))
        else:
            self.perdas += 1

    def saida(self, momento, controlador, cliente):
        # Atualizar tempo acumulado no estado atual
        self.ocupacao[self.total_clientes] += momento - self.instante
        self.instante = momento

        if self.total_clientes > 0:
            self.total_clientes -= 1

            if self.total_clientes >= self.servidores:
                tempo_servico = generate_random(self.servico_min, self.servico_max)
                controlador.agendar_evento(Evento('saida', momento + tempo_servico, cliente=cliente, origem=self))

            next_dest = self.get_next_destination()
            if next_dest == EXIT_NODE:
                self.saidas += 1
            else:
                controlador.agendar_evento(Evento('chegada', momento, cliente=cliente, origem=self, destino=next_dest))

    def relatorio(self, tempo_total):
        print(f"\nQueue: {self.name} (G/G/{self.servidores}/{self.limite})")
        print(f"Arrival: {self.chegada_min} ... {self.chegada_max}")
        print(f"Service: {self.servico_min} ... {self.servico_max}")
        print("*" * 50)
        print(f"{'State':>6} {'Time':>20} {'Probability':>20}")
        for i, tempo in enumerate(self.ocupacao):
            probabilidade = (tempo / tempo_total) * 100 if tempo_total > 0 else 0
            print(f"{i:>6} {tempo:>20.4f} {probabilidade:>19.2f}%")
        print(f"\nNumber of losses: {self.perdas}")

    def __str__(self):
        return f"Fila {self.name} | Clientes: {self.total_clientes} | Perdas: {self.perdas} | Saídas: {self.saidas}"

class Controlador:
    def __init__(self):
        self.eventos = []
        self.instante = 0
        self.filas = {}

    def adicionar_fila(self, fila):
        self.filas[fila.name] = fila

    def agendar_evento(self, evento):
        self.eventos.append(evento)

    def executar_proximo(self):
        if not self.eventos:
            return None

        proximo = min(self.eventos, key=lambda e: e.tempo)
        self.eventos.remove(proximo)
        self.instante = proximo.tempo

        if proximo.tipo == 'nova_chegada':  # Cliente novo entrando na rede
            proximo.destino.chegada(proximo.tempo, self, proximo.cliente)
            # Agendar próxima chegada de cliente novo, se aplicável
            if proximo.destino.chegada_min is not None and proximo.destino.chegada_max is not None:
                tempo_proxima_chegada = generate_random(proximo.destino.chegada_min, proximo.destino.chegada_max)
                if tempo_proxima_chegada is None:
                    print("A lista de números aleatórios acabou. Finalizando a simulação...")
                    return False  # Indica que a simulação deve parar
                novo_cliente = Cliente(id=len(self.eventos) + 1)
                self.agendar_evento(Evento('nova_chegada', self.instante + tempo_proxima_chegada, cliente=novo_cliente, destino=proximo.destino))
        elif proximo.tipo == 'chegada':  # Transição entre filas
            destino_fila = self.filas.get(proximo.destino)  # Buscar a instância da fila
            if destino_fila:
                destino_fila.chegada(proximo.tempo, self, proximo.cliente)
        elif proximo.tipo == 'saida':
            proximo.origem.saida(proximo.tempo, self, proximo.cliente)

        return True  # Indica que a simulação deve continuar

    def simular(self):
        while rndnumbers:  # Continua enquanto houver números na lista
            if not self.executar_proximo():
                break  # Finaliza a simulação se não houver mais eventos

class Cliente:
    def __init__(self, id):
        self.id = id
        self.historico = []

    def registrar_passagem(self, fila, tempo):
        self.historico.append((fila, tempo))

def simular(tempo_primeira_chegada):
    controlador = Controlador()

    # Configuração das filas
    fila1 = Fila(name="F1", servidores=2, limite=3, servico_min=3, servico_max=4, chegada_min=1, chegada_max=5)
    fila2 = Fila(name="F2", servidores=1, limite=5, servico_min=2, servico_max=3)  # Sem chegada_min e chegada_max

    # Configuração das probabilidades de transição
    fila1.add_possible_destination("F2", 0.7)
    fila1.add_possible_destination(EXIT_NODE, 0.3)
    fila2.add_possible_destination(EXIT_NODE, 1.0)

    # Adicionar filas ao controlador
    controlador.adicionar_fila(fila1)
    controlador.adicionar_fila(fila2)

    # Agendar evento inicial de chegada de cliente novo
    cliente = Cliente(id=1)
    controlador.agendar_evento(Evento('nova_chegada', tempo_primeira_chegada, cliente=cliente, destino=fila1))

    # Executar simulação
    controlador.simular()

    # Resultados
    print("\nSimulação Finalizada")
    tempo_total = controlador.instante
    fila1.relatorio(tempo_total)
    fila2.relatorio(tempo_total)

if __name__ == "__main__":
    # Defina o tempo da primeira chegada
    tempo_primeira_chegada = 2.0  # Exemplo: o primeiro cliente chega no tempo 2.5
    simular(tempo_primeira_chegada)