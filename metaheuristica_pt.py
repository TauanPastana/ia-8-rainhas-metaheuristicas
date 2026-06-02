import argparse
import csv
import math
import random
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean, pstdev

N = 8

DIRETORIO_SAIDA = Path("output")
DIRETORIO_SAIDA.mkdir(exist_ok=True)

@dataclass
class ResultadoExecucao:
    algoritmo: str
    id_execucao: int
    tempo_segundos: float
    iteracoes: int
    melhor_solucao: str
    conflitos_finais: int
    sucesso: int
    fitness_final: float

def contar_conflitos(tabuleiro):
    conflitos = 0
    for i in range(N):
        for j in range(i + 1, N):
            mesma_linha = tabuleiro[i] == tabuleiro[j]
            mesma_diagonal = abs(tabuleiro[i] - tabuleiro[j]) == abs(i - j)
            if mesma_linha or mesma_diagonal:
                conflitos += 1
    return conflitos

def fitness_a_partir_de_conflitos(conflitos):
    return 1 / (1 + conflitos)

def tabuleiro_aleatorio():
    return [random.randint(0, N - 1) for _ in range(N)]

def tabuleiro_para_binario(tabuleiro):
    bits = []
    for linha in tabuleiro:
        bits.extend(int(b) for b in format(linha, "03b"))
    return bits

def binario_para_tabuleiro(bits):
    tabuleiro = []
    for i in range(0, len(bits), 3):
        trecho = bits[i:i + 3]
        if len(trecho) < 3:
            trecho = trecho + [0] * (3 - len(trecho))
        linha = int("".join(str(b) for b in trecho), 2) % N
        tabuleiro.append(linha)
    return tabuleiro[:N]

def tabuleiro_para_string(tabuleiro):
    return "[" + ", ".join(map(str, tabuleiro)) + "]"

def melhores_solucaoes_distintas(resultados, top_k=5):
    vistos = set()
    melhores = []
    for r in sorted(resultados, key=lambda x: (x["conflitos_finais"], x["tempo_segundos"])):
        s = r["melhor_solucao"]
        if s not in vistos:
            vistos.add(s)
            melhores.append(r)
        if len(melhores) == top_k:
            break
    return melhores

def construcao_gulosa_randomizada(tamanho_rcl):
    tabuleiro = [-1] * N
    for coluna in range(N):
        candidatos = []
        for linha in range(N):
            tabuleiro[coluna] = linha
            conflitos = 0
            for coluna_anterior in range(coluna):
                if tabuleiro[coluna_anterior] == linha or abs(tabuleiro[coluna_anterior] - linha) == abs(coluna_anterior - coluna):
                    conflitos += 1
            candidatos.append((conflitos, linha))
        candidatos.sort(key=lambda x: x[0])
        rcl = candidatos[:max(1, min(tamanho_rcl, len(candidatos)))]
        tabuleiro[coluna] = random.choice(rcl)[1]
    return tabuleiro

def busca_local(tabuleiro):
    atual = tabuleiro[:]
    conflitos_atual = contar_conflitos(atual)
    melhorou = True
    while melhorou:
        melhorou = False
        melhor_tabuleiro = atual[:]
        melhor_conflitos = conflitos_atual
        for coluna in range(N):
            original = atual[coluna]
            for linha in range(N):
                if linha == original:
                    continue
                candidato = atual[:]
                candidato[coluna] = linha
                c = contar_conflitos(candidato)
                if c < melhor_conflitos:
                    melhor_conflitos = c
                    melhor_tabuleiro = candidato[:]
                    melhorou = True
        atual = melhor_tabuleiro
        conflitos_atual = melhor_conflitos
    return atual

def grasp(max_iterations=200, rcl_size=3):
    inicio = time.perf_counter()
    melhor_tabuleiro = None
    melhores_conflitos = math.inf
    iteracoes_usadas = 0
    for it in range(max_iterations):
        iteracoes_usadas = it + 1
        candidato = construcao_gulosa_randomizada(rcl_size)
        candidato = busca_local(candidato)
        conflitos = contar_conflitos(candidato)
        if conflitos < melhores_conflitos:
            melhores_conflitos = conflitos
            melhor_tabuleiro = candidato[:]
        if melhores_conflitos == 0:
            break
    tempo_decorrido = time.perf_counter() - inicio
    return {
        "algoritmo": "GRASP",
        "tempo_segundos": tempo_decorrido,
        "iteracoes": iteracoes_usadas,
        "melhor_solucao": melhor_tabuleiro,
        "conflitos_finais": melhores_conflitos,
        "fitness_final": fitness_a_partir_de_conflitos(melhores_conflitos),
        "sucesso": int(melhores_conflitos == 0),
    }

