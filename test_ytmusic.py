"""Testa a lógica de match com resultados simulados (não usa a rede)."""
from parser import limpar_titulo
from ytmusic import buscar_faixa, escolher_faixa


class FakeYT:
    def __init__(self, tabela, erro=False):
        self.tabela, self.erro = tabela, erro

    def search(self, consulta, filter=None, limit=5):
        if self.erro:
            raise ConnectionError("sem rede")
        return self.tabela


def r(vid, titulo, artistas, dur):
    return {"videoId": vid, "title": titulo, "duration_seconds": dur,
            "artists": [{"name": a} for a in artistas]}


def faixa(titulo, canal=None, dur=None):
    f = limpar_titulo(titulo, canal)
    f.update(titulo_original=titulo, duracao_s=dur)
    return f


falhas = 0
def checar(nome, cond):
    global falhas
    falhas += not cond
    print("OK   " if cond else "FALHA", nome)

# 1) escolhe a versão certa entre resultados parecidos
yt = FakeYT([
    r("errado1", "Casa do Pai (Karaokê)", ["Banda Qualquer"], 200),
    r("certo", "Casa do Pai", ["Aline Barros"], 301),
    r("errado2", "Casa", ["Aline Barros"], 180),
])
m = buscar_faixa(yt, faixa("Aline Barros - Casa do Pai (Ao Vivo) - DVD Extraordinária Graça", "Aline Barros", 300))
checar("escolhe a faixa certa", m and m["video_id"] == "certo")

# 2) resultado irrelevante => None (cai no fallback do vídeo original)
yt = FakeYT([r("x", "Outra Coisa Totalmente", ["Fulano"], 100)])
checar("rejeita resultado irrelevante", buscar_faixa(yt, faixa("Era Eu | Melk Villar (Clipe Oficial)")) is None)

# 3) falha de rede não pode virar "não encontrada"
try:
    buscar_faixa(FakeYT([], erro=True), faixa("Era Eu | Melk Villar"))
    checar("propaga erro de rede", False)
except RuntimeError:
    checar("propaga erro de rede", True)

# 4) acento e caixa não atrapalham
yt = FakeYT([r("ok", "Tu És Deus", ["Paulo Cesar Baruk"], 280)])
m = buscar_faixa(yt, faixa("TU ES DEUS - Paulo Cesar Baruk", "Paulo Cesar Baruk"))
checar("ignora acento/caixa", m and m["video_id"] == "ok")

# 5) medley usa sempre o vídeo original, mesmo que a busca ache uma música avulsa parecida
yt = FakeYT([r("avulsa", "Eu Navegarei", ["Gabriela Rocha"], 440)])
f = faixa("Ester Oliveira | Eu navegarei + Então profetiza ❤️‍🔥 [Cover]", "Ester Oliveira", 435)
f["video_id"] = "VIDEO_ESTER"
e = escolher_faixa(yt, f)
checar("medley usa vídeo original", e and e["video_id"] == "VIDEO_ESTER" and e["origem"] == "video_original")

# 6) faixa normal sem match cai no vídeo original; com match usa a busca
f = faixa("Duda Pradino - Na Terra Como No Céu", "Duda Pradino", 442); f["video_id"] = "VIDEO_DUDA"
checar("sem match cai no vídeo original",
       escolher_faixa(FakeYT([r("x", "Nada a ver", ["Outro"], 100)]), f)["video_id"] == "VIDEO_DUDA")
checar("com match usa a busca",
       escolher_faixa(FakeYT([r("oficial", "Na Terra Como No Céu", ["Duda Pradino"], 440)]), f)["video_id"] == "oficial")

# 7) título idêntico de OUTRO artista é rejeitado (cai no vídeo original)
f = faixa("GABRIELA ROCHA - EU NAVEGAREI", "Gabriela Rocha", 471); f["video_id"] = "V_GABI"
yt = FakeYT([r("outro", "Eu Navegarei", ["Fulano Cover"], 471)])
checar("rejeita mesmo título com artista errado", buscar_faixa(yt, f) is None)

# 8) colaboração: precisa ter os dois artistas
f = faixa("JULLIANY SOUZA, GABRIELA ROCHA - GLORY TO CHRIST (LIVE)", "Julliany Souza", 579)
checar("aceita quando os dois artistas aparecem",
       buscar_faixa(FakeYT([r("dupla", "Glory To Christ", ["Julliany Souza", "Gabriela Rocha"], 580)]), f)["video_id"] == "dupla")
checar("rejeita quando falta um dos artistas",
       buscar_faixa(FakeYT([r("solo", "Glory To Christ", ["Julliany Souza"], 580)]), f) is None)

# 9) parser incerto (confiança baixa) ainda acha com artista/música invertidos
f = faixa("Casa do Pai - Aline Barros", None, 300)          # sem canal => ordem incerta
f["artista"], f["musica"], f["confianca"] = "Casa do Pai", "Aline Barros", "baixa"
checar("tolera inversão quando confiança baixa",
       buscar_faixa(FakeYT([r("ok", "Casa do Pai", ["Aline Barros"], 301)]), f)["video_id"] == "ok")

raise SystemExit(1 if falhas else 0)
