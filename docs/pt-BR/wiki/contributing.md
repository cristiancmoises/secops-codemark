# Contribuir

As contribuições devem manter SecOps Codemark local, limitado, compreensível e com poucas dependências. Leia o [guia de contribuição](../../../CONTRIBUTING.md) e a [política de segurança](../../../SECURITY.md).

## Ciclo de desenvolvimento

```sh
python3 -m codemark --help
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/build_site.py --check
```

Use Python 3.10 ou superior. Testes opcionais de assinatura precisam das ferramentas correspondentes; uma ausência é documentada, não contada como aprovação. Use fixtures sintéticas e chaves efêmeras.

Ao alterar tratamento de fontes, preserve round trips de bytes, prologues protegidos, exclusões, limites, transações, pinagem de assinaturas e comportamento de relatórios. Adicione regressão que exercite o contrato afetado.

## Documentação

Inglês fica em `docs/en`; português brasileiro em `docs/pt-BR`. Atualize ambos ao mudar um contrato visível. `README.md` e `README.pt-BR.md` são as entradas do projeto.

O site é gerado pela biblioteca padrão do Python em `website/public`. Seus assets são HTML/CSS/SVG locais; não adicione JavaScript, rastreadores, fontes web ou assets remotos. Animações CSS precisam respeitar redução de movimento.

## Evidência de lançamento

Use `website/data/release.json` no resumo do site e vincule relatórios datados com escopos exatos. Checks ficam pendentes até serem executados. Preserve evidências históricas e não descreva revisão por agente como auditoria externa.

Não publique prompts privados, instruções de execução, credenciais, históricos privados, chaves reais ou dados do usuário sem relação com o projeto. Os pacotes públicos devem conter apenas material aprovado.

## Licença

SecOps Codemark usa GPL-3.0-or-later. Contribuições precisam ser compatíveis com ela. Preserve avisos existentes e descreva origem e licença de material importado.