def individuo_binario_aleatorio():
    return tabuleiro_para_binario(tabuleiro_aleatorio())

def selecao_roleta(populacao, aptidoes):
    total = sum(aptidoes)
    if total == 0:
        return random.choice(populacao)
    escolha = random.uniform(0, total)
    acumulado = 0
    for individuo, aptidao in zip(populacao, aptidoes):
        acumulado += aptidao
        if acumulado >= escolha:
            return individuo
    return populacao[-1]

def cruzamento_um_ponto(p1, p2):
    ponto = random.randint(1, len(p1) - 1)
    return p1[:ponto] + p2[ponto:]

def mutar(individuo, taxa_mutacao):
    mutado = individuo[:]
    for i in range(len(mutado)):
        if random.random() < taxa_mutacao:
            mutado[i] = 1 - mutado[i]
    return mutado

def algoritmo_genetico(tamanho_populacao=20, taxa_cruzamento=0.80, taxa_mutacao=0.03, max_geracoes=1000):
    inicio = time.perf_counter()
    populacao = [individuo_binario_aleatorio() for _ in range(tamanho_populacao)]
    melhor_solucao = None
    melhores_conflitos = math.inf
    geracoes_usadas = 0
    for geracao in range(max_geracoes):
        geracoes_usadas = geracao + 1
        decodificados = [binario_para_tabuleiro(ind) for ind in populacao]
        lista_conflitos = [contar_conflitos(tabuleiro) for tabuleiro in decodificados]
        aptidoes = [fitness_a_partir_de_conflitos(c) for c in lista_conflitos]
        melhor_idx = min(range(len(lista_conflitos)), key=lambda i: lista_conflitos[i])
        if lista_conflitos[melhor_idx] < melhores_conflitos:
            melhores_conflitos = lista_conflitos[melhor_idx]
            melhor_solucao = decodificados[melhor_idx][:]
        if melhores_conflitos == 0:
            break
        elite_count = max(1, tamanho_populacao // 5)
        elite_indices = sorted(range(tamanho_populacao), key=lambda i: lista_conflitos[i])[:elite_count]
        nova_populacao = [populacao[i][:] for i in elite_indices]
        while len(nova_populacao) < tamanho_populacao:
            pai1 = selecao_roleta(populacao, aptidoes)
            pai2 = selecao_roleta(populacao, aptidoes)
            filho = pai1[:]
            if random.random() < taxa_cruzamento:
                filho = cruzamento_um_ponto(pai1, pai2)
            filho = mutar(filho, taxa_mutacao)
            nova_populacao.append(filho)
        populacao = nova_populacao
    tempo_decorrido = time.perf_counter() - inicio
    return {
        "algoritmo": "GA",
        "tempo_segundos": tempo_decorrido,
        "iteracoes": geracoes_usadas,
        "melhor_solucao": melhor_solucao,
        "conflitos_finais": melhores_conflitos,
        "fitness_final": fitness_a_partir_de_conflitos(melhores_conflitos),
        "sucesso": int(melhores_conflitos == 0),
    }

def executar_experimentos(execucao_total, iteracoes_grasp, tamanho_rcl, tamanho_populacao, taxa_cruzamento, taxa_mutacao, max_geracoes):
    resultados = []
    for i in range(1, execucao_total + 1):
        r = grasp(iteracoes_grasp, tamanho_rcl)
        resultados.append(ResultadoExecucao(
            algoritmo=r["algoritmo"],
            id_execucao=i,
            tempo_segundos=r["tempo_segundos"],
            iteracoes=r["iteracoes"],
            melhor_solucao=tabuleiro_para_string(r["melhor_solucao"]),
            conflitos_finais=r["conflitos_finais"],
            fitness_final=r["fitness_final"],
            sucesso=r["sucesso"]
        ))
    for i in range(1, execucao_total + 1):
        r = algoritmo_genetico(tamanho_populacao, taxa_cruzamento, taxa_mutacao, max_geracoes)
        resultados.append(ResultadoExecucao(
            algoritmo=r["algoritmo"],
            id_execucao=i,
            tempo_segundos=r["tempo_segundos"],
            iteracoes=r["iteracoes"],
            melhor_solucao=tabuleiro_para_string(r["melhor_solucao"]),
            conflitos_finais=r["conflitos_finais"],
            fitness_final=r["fitness_final"],
            sucesso=r["sucesso"]
        ))
    return resultados

def resumir(resultados):
    resumo = []
    for alg in sorted(set(r.algoritmo for r in resultados)):
        resultados_alg = [r for r in resultados if r.algoritmo == alg]
        tempos = [r.tempo_segundos for r in resultados_alg]
        iteracoes = [r.iteracoes for r in resultados_alg]
        conflitos = [r.conflitos_finais for r in resultados_alg]
        fitness = [r.fitness_final for r in resultados_alg]
        taxa_sucesso = sum(r.sucesso for r in resultados_alg) / len(resultados_alg)
        resumo.append({
            "algoritmo": alg,
            "execucoes": len(resultados_alg),
            "media_tempo_segundos": mean(tempos),
            "desvio_padrao_tempo_segundos": pstdev(tempos) if len(tempos) > 1 else 0.0,
            "media_iteracoes": mean(iteracoes),
            "desvio_padrao_iteracoes": pstdev(iteracoes) if len(iteracoes) > 1 else 0.0,
            "taxa_sucesso": taxa_sucesso,
            "media_conflitos_finais": mean(conflitos),
            "media_fitness_final": mean(fitness),
            "melhor_conflitos": min(conflitos),
            "pior_conflitos": max(conflitos),
        })
    return resumo

def salvar_resultados_csv(resultados, nome_arquivo="results.csv"):
    caminho = DIRETORIO_SAIDA / nome_arquivo
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(asdict(resultados[0]).keys()))
        escritor.writeheader()
        for r in resultados:
            escritor.writerow(asdict(r))
    return caminho

