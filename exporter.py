import re
import pandas as pd
from datetime import datetime

def limpar_telefone_whatsapp(telefone: str) -> str:
    """
    Remove caracteres especiais e gera o link wa.me se houver número válido.
    """
    if not telefone or telefone == "Não informado":
        return "Sem telefone"

    # Mantém apenas os dígitos
    apenas_numeros = re.sub(r"\D", "", telefone)

    # Adiciona o DDI 55 (Brasil) se ainda não tiver
    if len(apenas_numeros) in (10, 11):
        apenas_numeros = "55" + apenas_numeros

    if len(apenas_numeros) >= 12:
        return f"https://wa.me/{apenas_numeros}"
    return "Número inválido"


def exportar_para_excel(leads: list[dict], termo_busca: str) -> str:
    """
    Recebe a lista de leads, trata os dados e exporta um Excel formatado com 2 abas.
    Retorna o nome do arquivo gerado.
    """
    if not leads:
        raise ValueError("A lista de leads está vazia. Nada para exportar.")

    df = pd.DataFrame(leads)

    # Renomeia colunas para apresentação profissional ao cliente
    df = df.rename(columns={
        "nome": "Empresa",
        "telefone": "Telefone",
        "site": "Website",
        "nota": "Avaliação Google"
    })

    # Cria coluna com link clicável de WhatsApp
    df["Link WhatsApp"] = df["Telefone"].apply(limpar_telefone_whatsapp)

    # Filtra os "Leads Quentes" (empresas que não possuem site)
    df_quentes = df[df["Website"] == "Não possui site"].copy()

    # Gera nome de arquivo limpo com data/hora
    slug_busca = re.sub(r"[^a-zA-Z0-9]+", "_", termo_busca.lower()).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    nome_arquivo = f"leads_{slug_busca}_{timestamp}.xlsx"

    # Salva no Excel com 2 abas e ajusta largura das colunas
    with pd.ExcelWriter(nome_arquivo, engine="openpyxl") as writer:
        df_quentes.to_excel(writer, sheet_name="Leads Quentes (Sem Site)", index=False)
        df.to_excel(writer, sheet_name="Base Completa", index=False)

        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for col in worksheet.columns:
                max_length = 0
                col_letter = col[0].column_letter
                for cell in col:
                    val = str(cell.value or "")
                    if len(val) > max_length:
                        max_length = len(val)
                worksheet.column_dimensions[col_letter].width = min(max_length + 4, 55)

    print(f"📊 Planilha gerada com sucesso: {nome_arquivo}")
    return nome_arquivo


if __name__ == "__main__":
    # Teste rápido isolado para validar a geração do Excel
    dados_teste = [
        {"nome": "Clínica Sorriso Real", "telefone": "(62) 99999-1234", "site": "Não possui site", "nota": "4,9"},
        {"nome": "Odonto Plus", "telefone": "(62) 3214-5678", "site": "https://odontoplus.com.br", "nota": "4,7"},
    ]
    exportar_para_excel(dados_teste, "Clinica Odontologica Goiania")