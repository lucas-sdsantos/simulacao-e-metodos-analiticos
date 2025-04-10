import random

# Parâmetros do Gerador Congruente Linear
MULTIPLICADOR = 1664525
INCREMENTO = 1013904223
MODULO = 2**32
estado_atual = random.randint(0, MODULO - 1)

def gerar_aleatorio():
    global estado_atual
    estado_atual = (MULTIPLICADOR * estado_atual + INCREMENTO) % MODULO
    return estado_atual / MODULO

# Total de eventos a simular
NUM_EVENTOS = 100000

class Evento:
    def __init__(self, tipo, tempo, origem=None, destino=None):
        self.tipo = tipo
        self.tempo = tempo
        self.origem = origem
        self.destino = destino

    def __str__(self):
        origem_str = self.origem.__str__() if self.origem else "None"
        destino_str = self.destino.__str__() if self.destino else "None"
        return f"Evento: {self.tipo} | Tempo: {self.tempo} | Origem: {origem_str} | Destino: {destino_str}"

class Fila:
    def __init__(self, servidores, limite, servico_min, servico_max, controlador,
                 origem=None, destino=None, chegada_min=None, chegada_max=None):
        self.servidores = servidores
        self.limite = limite
        self.chegada_min = chegada_min
        self.chegada_max = chegada_max
        self.servico_min = servico_min
        self.servico_max = servico_max
        self.total_clientes = 0
        self.ocupacao = [0] * (limite + 1)
        self.perdas = 0
        self.instante = 0
        self.controlador = controlador
        self.origem = origem if origem else self
        self.destino = destino

    def chegada(self, momento):
        if self.total_clientes < self.limite:
            self.ocupacao[self.total_clientes] += self.controlador.instante - self.instante
            self.instante = momento
            self.total_clientes += 1

            if self.total_clientes <= self.servidores:
                tempo_servico = gerar_aleatorio() * (self.servico_max - self.servico_min) + self.servico_min
                self.controlador.agendar_evento(Evento('passagem', momento + tempo_servico, origem=self.origem, destino=self.destino))
        else:
            self.perdas += 1

        proxima_chegada = gerar_aleatorio() * (self.chegada_max - self.chegada_min) + self.chegada_min
        self.controlador.agendar_evento(Evento('chegada', momento + proxima_chegada, origem=self.origem))

    def passagem(self, momento, destino):
        self.origem.ocupacao[self.origem.total_clientes] += self.controlador.instante - self.origem.instante
        self.origem.instante = momento
        self.ocupacao[self.total_clientes] += self.controlador.instante - self.instante
        self.instante = momento

        self.origem.total_clientes -= 1
        if self.origem.total_clientes >= self.origem.servidores:
            novo_servico = gerar_aleatorio() * (self.servico_max - self.servico_min) + self.servico_min
            self.controlador.agendar_evento(Evento('passagem', momento + novo_servico, origem=self.origem, destino=destino))

        if self.total_clientes < self.limite:
            self.total_clientes += 1
            if self.total_clientes <= self.servidores:
                novo_saida = gerar_aleatorio() * (self.servico_max - self.servico_min) + self.servico_min
                self.controlador.agendar_evento(Evento('saida', momento + novo_saida, origem=self))
        else:
            self.perdas += 1

    def saida(self, momento):
        if self.total_clientes > 0:
            self.ocupacao[self.total_clientes] += self.controlador.instante - self.instante
            self.instante = momento
            self.total_clientes -= 1
            if self.total_clientes >= self.servidores:
                novo_saida = gerar_aleatorio() * (self.servico_max - self.servico_min) + self.servico_min
                self.controlador.agendar_evento(Evento('saida', momento + novo_saida, origem=self))

    def __str__(self):
        return f"G/G/{self.servidores}/{self.limite} | Clientes: {self.total_clientes} | Perdas: {self.perdas}"

    def relatorio(self):
        print("Distribuição de Ocupação:")
        for i, tempo in enumerate(self.ocupacao):
            print(f"{i}: {tempo / self.controlador.instante:.1%} | Tempo: {tempo}")
        print("Tempo Total:", self.controlador.instante)

class Controlador:
    def __init__(self):
        self.eventos = []
        self.instante = 0
        self.filas = []

    def adicionar_fila(self, fila):
        self.filas.append(fila)

    def agendar_evento(self, evento):
        self.eventos.append(evento)

    def executar_proximo(self):
        if not self.eventos:
            return None

        proximo = min(self.eventos, key=lambda e: e.tempo)
        self.eventos.remove(proximo)
        self.instante = proximo.tempo

        if proximo.tipo == 'chegada':
            proximo.origem.chegada(proximo.tempo)
        elif proximo.tipo == 'passagem':
            proximo.destino.passagem(proximo.tempo, destino=proximo.destino)
        elif proximo.tipo == 'saida':
            proximo.origem.saida(proximo.tempo)

def simular():
    controlador = Controlador()

    fila1 = Fila(servidores=2, limite=3, chegada_min=1, chegada_max=4, servico_min=3, servico_max=4, controlador=controlador)
    fila2 = Fila(servidores=1, limite=5, servico_min=2, servico_max=3, controlador=controlador)

    controlador.adicionar_fila(fila1)
    controlador.adicionar_fila(fila2)

    fila1.destino = fila2
    fila2.origem = fila1

    print(f"Fila1: {fila1} | Origem: {fila1.origem} | Destino: {fila1.destino}")
    print(f"Fila2: {fila2} | Origem: {fila2.origem} | Destino: {fila2.destino if fila2.destino else 'None'}")

    controlador.agendar_evento(Evento('chegada', 1.5, origem=fila1))
    for _ in range(NUM_EVENTOS):
        controlador.executar_proximo()

    print("\nSimulação Finalizada")
    print("Resultados:")
    print(fila1)
    fila1.relatorio()
    print()
    print(fila2)
    fila2.relatorio()

if __name__ == "__main__":
    simular()
