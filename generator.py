import json
import os
import sys
import subprocess
import math

def validate_json(data):
    entities = data.get("entities", [])
    relationships = data.get("relationships", [])
    generalizations = data.get("generalizations", [])
    
    ent_names = set()
    for e in entities:
        if "name" not in e: raise ValueError("Entidade sem nome encontrada.")
        if e["name"] in ent_names: raise ValueError(f"Entidade duplicada: {e['name']}")
        ent_names.add(e["name"])
        
        attrs = e.get("attributes", [])
        attr_names = set()
        for a in attrs:
            if "name" not in a: raise ValueError(f"Atributo sem nome na entidade {e['name']}")
            if a["name"] in attr_names: raise ValueError(f"Atributo duplicado: {a['name']}")
            attr_names.add(a["name"])
            if a.get("composite") and not a.get("components"):
                raise ValueError(f"Atributo composto '{a['name']}' sem components na entidade {e['name']}.")
                
    for r in relationships:
        if "name" not in r: raise ValueError("Relacionamento sem nome encontrado.")
        for conn in r.get("connections", []):
            if conn["entity"] not in ent_names:
                raise ValueError(f"Relacionamento '{r['name']}' aponta para entidade inexistente: {conn['entity']}")
    
    for g in generalizations:
        if g.get("supertype") not in ent_names:
            raise ValueError(f"Especializacao aponta para supertypo inexistente: {g.get('supertype')}")
        for sub in g.get("subtypes", []):
            if sub not in ent_names:
                raise ValueError(f"Especializacao aponta para subtypo inexistente: {sub}")

def auto_layout(data):
    settings = data.get("settings", {})
    do_auto = settings.get("autoLayout", False)
    
    entities = data.get("entities", [])
    relationships = data.get("relationships", [])
    generalizations = data.get("generalizations", [])

    for e in entities:
        if "x" not in e or "y" not in e: do_auto = True

    if not do_auto: return data

    ent_count = len(entities)
    center_x, center_y = 600, 400
    radius = max(300, ent_count * 50)

    for i, e in enumerate(entities):
        angle = (2 * math.pi * i) / ent_count if ent_count > 0 else 0
        e["x"] = int(center_x + radius * math.cos(angle))
        e["y"] = int(center_y + radius * math.sin(angle))
        
    ent_map = {e["name"]: e for e in entities}

    for r in relationships:
        conns = r.get("connections", [])
        if not conns:
            r["x"], r["y"] = center_x, center_y
            continue
        avg_x = sum(ent_map[c["entity"]].get("x", center_x) for c in conns) / len(conns)
        avg_y = sum(ent_map[c["entity"]].get("y", center_y) for c in conns) / len(conns)
        r["x"], r["y"] = int(avg_x), int(avg_y)

    for g in generalizations:
        supertype = g.get("supertype")
        if supertype in ent_map:
            sx, sy = ent_map[supertype].get("x", center_x), ent_map[supertype].get("y", center_y)
            g["x"], g["y"] = sx, sy + 150
        else:
            g["x"], g["y"] = center_x, center_y

    return data
    
