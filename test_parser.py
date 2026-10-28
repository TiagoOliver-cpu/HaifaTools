from parser import limpar_titulo

# (título, canal, artista esperado, música esperada)
CASOS = [
    ("Santo + Oh Quão Lindo esse Nome é - Jadson Moreno - Ministração Ao Vivo",
     None, "Jadson Moreno", "Santo + Oh Quão Lindo esse Nome é"),
    ("Era Eu | Melk Villar (Clipe Oficial)",
     None, "Melk Villar", "Era Eu"),
    ("TU ÉS DEUS (A ELE) - O Canto das Igrejas, Paulo Cesar Baruk, Lucas & Evelyn Cortazio",
     None, "O Canto das Igrejas, Paulo Cesar Baruk, Lucas & Evelyn Cortazio", "TU ÉS DEUS (A ELE)"),
    ("Aline Barros - Casa do Pai (Ao Vivo) - DVD Extraordinária Graça",
     None, "Aline Barros", "Casa do Pai"),
    ("Tu És Deus + Sublime (Medley) | Live Performance - KeyCam | Francesco Xavier",
     None, "Francesco Xavier", "Tu És Deus + Sublime"),
    # com pista do canal
    ("Casa do Pai - Aline Barros", "Aline Barros", "Aline Barros", "Casa do Pai"),
    # casos reais do teste da playlist "Domingo Noite"
    ("JULLIANY SOUZA, GABRIELA ROCHA - GLORY TO CHRIST (LIVE)", "Julliany Souza",
     "JULLIANY SOUZA, GABRIELA ROCHA", "GLORY TO CHRIST"),
    ("GABRIELA ROCHA - EU NAVEGAREI (CLIPE OFICIAL) | EP CÉU", "Gabriela Rocha",
     "GABRIELA ROCHA", "EU NAVEGAREI"),
    ("Ester Oliveira | Eu navegarei + Então profetiza ❤️‍🔥 [Cover]", "Ester Oliveira",
     "Ester Oliveira", "Eu navegarei + Então profetiza"),
    ("Carol Braga | É Ele / Agnus Dei - Ministração Ao Vivo", "Carol Braga",
     "Carol Braga", "É Ele / Agnus Dei"),
    ("Sublime (Ao Vivo) | fhop music", "Fhop Music", "fhop music", "Sublime"),
    ("Duda Pradino - Na Terra Como No Céu (Here as in Heaven)", "Duda Pradino",
     "Duda Pradino", "Na Terra Como No Céu (Here as in Heaven)"),
    ("Pré-Venda de Fé - Fulano", "Fulano", "Fulano", "Pré-Venda de Fé"),
]

falhas = 0
for titulo, canal, art, mus in CASOS:
    r = limpar_titulo(titulo, canal)
    ok = r["artista"] == art and r["musica"] == mus
    falhas += not ok
    print(("OK  " if ok else "FALHA"), "|", titulo)
    print(f"      artista={r['artista']!r} musica={r['musica']!r} confianca={r['confianca']}")
    if not ok:
        print(f"      esperado: artista={art!r} musica={mus!r}")
print(f"\n{len(CASOS) - falhas}/{len(CASOS)} casos corretos")
raise SystemExit(1 if falhas else 0)
