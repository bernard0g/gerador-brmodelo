import json
import os
import sys
import subprocess

def generate_java_code(json_file_path, output_brm3_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Template do código Java que eu vou injetar pra abstrair a UI do brModelo
    java_code = """
import controlador.Editor;
import diagramas.conceitual.DiagramaConceitual;
import diagramas.conceitual.Entidade;
import diagramas.conceitual.Relacionamento;
import diagramas.conceitual.Ligacao;
import desenho.preAnyDiagrama.PreCardinalidade;
import java.awt.Point;

public class BrmAutoGenerator {
    public static void main(String[] args) {
        try {
            System.setProperty("java.awt.headless", "true");
            Editor omaster = new Editor();
            DiagramaConceitual dia = new DiagramaConceitual(omaster);
            
"""
    entities_map = {}
    
    # 1. Eu crio as Entidades baseado no JSON
    if "entities" in data:
        for i, ent in enumerate(data["entities"]):
            name = ent["name"]
            x = ent["x"]
            y = ent["y"]
            var_name = f"ent_{i}"
            entities_map[name] = var_name
            java_code += f"""
            Entidade {var_name} = new Entidade(dia, "{name}");
            {var_name}.setTexto("{name}");
            {var_name}.SetBounds({x}, {y}, 120, 58);
            {var_name}.Reenquadre();
            dia.getListaDeItens().add({var_name});
"""

    # 2. Eu gero os Relacionamentos e amarro as Ligações
    if "relationships" in data:
        for i, rel in enumerate(data["relationships"]):
            name = rel["name"]
            x = rel["x"]
            y = rel["y"]
            rel_var = f"rel_{i}"
            java_code += f"""
            Relacionamento {rel_var} = new Relacionamento(dia, "{name}");
            {rel_var}.setTexto("{name}");
            {rel_var}.SetBounds({x}, {y}, 150, 50);
            {rel_var}.Reenquadre();
            dia.getListaDeItens().add({rel_var});
"""
            # Add connections
            for j, conn in enumerate(rel.get("connections", [])):
                ent_name = conn["entity"]
                card = conn["cardinality"]
                ent_var = entities_map.get(ent_name)
                
                if ent_var:
                    # O brModelo usa Enums específicos pras cardinalidades: PreCardinalidade.TiposCard.C01, C11, C1N, C0N
                    card_enum = "PreCardinalidade.TiposCard.C0N"
                    if card == "(0,1)": card_enum = "PreCardinalidade.TiposCard.C01"
                    elif card == "(1,1)": card_enum = "PreCardinalidade.TiposCard.C11"
                    elif card == "(1,n)": card_enum = "PreCardinalidade.TiposCard.C1N"
                    elif card == "(n,1)": card_enum = "PreCardinalidade.TiposCard.C1N" # Não existe Cn1 direto na API, uso C1N porque visualmente o brModelo mapeia assim
                    elif card == "(0,n)": card_enum = "PreCardinalidade.TiposCard.C0N"

                    java_code += f"""
            Ligacao lig_{i}_{j} = new Ligacao(dia);
            lig_{i}_{j}.SuperInicie(0, 
                new Point({ent_var}.getLeft() + {ent_var}.getWidth()/2, {ent_var}.getTop() + {ent_var}.getHeight()/2),
                new Point({rel_var}.getLeft() + {rel_var}.getWidth()/2, {rel_var}.getTop() + {rel_var}.getHeight()/2));
            lig_{i}_{j}.getPontaA().SetEm({ent_var});
            lig_{i}_{j}.getPontaB().SetEm({rel_var});
            lig_{i}_{j}.PrepareCardinalidade();
            if (lig_{i}_{j}.getCard() != null) {{
                lig_{i}_{j}.getCard().setCard({card_enum});
            }}
            dia.getListaDeItens().add(lig_{i}_{j});
            if (lig_{i}_{j}.getCard() != null) dia.getListaDeItens().add(lig_{i}_{j}.getCard());
"""

    java_code += f"""
            System.out.println("Saving file to {output_brm3_path}...");
            try (java.io.FileOutputStream fo = new java.io.FileOutputStream("{output_brm3_path}")) {{
                try (java.io.ObjectOutput out = new java.io.ObjectOutputStream(fo)) {{
                    controlador.apoios.GuardaPadraoBrM seg = new controlador.apoios.GuardaPadraoBrM(dia);
                    seg.versaoDiagrama = "3.2.0";
                    out.writeObject(seg);
                }}
            }}
            System.out.println("Saved successfully: true");
            System.exit(0);

        }} catch (Exception e) {{
            e.printStackTrace();
            System.exit(1);
        }}
    }}
}}
"""
    
    # Salvo o template Java no disco pra compilar jajá
    with open('BrmAutoGenerator.java', 'w', encoding='utf-8') as f:
        f.write(java_code)
    
    print("Arquivo BrmAutoGenerator.java gerado com sucesso!")
    
    import glob
    javac_cmd = "javac"
    java_cmd = "java"
    
    from shutil import which
    if which("javac") is None:
        print("=> Procurando JDK em locais comuns (como Microsoft OpenJDK)...")
        possible_javacs = glob.glob("C:/Program Files/Microsoft/jdk*/bin/javac.exe") + \
                          glob.glob("C:/Program Files/Java/jdk*/bin/javac.exe")
        if possible_javacs:
            javac_cmd = possible_javacs[0]
            java_cmd = javac_cmd.replace("javac.exe", "java.exe")
            print(f"=> Encontrado: {javac_cmd}")
        else:
            print("AVISO: 'javac' (JDK) não foi encontrado no PATH do sistema.")
            print("Para compilar e gerar o .brM3, instale o Java JDK e execute manualmente:")
            print(f"1) javac -cp brModelo.jar BrmAutoGenerator.java")
            print(f"2) java -cp brModelo.jar;. BrmAutoGenerator")
            return
            
    # Compilo e rodo chamando o Java localmente debaixo dos panos
    print("Compilando código Java dinâmico...")
    cp_sep = ";" if os.name == 'nt' else ":"
    try:
        subprocess.run([javac_cmd, "-cp", f"brModelo.jar{cp_sep}.", "BrmAutoGenerator.java"], check=True, capture_output=True, text=True)
        print("Executando gerador brM3...")
        subprocess.run([java_cmd, "-cp", f"brModelo.jar{cp_sep}.", "BrmAutoGenerator"], check=True, capture_output=True, text=True)
        print(f"Sucesso! Arquivo {output_brm3_path} foi gerado e está pronto pro uso.")
    except subprocess.CalledProcessError as e:
        print("ERRO AO EXECUTAR O MOTOR JAVA:")
        print(e.stderr)
        print(e.stdout)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generator.py <input.json> <output.brM3>")
        sys.exit(1)
        
    generate_java_code(sys.argv[1], sys.argv[2])
