from datetime import date, timedelta
import requests
import zipfile
import os
import xml.etree.ElementTree as ET
import smtplib
from email.message import EmailMessage

# =========================
# CONFIGURAÇÕES
# =========================
LOGIN_IN = "jpribeirogava@gmail.com"
SENHA_IN = os.getenv("SENHA_IN")

EMAIL_REMETENTE = "jpribeirogava@gmail.com"
SENHA_APP = os.getenv("SENHA_APP")
EMAIL_DESTINO = "jpgr03062003@gmail.com"

TIPO_DOU = "DO1 DO1E"
TERMO = "UNIVERSIDADE TECNOLÓGICA FEDERAL DO PARANÁ"

URL_LOGIN = "https://inlabs.in.gov.br/logar.php"
URL_DOWNLOAD = "https://inlabs.in.gov.br/index.php?p="

# =========================
# DATA (DIA ANTERIOR)
# =========================
ontem = date.today() - timedelta(days=1)
data_completa = ontem.strftime('%Y-%m-%d')

# =========================
# SESSÃO
# =========================
session = requests.Session()
payload = {"email": LOGIN_IN, "password": SENHA_IN}
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

# =========================
# LOGIN
# =========================
response = session.post(URL_LOGIN, data=payload, headers=headers)

cookie = session.cookies.get("inlabs_session_cookie")
if not cookie:
    raise Exception("Falha no login. Cookie não obtido.")

# =========================
# DOWNLOAD DOS ZIPs
# =========================
zips = []

for secao in TIPO_DOU.split():
    nome_zip = f"{data_completa}-{secao}.zip"
    url = f"{URL_DOWNLOAD}{data_completa}&dl={nome_zip}"

    print(f"⬇️ Baixando {nome_zip}...")
    r = session.get(url, headers={"Cookie": f"inlabs_session_cookie={cookie}"})

    if r.status_code == 200:
        with open(nome_zip, "wb") as f:
            f.write(r.content)
        zips.append(nome_zip)
        print(f"✅ Salvo: {nome_zip}")
    else:
        print(f"⚠️ Não encontrado: {nome_zip}")

# =========================
# PROCESSAMENTO DOS XMLs
# =========================
resultados = []

for zip_name in zips:
    with zipfile.ZipFile(zip_name, "r") as z:
        for nome_xml in z.namelist():
            if nome_xml.lower().endswith(".xml"):
                with z.open(nome_xml) as f:
                    conteudo = f.read().decode("utf-8", errors="ignore")

                if TERMO in conteudo:
                    root = ET.fromstring(conteudo)
                    article = root.find(".//article")

                    if article is not None:
                        name = article.attrib.get("name")
                        pdf_page = article.attrib.get("pdfPage")

                        resultados.append((name, pdf_page))

                        print("✅ ENCONTRADO")
                        print(f"ZIP: {zip_name}")
                        print(f"XML: {nome_xml}")
                        print(f"NAME: {name}")
                        print(f"PDFPAGE: {pdf_page}")

# =========================
# ENVIO DE EMAIL (SE HOUVER RESULTADO)
# =========================
if resultados:
    msg = EmailMessage()
    msg["Subject"] = "Publicações encontradas no DOU"
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINO

    corpo = f"""Olá,

Foram encontradas as seguintes publicações no DOU ({data_completa})
contendo "UNIVERSIDADE TECNOLÓGICA FEDERAL DO PARANÁ":

"""

    for name, pdf in resultados:
        corpo += f"- {name}\n  {pdf}\n\n"

    corpo += "Atenciosamente,\nScript Colab"

    msg.set_content(corpo)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_REMETENTE, SENHA_APP)
        smtp.send_message(msg)

    print("📧 E-mail enviado com sucesso")
else:
    print("ℹ️ Nenhuma ocorrência encontrada. E-mail não enviado.")

# =========================
# LIMPEZA DOS ZIPs
# =========================
for zip_name in zips:
    try:
        os.remove(zip_name)
        print(f"🗑️ ZIP removido: {zip_name}")
    except Exception as e:
        print(f"⚠️ Erro ao remover {zip_name}: {e}")



