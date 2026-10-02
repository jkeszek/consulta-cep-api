from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import re

app = FastAPI(
    title="API Consulta CEP",
    description="API principal para consulta e gerenciamento de endereços.",
    version="1.0.0"
)

API_HISTORICO = "http://historico-api:8001"


class Endereco(BaseModel):
    cep: str
    logradouro: str = ""
    bairro: str = ""
    cidade: str = ""
    uf: str = ""


@app.get("/")
def inicio():
    return {"mensagem": "API Consulta CEP funcionando!"}


# CONSULTAR CEP NO VIACEP E SALVAR NO HISTÓRICO
@app.get("/cep/{cep}")
async def consultar_cep(cep: str):

    cep_limpo = re.sub(r"\D", "", cep)

    if len(cep_limpo) != 8:
        raise HTTPException(
            status_code=400,
            detail="CEP inválido. Informe um CEP com 8 números."
        )

    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"

    try:
        async with httpx.AsyncClient() as client:
            resposta = await client.get(url)

        if resposta.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="Erro ao consultar o ViaCEP."
            )

        dados = resposta.json()

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível acessar o ViaCEP."
        )

    if dados.get("erro"):
        raise HTTPException(
            status_code=404,
            detail="CEP não encontrado."
        )

    endereco = {
        "cep": dados.get("cep"),
        "logradouro": dados.get("logradouro"),
        "bairro": dados.get("bairro"),
        "cidade": dados.get("localidade"),
        "uf": dados.get("uf")
    }

    try:
        async with httpx.AsyncClient() as client:
            resposta_historico = await client.post(
                f"{API_HISTORICO}/historico",
                json=endereco
            )

        if resposta_historico.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="CEP encontrado, mas não foi possível salvar no histórico."
            )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="API de Histórico indisponível."
        )

    return {
        "mensagem": "CEP consultado e salvo no histórico com sucesso.",
        "endereco": endereco
    }


# LISTAR HISTÓRICO
@app.get("/historico")
async def listar_historico():

    try:
        async with httpx.AsyncClient() as client:
            resposta = await client.get(
                f"{API_HISTORICO}/historico"
            )

        return resposta.json()

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="API de Histórico indisponível."
        )


# CADASTRAR ENDEREÇO MANUALMENTE
@app.post("/historico")
async def adicionar_endereco(endereco: Endereco):

    try:
        async with httpx.AsyncClient() as client:
            resposta = await client.post(
                f"{API_HISTORICO}/historico",
                json=endereco.model_dump()
            )

        return resposta.json()

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="API de Histórico indisponível."
        )


# ATUALIZAR ENDEREÇO
@app.put("/historico/{id}")
async def atualizar_endereco(id: int, endereco: Endereco):

    try:
        async with httpx.AsyncClient() as client:
            resposta = await client.put(
                f"{API_HISTORICO}/historico/{id}",
                json=endereco.model_dump()
            )

        if resposta.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Endereço não encontrado."
            )

        return resposta.json()

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="API de Histórico indisponível."
        )


# EXCLUIR ENDEREÇO
@app.delete("/historico/{id}")
async def excluir_endereco(id: int):

    try:
        async with httpx.AsyncClient() as client:
            resposta = await client.delete(
                f"{API_HISTORICO}/historico/{id}"
            )

        if resposta.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Endereço não encontrado."
            )

        return resposta.json()

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="API de Histórico indisponível."
        )