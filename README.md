# IA 8 Rainhas - Metaheurísticas

Repositório do projeto: [https://github.com/TauanPastana/ia-8-rainhas-metaheuristicas.git](https://github.com/TauanPastana/ia-8-rainhas-metaheuristicas.git)

Este projeto automatiza experimentos para o problema das 8 rainhas usando n8n e Python.

O workflow:
- recebe parâmetros por formulário;
- executa automaticamente os algoritmos;
- registra os resultados em arquivos estruturados;
- retorna um resumo final da execução.

## Requisitos

Antes de testar, verifique se você tem:

- Git instalado.
- Docker instalado.
- Docker Compose instalado.
- Navegador web.
- n8n executando localmente via Docker.

## Como obter o projeto

Clone o repositório:

```bash
git clone https://github.com/TauanPastana/ia-8-rainhas-metaheuristicas.git
cd ia-8-rainhas-metaheuristicas
```

## Como subir o ambiente

Na pasta do projeto, execute:

```bash
docker compose up -d
```

Se o seu ambiente usar o comando antigo, também pode funcionar:

```bash
docker-compose up -d
```

Depois, acesse o n8n no navegador:

```text
http://localhost:5678
```

## Como importar o workflow

1. Abra o n8n no navegador.
2. Vá em **Workflows**.
3. Clique em **Import from File**.
4. Selecione o arquivo JSON do workflow.
5. Salve o workflow importado.

## Como testar o workflow



1. Abra o workflow.
2. Clique no node **Form Trigger**.
3. Clique em **Execute Workflow**.
4. Se o formulário não abrir automaticamente, use o **Test URL** mostrado no node.
5. Preencha os campos e envie o formulário.



## Campos do formulário

Os parâmetros variáveis do experimento são:

- `execucoes`
- `iteracoes_grasp`
- `tamanho_rcl`
- `populacao`
- `taxa_cruzamento`
- `taxa_mutacao`
- `max_geracoes`

Esses campos alimentam o comando executado pelo workflow.

## O que acontece após o envio

Ao enviar o formulário, o workflow:

1. lê os parâmetros informados;
2. executa o script Python;
3. salva os resultados em arquivos CSV;
4. retorna um JSON final com resumo da execução.

## Arquivos gerados

Os resultados são salvos na pasta de saída do projeto:

- `results.csv`
- `summary.csv`
- `top_solutions_by_algorithm.csv`

## Como testar o Python manualmente

Se quiser validar o script sem usar o n8n, entre no container:

```bash
docker exec -it n8n sh
```

Depois vá até a pasta do projeto e execute:

```bash
cd /home/node/.n8n-files
python3 metaheuristica.py --execucoes 1
```

Você também pode rodar com os parâmetros desejados:

```bash
python3 metaheuristica.py \
  --execucoes 50 \
  --iteracoes-grasp 200 \
  --tamanho-rcl 3 \
  --populacao 20 \
  --taxa-cruzamento 0.8 \
  --taxa-mutacao 0.03 \
  --max-geracoes 1000
```

## Como conferir se deu certo

O workflow foi executado corretamente se:

- o Form Trigger abrir ou mostrar o Test URL;
- o formulário aceitar os parâmetros;
- o node final retornar um JSON com sucesso/falha e resumo;
- os arquivos CSV aparecerem na pasta de saída.

## Observações importantes

- Se o formulário não abrir automaticamente, use o Test URL manualmente.
- Se estiver em produção, o workflow precisa estar ativado para a Production URL funcionar.
- Se você alterar apenas o Python, geralmente basta salvar o arquivo e rodar de novo.
- Se mudar variáveis do Docker ou caminhos de volume, reinicie o container.

## Estrutura esperada

- `docker-compose.yml`
- `metaheuristica.py`
- `workflow.json`
- `README.md`
- pasta `output/` com os arquivos gerados