def generate_java_code(json_file_path, output_brm3_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validations & Layout
    try:
        validate_json(data)
    except Exception as e:
        print(f"Validation Error: {e}")
        sys.exit(1)
        
    data = auto_layout(data)

    java_code = """
import controlador.Editor;
import diagramas.conceitual.DiagramaConceitual;
import diagramas.conceitual.Entidade;
import diagramas.conceitual.Relacionamento;
import diagramas.conceitual.Atributo;
import diagramas.conceitual.Especializacao;
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
    
    # 1. ENTITIES
    for i, ent in enumerate(data.get("entities", [])):
        name = ent["name"]
        x, y = ent["x"], ent["y"]
        var_name = f"ent_{i}"
        entities_map[name] = var_name
        
        java_code += f"""
            Entidade {var_name} = new Entidade(dia, "{name}");
            {var_name}.setTexto("{name}");
            {var_name}.SetBounds({x}, {y}, 120, 58);
            {var_name}.Reenquadre();
            dia.getListaDeItens().add({var_name});
"""
        # Attributes
        java_code += build_attributes(var_name, x, y, ent.get("attributes", []))

    # 2. RELATIONSHIPS
    for i, rel in enumerate(data.get("relationships", [])):
        name = rel["name"]
        x, y = rel["x"], rel["y"]
        rel_var = f"rel_{i}"
        
        java_code += f"""
            Relacionamento {rel_var} = new Relacionamento(dia, "{name}");
            {rel_var}.setTexto("{name}");
            {rel_var}.SetBounds({x}, {y}, 150, 50);
            {rel_var}.Reenquadre();
            dia.getListaDeItens().add({rel_var});
"""
        # Rel Attributes
        java_code += build_attributes(rel_var, x, y, rel.get("attributes", []))

        # Connections
        is_identifying = "true" if rel.get("identifying", False) else "false"
        for j, conn in enumerate(rel.get("connections", [])):
            ent_name = conn["entity"]
            card = conn.get("cardinality", "(0,n)")
            ent_var = entities_map.get(ent_name)
            
            if ent_var:
                is_weak = "true" if next((e for e in data.get("entities", []) if e["name"] == ent_name), {}).get("weak", False) else "false"
                # Enum parse
                card_enum = "PreCardinalidade.TiposCard.C0N"
                if card in ["(0,1)", "0,1", "0..1"]: card_enum = "PreCardinalidade.TiposCard.C01"
                elif card in ["(1,1)", "1,1", "1..1"]: card_enum = "PreCardinalidade.TiposCard.C11"
                elif card in ["(1,n)", "1,n", "1..n"]: card_enum = "PreCardinalidade.TiposCard.C1N"
                elif card in ["(n,1)", "n,1", "n..1"]: card_enum = "PreCardinalidade.TiposCard.C1N"
                
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
            if ({is_weak} || {is_identifying}) {{
                lig_{i}_{j}.setDuplaLinha(true);
            }}
            dia.getListaDeItens().add(lig_{i}_{j});
            if (lig_{i}_{j}.getCard() != null) dia.getListaDeItens().add(lig_{i}_{j}.getCard());
"""

    # 3. GENERALIZATIONS
    for i, gen in enumerate(data.get("generalizations", [])):
        x, y = gen["x"], gen["y"]
        supertype = gen["supertype"]
        is_total = "true" if gen.get("total", False) else "false"
        
        super_var = entities_map.get(supertype)
        if super_var:
            java_code += f"""
            Especializacao esp_{i} = new Especializacao(dia);
            esp_{i}.SetBounds({x}, {y}, 40, 40);
            esp_{i}.setTotal({is_total});
            esp_{i}.Reenquadre();
            dia.getListaDeItens().add(esp_{i});
            
            Ligacao lig_sup_{i} = new Ligacao(dia);
            lig_sup_{i}.SuperInicie(0, 
                new Point({super_var}.getLeft() + {super_var}.getWidth()/2, {super_var}.getTop() + {super_var}.getHeight()/2),
                new Point(esp_{i}.getLeft() + esp_{i}.getWidth()/2, esp_{i}.getTop() + esp_{i}.getHeight()/2));
            lig_sup_{i}.getPontaA().SetEm({super_var});
            lig_sup_{i}.getPontaB().SetEm(esp_{i});
            dia.getListaDeItens().add(lig_sup_{i});
"""
            for j, sub in enumerate(gen.get("subtypes", [])):
                sub_var = entities_map.get(sub)
                if sub_var:
                    java_code += f"""
            Ligacao lig_sub_{i}_{j} = new Ligacao(dia);
            lig_sub_{i}_{j}.SuperInicie(0, 
                new Point(esp_{i}.getLeft() + esp_{i}.getWidth()/2, esp_{i}.getTop() + esp_{i}.getHeight()/2),
                new Point({sub_var}.getLeft() + {sub_var}.getWidth()/2, {sub_var}.getTop() + {sub_var}.getHeight()/2));
            lig_sub_{i}_{j}.getPontaA().SetEm(esp_{i});
            lig_sub_{i}_{j}.getPontaB().SetEm({sub_var});
            dia.getListaDeItens().add(lig_sub_{i}_{j});
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
    with open('BrmAutoGenerator.java', 'w', encoding='utf-8') as f:
        f.write(java_code)
    
    print("Arquivo BrmAutoGenerator.java gerado com sucesso!")
    
    import glob
    from shutil import which
    javac_cmd = "javac"
    java_cmd = "java"
    
    if which("javac") is None:
        print("=> Procurando JDK em locais comuns...")
        possible_javacs = glob.glob("C:/Program Files/Microsoft/jdk*/bin/javac.exe") + \
                          glob.glob("C:/Program Files/Java/jdk*/bin/javac.exe")
        if possible_javacs:
            javac_cmd = possible_javacs[0]
            java_cmd = javac_cmd.replace("javac.exe", "java.exe")
        else:
            print("AVISO: 'javac' não encontrado. Compile manualmente.")
            return

    cp_sep = ";" if os.name == 'nt' else ":"
    try:
        print("Compilando BrmAutoGenerator.java...")
        subprocess.run([javac_cmd, "-cp", f"brModelo.jar{cp_sep}.", "BrmAutoGenerator.java"], check=True, capture_output=True, text=True)
        print("Executando gerador brM3...")
        subprocess.run([java_cmd, "-cp", f"brModelo.jar{cp_sep}.", "BrmAutoGenerator"], check=True, capture_output=True, text=True)
        print(f"Sucesso! {output_brm3_path} gerado.")
    except subprocess.CalledProcessError as e:
        print("ERRO AO EXECUTAR O MOTOR JAVA:")
        print(e.stderr)

def build_attributes(parent_var, ax, ay, attrs):
    res = ""
    for idx, attr in enumerate(attrs):
        attr_name = attr.get("name", f"attr_{idx}")
        attr_var = f"{parent_var}_attr_{idx}"
        is_key = "true" if attr.get("key", False) or attr.get("partial_key", False) else "false"
        is_multi = "true" if attr.get("multivalued", False) else "false"
        is_derived = "true" if attr.get("derived", False) else "false"
        
        nx, ny = ax + 50 + (idx * 20), ay - 60 - (idx * 15)
        res += f"""
            Atributo {attr_var} = new Atributo(dia, "{attr_name}");
            {attr_var}.setTexto("{attr_name}");
            {attr_var}.SetBounds({nx}, {ny}, 80, 40);
            {attr_var}.setIdentificador({is_key});
            {attr_var}.setMultivalorado({is_multi});
            {attr_var}.setOpcional({is_derived});
            {attr_var}.Reenquadre();
            dia.getListaDeItens().add({attr_var});
            
            Ligacao l_{attr_var} = new Ligacao(dia);
            l_{attr_var}.SuperInicie(0, 
                new Point({parent_var}.getLeft() + {parent_var}.getWidth()/2, {parent_var}.getTop() + {parent_var}.getHeight()/2),
                new Point({attr_var}.getLeft() + {attr_var}.getWidth()/2, {attr_var}.getTop() + {attr_var}.getHeight()/2));
            l_{attr_var}.getPontaA().SetEm({parent_var});
            l_{attr_var}.getPontaB().SetEm({attr_var});
            dia.getListaDeItens().add(l_{attr_var});
"""
        if attr.get("composite", False) and attr.get("components"):
            for c_x, comp in enumerate(attr.get("components")):
                sub_var = f"{attr_var}_sub_{c_x}"
                sub_name = comp.get("name", "sub")
                sx, sy = nx + 60, ny - 30 - (c_x*15)
                res += f"""
            Atributo {sub_var} = new Atributo(dia, "{sub_name}");
            {sub_var}.setTexto("{sub_name}");
            {sub_var}.SetBounds({sx}, {sy}, 80, 40);
            {sub_var}.Reenquadre();
            dia.getListaDeItens().add({sub_var});
            
            Ligacao l_{sub_var} = new Ligacao(dia);
            l_{sub_var}.SuperInicie(0, 
                new Point({attr_var}.getLeft() + {attr_var}.getWidth()/2, {attr_var}.getTop() + {attr_var}.getHeight()/2),
                new Point({sub_var}.getLeft() + {sub_var}.getWidth()/2, {sub_var}.getTop() + {sub_var}.getHeight()/2));
            l_{sub_var}.getPontaA().SetEm({attr_var});
            l_{sub_var}.getPontaB().SetEm({sub_var});
            dia.getListaDeItens().add(l_{sub_var});
"""
    return res

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generator.py <input.json> <output.brM3>")
        sys.exit(1)
    generate_java_code(sys.argv[1], sys.argv[2])
