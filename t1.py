from __future__ import annotations

import heapq
from argparse import ArgumentParser
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

# Arthur Mariano Foltz Barroso, Lorenzo Duarte More e Lucas Schwartz dos Santos

# ==========================================================================
# Modelos de dados
# ==========================================================================

@dataclass(slots=True)
class Cliente:
    id: int
    tempo_chegada: float
    fila_atual: str
    proxima_fila: Optional[str] = None


class GeradorLCG:
    def __init__(self, seed: int = 1, a: int = 1_664_525, c: int = 1_013_904_223, m: int = 2**32) -> None:
        self._estado = seed
        self._a = a
        self._c = c
        self._m = m

    def random(self) -> float:
        self._estado = (self._a * self._estado + self._c) % self._m
        return self._estado / self._m


class Fila:
    def __init__(self, nome: str, cfg: Dict) -> None:
        self.nome = nome
        self.tipo = cfg["tipo"]

        partes = self.tipo.split("/")
        self.num_servidores = int(partes[2]) if len(partes) > 2 else 1
        self.capacidade = int(partes[3]) if len(partes) > 3 else float("inf")

        chegada_cfg = cfg.get("chegada_intervalo", {})
        self.arrival_min = chegada_cfg.get("minimo", 0.0)
        self.arrival_max = chegada_cfg.get("maximo", 0.0)

        serv_cfg = cfg["servico_intervalo"]
        self.service_min = serv_cfg["minimo"]
        self.service_max = serv_cfg["maximo"]

        self.destino: Dict[str, float] = cfg.get("destino", {})

        self.fila: List[Cliente] = []
        self.servidores: List[Tuple[Optional[Cliente], float]] = [(None, 0.0)] * self.num_servidores
        self.clientes_perdidos = 0
        self.tempo_em_estado: defaultdict[int, float] = defaultdict(float)
        self.ultimo_tempo_evento = 0.0

        self.rand = GeradorLCG()

    def _unif(self, lo: float, hi: float) -> float:
        return lo + (hi - lo) * self.rand.random()

    def tempo_servico(self) -> float:
        return self._unif(self.service_min, self.service_max)

    def proxima_chegada(self, now: float) -> float:
        if self.arrival_min == self.arrival_max == 0.0:
            return float("inf")
        return now + self._unif(self.arrival_min, self.arrival_max)

    def escolher_destino(self) -> Optional[str]:
        return next(iter(self.destino.keys())) if self.destino else None


# ==========================================================================
# Agenda de eventos
# ==========================================================================

@dataclass(order=True, slots=True)
class Evento:
    tempo: float
    tipo: str
    fila: str
    cliente: Optional[Cliente] = None


# ==========================================================================
# Núcleo da simulação
# ==========================================================================

class SimuladorRede:
    def __init__(self, arquivo_cfg: str | Path, num_eventos: int = 100_000) -> None:
        self.cfg_path = Path(arquivo_cfg)
        self.num_eventos = num_eventos

        with self.cfg_path.open("r", encoding="utf-8") as fp:
            cfg = yaml.safe_load(fp)

        self.filas: Dict[str, Fila] = {n: Fila(n, fcfg) for n, fcfg in cfg["filas"].items()}
        self.eventos: List[Evento] = []
        self.relogio = 0.0
        self._contador = 0

        for nome, fila in self.filas.items():
            if fila.arrival_min or fila.arrival_max:
                self._agenda(Evento(fila.proxima_chegada(0.0), "chegada", nome))

    # ---------- agenda ---------- #
    def _agenda(self, ev: Evento) -> None:
        heapq.heappush(self.eventos, ev)

    def _next(self) -> Evento:
        return heapq.heappop(self.eventos)

    # ---------- estatísticas ---------- #
    def _acumula(self, dt: float) -> None:
        for fila in self.filas.values():
            espera = len(fila.fila)
            serv   = sum(1 for c, _ in fila.servidores if c)
            fila.tempo_em_estado[espera + serv] += dt
            fila.ultimo_tempo_evento = self.relogio

    # ---------- handlers ---------- #
    def _chegada(self, f: str, cli: Optional[Cliente]) -> None:
        fila = self.filas[f]
        if cli is None:
            self._contador += 1
            cli = Cliente(self._contador, self.relogio, f, fila.escolher_destino())
        else:
            cli.fila_atual = f
            cli.proxima_fila = fila.escolher_destino()

        if len(fila.fila) >= fila.capacidade:
            fila.clientes_perdidos += 1
            return

        fila.fila.append(cli)

        if fila.arrival_min or fila.arrival_max:
            self._agenda(Evento(fila.proxima_chegada(self.relogio), "chegada", f))

        for idx, (oc, _) in enumerate(fila.servidores):
            if oc is None:
                self._inicio_serv(f, idx)
                break

    def _inicio_serv(self, f: str, idx: int) -> None:
        fila = self.filas[f]
        if not fila.fila:
            return
        cli = fila.fila.pop(0)
        ts = fila.tempo_servico()
        fila.servidores[idx] = (cli, self.relogio + ts)
        self._agenda(Evento(self.relogio + ts, "partida", f, cli))

    def _partida(self, f: str, cli: Cliente) -> None:
        fila = self.filas[f]
        for idx, (oc, _) in enumerate(fila.servidores):
            if oc and oc.id == cli.id:
                fila.servidores[idx] = (None, 0.0)
                break
        if cli.proxima_fila:
            self._chegada(cli.proxima_fila, Cliente(cli.id, self.relogio, cli.proxima_fila))
        for idx, (oc, _) in enumerate(fila.servidores):
            if oc is None:
                self._inicio_serv(f, idx)

    # ---------- execução ---------- #
    def rodar(self) -> None:
        proc = 0
        while proc < self.num_eventos and self.eventos:
            ev = self._next()
            dt = ev.tempo - self.relogio
            self.relogio = ev.tempo
            self._acumula(dt)
            if ev.tipo == "chegada":
                self._chegada(ev.fila, ev.cliente)
            else:
                self._partida(ev.fila, ev.cliente)  # ev.tipo == 'partida'
            proc += 1
        self._mostrar()

    # ---------- saída ---------- #
    def _mostrar(self) -> None:
        cabecalho = f"{'Fila':<8}│{'Tipo':^12}│{'Perdidos':^9}│  Distribuição de Tempo em Estados (%)"
        separador = "-" * len(cabecalho)

        for nome, fila in self.filas.items():
            print(cabecalho)
            print(separador)

            tot = sum(fila.tempo_em_estado.values())
            dist = " ".join(
                f"E{estado}:{(tempo / tot * 100):5.1f}%"
                if tot else
                f"E{estado}: --.-%"
                for estado, tempo in sorted(fila.tempo_em_estado.items())
            )

            print(f"{nome:<8}│{fila.tipo:^12}│{fila.clientes_perdidos:^9}│ {dist}\n")

        print(f"Tempo total simulado: {self.relogio:.2f} unidades de tempo")



# ==========================================================================
# CLI
# ==========================================================================

def main(argv: List[str] | None = None) -> None:
    p = ArgumentParser(description="Simulador de filas (v2)")
    p.add_argument("config")
    p.add_argument("-n", "--num-events", type=int, default=100_000)
    args = p.parse_args(argv)

    SimuladorRede(args.config, args.num_events).rodar()


if __name__ == "__main__":
    main()
