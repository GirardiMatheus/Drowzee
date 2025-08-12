<div align="center"> <h1> <img src="drowzee.png" width="40" height="40" alt="Drowzee" style="vertical-align: middle;"> Drowzee Pomodoro </h1> <p>Pomodoro simples para Linux, inspirado no Pokémon Drowzee</p> <p> <img src="https://img.shields.io/badge/Python-3.7%2B-blue" alt="Python"> <img src="https://img.shields.io/badge/Linux-Suporte%20a%20Áudio-yellowgreen" alt="Linux"> <img src="https://img.shields.io/badge/License-MIT-green" alt="License"> </p> </div>

## Funcionalidades

- Timer de foco e descanso personalizáveis
- Interface gráfica com tema Drowzee (amarelo/marrom)
- Exibe imagem do Drowzee
- Alarme sonoro ao final do foco e do descanso (sons fixos no código)
- Suporte a arquivos de áudio `.mp3`, `.wav`, `.ogg`
- Fallback para beep do terminal caso não seja possível tocar áudio

## Pré-requisitos

- Python 3.7+
- Linux (preferencialmente com suporte a áudio)

## Instalação

1. Clone este repositório.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Coloque o arquivo de áudio `drowzee_1.mp3` na mesma pasta do `main.py`.
4. Coloque a imagem `drowzee.png` na mesma pasta do `main.py` para exibição/ícone.

## Execução

```bash
python3 main.py
```

## Observações

- O áudio será tocado usando `paplay`, `aplay` ou `simpleaudio` (com fallback para beep do terminal).
- Se estiver em WSL, container ou servidor remoto, pode não haver suporte a áudio.
- O beep do terminal depende da configuração do seu sistema/terminal.

---
