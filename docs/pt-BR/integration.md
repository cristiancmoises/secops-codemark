# Integrar ao fluxo de lançamento

CodeMark é uma CLI local. Não exige daemon, extensão de navegador, conta de serviço, telemetria ou processo em segundo plano.

## Um lançamento reproduzível

1. Comece pela revisão de fonte pretendida e execute os testes do projeto.
2. Confira a prévia de marcação de um módulo próprio e suas exclusões.
3. Aplique as marcas e execute os testes do projeto novamente.
4. Revise e versione os fontes pretendidos e os metadados do manifesto.
5. Assine com uma chave confiável existente quando precisar de autenticação.
6. Preserve revisão, manifesto, assinatura e referência de chave pública de forma independente.

Marque apenas código para o qual o titular informado é apropriado. Diretórios conhecidos de dependências são excluídos, mas caminhos arbitrários de terceiros não são reconhecidos automaticamente.

## Verificação no CI

```sh
python3 /confiavel/codemark.pyz verify /checkout --ssh-public-key /confiavel/codemark.pub --ssh-fingerprint 'SHA256:SEU_FINGERPRINT_COMPLETO' --json
```

Faça checkout da revisão que pretende verificar. Proteja executável, chave e fingerprint contra a contribuição não confiável em análise. Nos jobs de verificação, execute `verify` com a referência aprovada. Executar `mark --apply` antes aceitaria as mudanças atuais como nova referência.

Um hook local opcional pode executar o mesmo comando. CodeMark não instala hooks. A verificação examina a árvore de trabalho, não o snapshot do índice Git.

## Guardar relatórios fora da árvore

```sh
python3 codemark.pyz verify /checkout --json --output /relatorios/verificacao-NOVA.json
```

Use um destino novo e externo às árvores tratadas, aguarde o término e registre o código de saída. Preserve evidências de falhas e sucessos ao decidir um lançamento.

## GNU Guix

A CLI usa o Python do seu perfil. Um possível ambiente temporário é:

```sh
guix shell python -- python3 codemark.pyz doctor --json
```

Assinaturas também precisam de OpenSSH ou GnuPG. A GUI opcional requer Tkinter e sessão gráfica. Os exemplos são orientações de uso; não afirmam um pacote Guix qualificado ou build da plataforma. Consulte a [validação atual](validation.md).

## Distribuição do fonte

Para desenvolver e gerar artefatos, veja [Contribuir](wiki/contributing.md). O formato dos arquivos de lançamento e suas verificações seguem o script de build e a documentação atuais do repositório. Checksums exigem uma referência confiável independente.
