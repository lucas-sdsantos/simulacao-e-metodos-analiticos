# Simulador de Redes de Filas (v2)

Arthur Mariano Foltz Barroso, Lorenzo Duarte More e Lucas Schwartz dos Santos

Simulador em **Python 3** para redes genéricas de filas (formato G/G/s/c) usando abordagem de **eventos discretos**.  
Permite definir múltiplas estações de serviço, intervalos de chegada/atendimento uniformes e roteamento probabilístico entre filas, tudo configurado por um arquivo **YAML** simples.

---

## Principais funcionalidades
| Recurso | Descrição |
|---------|-----------|
| **Modelo G/G/s/c** | Suporta qualquer número de servidores (`s`) e capacidade (`c`). |
| **Chegadas independentes** | Cada fila pode (ou não) receber clientes externos. |
| **Roteamento probabilístico** | Probabilidade de saída ou encaminhamento para outras filas. |
| **Capacidade finita/infinita** | Clientes excedentes contam como “perdidos”. |
| **Métricas** | Distribuição de ocupação por fila, clientes perdidos e tempo total simulado. |
| **Saída em tabela** | Resultados formatados no terminal com layout legível. |

---

## Requisitos

* Python ≥ 3.8  
* [PyYAML](https://pyyaml.org/) – `pip install pyyaml`

---

## Instalação

```bash
git clone https://github.com/seu‑usuario/simulador‑filas.git
cd simulador‑filas
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt   # contém apenas pyyaml

## Executando a Simulação

Para executar a simulação:

** abra o
python t1.py config.yml
