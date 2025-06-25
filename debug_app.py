#!/usr/bin/env python3
"""
Script per diagnosticar problemes amb l'aplicació
"""

import os
import sys
import importlib.util

def check_file_exists(filepath, description):
    """Comprova si un fitxer existeix"""
    exists = os.path.isfile(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def check_module_import(module_name, filepath=None):
    """Comprova si un mòdul es pot importar"""
    try:
        if filepath:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            __import__(module_name)
        print(f"✅ Mòdul '{module_name}' importat correctament")
        return True
    except Exception as e:
        print(f"❌ Error important mòdul '{module_name}': {e}")
        return False

def check_config(config_file):
    """Comprova la configuració"""
    print(f"\n📋 Comprovant configuració: {config_file}")
    
    if not check_file_exists(config_file, "Fitxer de configuració"):
        return False
    
    try:
        spec = importlib.util.spec_from_file_location("config", config_file)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        
        # Comprova atributs essencials
        required_attrs = ['dbpath', 'theme']
        for attr in required_attrs:
            if hasattr(config, attr):
                value = getattr(config, attr)
                print(f"✅ {attr}: {value}")
            else:
                print(f"⚠️  Atribut opcional '{attr}' no trobat")
        
        return True
        
    except Exception as e:
        print(f"❌ Error carregant configuració: {e}")
        return False

def check_database(config_file):
    """Comprova la base de dades"""
    print(f"\n🗄️  Comprovant base de dades...")
    
    try:
        spec = importlib.util.spec_from_file_location("config", config_file)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        
        dbpath = getattr(config, 'dbpath', './db/links.db')
        
        # Comprova si el directori de la BD existeix
        db_dir = os.path.dirname(dbpath)
        if db_dir and not os.path.exists(db_dir):
            print(f"⚠️  Directori de BD no existeix: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
            print(f"✅ Directori creat: {db_dir}")
        
        # Comprova si la BD existeix
        if os.path.isfile(dbpath):
            print(f"✅ Base de dades trobada: {dbpath}")
        else:
            print(f"⚠️  Base de dades no trobada: {dbpath}")
            # Comprova si hi ha base.sql
            if os.path.isfile('base.sql'):
                print("✅ Esquema base.sql trobat")
            else:
                print("❌ Esquema base.sql no trobat")
        
        return True
        
    except Exception as e:
        print(f"❌ Error comprovant base de dades: {e}")
        return False

def check_templates(config_file):
    """Comprova els templates"""
    print(f"\n🎨 Comprovant templates...")
    
    try:
        spec = importlib.util.spec_from_file_location("config", config_file)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        
        theme = getattr(config, 'theme', 'default')
        template_dir = os.path.join('templates', theme)
        
        if os.path.isdir(template_dir):
            print(f"✅ Directori de templates trobat: {template_dir}")
            
            # Comprova templates essencials
            templates = ['index.html', 'addlink.html', 'view.html']
            for template in templates:
                template_path = os.path.join(template_dir, template)
                check_file_exists(template_path, f"Template {template}")
        else:
            print(f"⚠️  Directori de templates no trobat: {template_dir}")
            print("   L'aplicació utilitzarà HTML de fallback")
        
        return True
        
    except Exception as e:
        print(f"❌ Error comprovant templates: {e}")
        return False

def check_database_connectivity(config_file):
    """Prova la connexió real a la base de dades"""
    print(f"\n🔗 Provant connexió a la base de dades...")
    
    try:
        # Importa dbtools si existeix
        if not os.path.isfile('dbtools.py'):
            print("❌ dbtools.py no trobat, no es pot provar la connexió")
            return False
            
        spec = importlib.util.spec_from_file_location("dbtools", "dbtools.py")
        dbtools = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dbtools)
        
        # Carrega configuració
        spec = importlib.util.spec_from_file_location("config", config_file)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        
        dbpath = getattr(config, 'dbpath', './db/links.db')
        
        # Prova connexió
        conn = dbtools.create_connection(dbpath)
        if conn:
            print("✅ Connexió a la base de dades correcta")
            
            # Prova consulta bàsica
            try:
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cur.fetchall()
                print(f"✅ Taules trobades: {[table[0] for table in tables]}")
                
                # Comprova taula links
                cur.execute("SELECT COUNT(*) FROM links")
                count = cur.fetchone()[0]
                print(f"✅ Enllaços a la base de dades: {count}")
                
                conn.close()
                return True
            except Exception as e:
                print(f"⚠️  Error consultant la base de dades: {e}")
                conn.close()
                return False
        else:
            print("❌ No s'ha pogut connectar a la base de dades")
            return False
            
    except Exception as e:
        print(f"❌ Error provant connexió: {e}")
        return False

def test_addlink_functionality(config_file):
    """Prova la funcionalitat d'addlink"""
    print(f"\n🔧 Provant funcionalitat addlink...")
    
    try:
        if not os.path.isfile('addlink.py'):
            print("❌ addlink.py no trobat")
            return False
            
        # Prova importar addlink
        spec = importlib.util.spec_from_file_location("addlink", "addlink.py")
        addlink_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(addlink_module)
        print("✅ Mòdul addlink importat correctament")
        
        # Prova crear connexió
        config_spec = importlib.util.spec_from_file_location("config", config_file)
        config = importlib.util.module_from_spec(config_spec)
        config_spec.loader.exec_module(config)
        
        dbpath = getattr(config, 'dbpath', './db/links.db')
        conn = addlink_module.create_connection(dbpath)
        
        if conn:
            print("✅ AddLink pot connectar a la base de dades")
            conn.close()
            return True
        else:
            print("❌ AddLink no pot connectar a la base de dades")
            return False
            
    except Exception as e:
        print(f"❌ Error provant addlink: {e}")
        return False

def main():
    """Funció principal de diagnòstic"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnòstic de l\'aplicació SLink3')
    parser.add_argument('-c', '--config', type=str, default='config.py',
                       help='Fitxer de configuració (per defecte: config.py)')
    parser.add_argument('--quick', action='store_true',
                       help='Diagnòstic ràpid (només fitxers i imports)')
    parser.add_argument('--verbose', action='store_true',
                       help='Sortida detallada')
    parser.add_argument('--test-db', action='store_true',
                       help='Prova connexió real a la base de dades')
    parser.add_argument('--test-addlink', action='store_true',
                       help='Prova funcionalitat addlink')
    
    args = parser.parse_args()
    
    print("🔍 DIAGNÒSTIC DE L'APLICACIÓ SLINK3")
    print("=" * 50)
    print(f"📁 Directori de treball: {os.getcwd()}")
    print(f"⚙️  Fitxer de configuració: {args.config}")
    print("=" * 50)
    
    # Comprova si el fitxer de configuració existeix
    if not check_file_exists(args.config, "Fitxer de configuració"):
        print("❌ No es pot continuar sense fitxer de configuració")
        sys.exit(1)
    
    # Diagnòstic bàsic sempre
    print("\n📁 Comprovant fitxers essencials...")
    essential_files = [
        ('app.py', 'Aplicació principal'),
        ('addlink.py', 'Mòdul addlink'),
        ('dbtools.py', 'Eines de base de dades'),
        ('base.sql', 'Esquema de base de dades'),
    ]
    
    missing_files = []
    for filepath, description in essential_files:
        if not check_file_exists(filepath, description):
            missing_files.append(filepath)
    
    if missing_files and args.verbose:
        print(f"\n⚠️  Fitxers que falten: {', '.join(missing_files)}")
    
    # Comprova imports
    print("\n📦 Comprovant imports...")
    modules = [
        'flask',
        'sqlite3', 
        'requests',
        'subprocess',
        'datetime',
        'os',
        'sys'
    ]
    
    failed_imports = []
    for module in modules:
        if not check_module_import(module):
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Imports fallits: {', '.join(failed_imports)}")
        if not args.quick:
            print("💡 Prova: pip install flask requests")
    
    # Comprova mòduls locals
    print("\n📦 Comprovant mòduls locals...")
    if check_file_exists('dbtools.py', 'dbtools.py'):
        check_module_import('dbtools', 'dbtools.py')
    
    if not args.quick:
        # Comprova configuració
        config_ok = check_config(args.config)
        
        # Comprova base de dades
        db_ok = check_database(args.config)
        
        # Comprova templates
        templates_ok = check_templates(args.config)
        
        # Tests addicionals si s'especifiquen
        if args.test_db or args.test_addlink:
            if args.test_db:
                check_database_connectivity(args.config)
            
            if args.test_addlink:
                test_addlink_functionality(args.config)
    
    print("\n" + "=" * 50)
    print("✅ Diagnòstic completat!")
    
    if not args.quick:
        print("\n💡 Consells:")
        print("   • Executa amb --quick per un diagnòstic ràpid")
        print("   • Executa amb --test-db per provar la base de dades")
        print("   • Executa amb --test-addlink per provar addlink")
        print("   • Executa amb --verbose per més detalls")
        
    print("\n🚀 Per iniciar l'aplicació:")
    print(f"   python app.py -c {args.config} --debug")

if __name__ == "__main__":
    main()