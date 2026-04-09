# brModelo JSON Generator Avançado

Um conversor inteligente em Python que transforma arquivos JSON em diagramas conceituais nativos `.brM3` para o brModelo usando a Simbologia de Peter Chen.

Criei esse script como uma ponte programática nativa. Ele atua sob o motor do brModelo (invocando o `brModelo.jar` internamente) para montar e gravar o modelo com a mesma exatidão e qualidade da ferramenta original, impossibilitando qualquer corrupção gráfica.

## Evolução Completa (Nova Arquitetura)
O motor foi reescrito para transcender cardinalidades básicas e agora é um gerador conceitual semântico completo:
- **Entidades e Relacionamentos com Atributos** (Simples, Chave/Primários, Multivalorados, Derivados, e Compostos).
- **Entidades Fracas e Relacionamentos Identificadores**.
- **Especialização e Generalização** com auto-conexão.
- **Validação Semântica** embutida (previne duplicações, entidades fantasmas, e esquemas rompidos).
- **Auto-Layout Dinâmico (Physics-Like)**: Posicionamento autônomo.

Ideal para montar topologias massivas rapidamente vindas de Engenharia de Prompts ou IA Generativa!

## Requisitos
- **Python 3.x**
- **Java JDK (ex: Microsoft OpenJDK)**: Certifique-se de que o `javac` e o `java` estejam instalados e no seu PATH do sistema (ou no diretório comum).

## Como Usar

> **IMPORTANTE:** Este script (`generator.py`) obrigatoriamente precisa estar **na mesma pasta** que o arquivo `brModelo.jar` para conseguir invocar as classes nativas do sistema durante a geração do diagrama. A pasta atual do repositório já contém a arquitetura pronta.

Com seu JSON pronto, abra o terminal e execute:
```bash
python generator.py <seu_arquivo.json> <nome_saida.brM3>
```

**Validando os Novos Exemplos**
A pasta `exemplos/` abriga implementações ricas (`biblioteca.json`, `loja.json`, `fraca.json`, `especializacao.json`, `clinica.json`). Experimente o caso de teste obrigatório da Biblioteca:
```bash
python generator.py exemplos/biblioteca.json biblioteca.brM3
```

## Formato JSON Suportado
A nova arquitetura também fornece formalização via `schema.json`. O script entende o antigo formato e atua com retrocompatibilidade, mas recomenda a estrutura atual:

```json
{
  "settings": {
    "autoLayout": true
  },
  "entities": [
    {
      "name": "Dependente",
      "weak": true,
      "attributes": [
        { "name": "id_dependente", "partial_key": true },
        { "name": "nome_completo", "composite": true, "components": [{"name": "primeiro_nome"}] }
      ]
    }
  ],
  "relationships": [
    {
      "name": "Possui",
      "identifying": true,
      "attributes": [],
      "connections": [
        { "entity": "Funcionario", "cardinality": "(1,1)" },
        { "entity": "Dependente", "cardinality": "(0,n)" }
      ]
    }
  ],
  "generalizations": [
    {
      "supertype": "Pessoa",
      "subtypes": ["Fisica", "Juridica"],
      "total": true
    }
  ]
}
```

### Opções de Atributos
- `"key": true` ou `"partial_key": true` -> Desenha o atributo como Identificador/Chave.
- `"multivalued": true` -> Desenha Atributo Multivalorado.
- `"derived": true` -> Desenha Atributo Derivado (tracejado, equivalente ao Opcional em brM3).
- `"composite": true` e `"components": [...]` -> Permite aninhar atributos em Atributos Compostos.

## Limitações Restantes
- **Complexidade de Layout**: Embora tenha um Auto-Layout de anel funcional implementado (`settings.autoLayout`), o modelo dinâmico cruza muitas linhas em topologias gigantescas (fator intrínseco de grafos). Para o refinamento final e reposicionamento fino, basta arrastar os elementos visualmente no programa brModelo após a importação.
- **Injeção de Cardinalidades Extras**: Apenas cardinalidades oficiais do framework brModelo sào mapeadas pelo Enum original. Extensões fora de `(0,n)`, `(1,n)`, `(1,1)`, `(0,1)` caem pro comportamento default.

## Detalhes Técnicos - Engenharia do brModelo
A arquitetura de alto-nível injeta os conceitos na API nativa do `chcandido` lendo comportamentos profundos do motor de layout:
- Relacionamentos Identificadores e Entidades Fracas se conectam instruindo via Java `ligacao.setDuplaLinha(true)` nas ligações em vez de alterar a tipagem da entidade diretamente, como mapeado pelo jar oficial.
- Generalizações operam injetando subclasses `Especializacao(dia)` com o motor do brM3 resolvendo exclusividades.
- A orquestração Java isola o usuário Python de lidar com os pipelines `Reenquadre`, `Add(Item)` e fluxos do OutputStream Binário `GuardaPadraoBrM`.