def salvar_resumo_csv(resumo, nome_arquivo="summary.csv"):
    caminho = DIRETORIO_SAIDA / nome_arquivo
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(resumo[0].keys()))
        escritor.writeheader()
        for linha in resumo:
            escritor.writerow(linha)
    return caminho

def salvar_melhores_solucoes_por_algoritmo_csv(resultados, nome_arquivo="top_solutions_by_algorithm.csv", top_k=5):
    caminho = DIRETORIO_SAIDA / nome_arquivo
    linhas = []
    algoritmos = sorted(set(r.algoritmo for r in resultados))
    for alg in algoritmos:
        resultados_alg = [r.__dict__ for r in resultados if r.algoritmo == alg]
        melhores = melhores_solucaoes_distintas(resultados_alg, top_k=top_k)
        linhas.extend(melhores)
    campos = [
        "algoritmo",
        "id_execucao",
        "tempo_segundos",
        "iteracoes",
        "melhor_solucao",
        "conflitos_finais",
        "fitness_final",
        "sucesso",
    ]
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow(linha)
    return caminho

def argumentos():
    parser = argparse.ArgumentParser(description="8 Rainhas: GRASP e Algoritmo Genético")
    parser.add_argument("--execucoes", type=int, default=50)
    parser.add_argument("--iteracoes-grasp", type=int, default=200)
    parser.add_argument("--tamanho-rcl", type=int, default=3)
    parser.add_argument("--populacao", type=int, default=20)
    parser.add_argument("--taxa-cruzamento", type=float, default=0.80)
    parser.add_argument("--taxa-mutacao", type=float, default=0.03)
    parser.add_argument("--max-geracoes", type=int, default=1000)
    return parser.parse_args()

def main():
    args = argumentos()
    resultados = executar_experimentos(
        execucao_total=args.execucoes,
        iteracoes_grasp=args.iteracoes_grasp,
        tamanho_rcl=args.tamanho_rcl,
        tamanho_populacao=args.populacao,
        taxa_cruzamento=args.taxa_cruzamento,
        taxa_mutacao=args.taxa_mutacao,
        max_geracoes=args.max_geracoes,
    )
    resumo = resumir(resultados)
    caminho_resultados = salvar_resultados_csv(resultados)
    caminho_resumo = salvar_resumo_csv(resumo)
    caminho_top = salvar_melhores_solucoes_por_algoritmo_csv(resultados)
    print("Saved:", caminho_resultados)
    print("Saved:", caminho_resumo)
    print("Saved:", caminho_top)
    for linha in resumo:
        print(linha)

if __name__ == "__main__":
    main()
