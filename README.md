# pylibevp

`pylibevp` é um pequeno wrapper Python para a biblioteca C++ [dvsku/libevp](https://github.com/dvsku/libevp), usada para compactar e descompactar arquivos `.evp` do Talisman Online.

## O que faz

- compacta arquivos `.evp`
- descompacta arquivos `.evp`
- expõe a biblioteca nativa para Python através de uma API simples com `ctypes`

## Instalação

Instale a partir da wheel publicada:

```bash
python -m pip install --upgrade "https://github.com/eudivanmelo/pylibevp/releases/download/v0.1.0/pylibevp-0.1.0-py3-none-any.whl"
```

## Biblioteca nativa

O pacote já inclui o wrapper nativo da plataforma alvo. Se você compilar o projeto a partir do código-fonte, a biblioteca nativa requer C++20.

## Limitações

- A validação de arquivos no formato v2 é limitada porque alguns arquivos de modelo, textura e cenário são criptografados.
- Essa criptografia extra fica fora do escopo desta biblioteca.

## Origem

Este projeto é apenas um wrapper Python para o código-base `libevp`. Os detalhes originais do projeto nativo e do suporte aos formatos estão documentados no repositório upstream.
