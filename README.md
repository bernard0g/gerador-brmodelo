# brModelo JSON Generator
Um conversor inteligente em Python que transforma arquivos JSON em diagramas nativos `.brM3` para o brModelo.

Criei esse script como uma ponte programática nativa. Ele atua sob o motor do brModelo (invocando o `brModelo.jar` internamente) para montar e gravar o modelo com a mesma exatidão e qualidade da ferramenta original, impossibilitando qualquer corrupção gráfica.

## 🚀 Como funciona
A arquitetura é Híbrida:
1. O Python lê a estrutura JSON de entrada.
2. Injeta as entidades, relacionamentos e ligações em um código Java dinâmico.
3. Compila e executa o motor através do OpenJDK em background.
4. O resultado é o arquivo binário visual `.brM3`, perfeito para o brModelo.

Ideal para montar topologias rapidamente vindas de Engenharia de Prompts ou IA Generativa!

## 📦 Requisitos
- **Python 3.x**
- **Java JDK (ex: Microsoft OpenJDK)**: Certifique-se de que o `javac` e o `java` estejam instalados e no seu PATH do sistema (ou no diretório comum).

## 🛠️ Como Usar

Com seu JSON pronto, abra o terminal e execute:
```bash
python generator.py <seu_arquivo.json> <nome_saida.brM3>
```

**Exemplo:**
```bash
python generator.py exemplo.json meu_diagrama.brM3
```

## 📝 Formato JSON Esperado
O script entende um formato simples focado nas cardinalidades e nós:

```json
{
  "entities": [
    { "name": "Usuario", "x": 100, "y": 100 },
    { "name": "Livro", "x": 300, "y": 100 }
  ],
  "relationships": [
    {
      "name": "Empresta",
      "x": 200,
      "y": 200,
      "connections": [
        { "entity": "Usuario", "cardinality": "(0,n)" },
        { "entity": "Livro", "cardinality": "(1,n)" }
      ]
    }
  ]
}
```

Espero que essa ferramenta facilite seu ecossistema brModelo tanto quanto o meu! Divirta-se.
