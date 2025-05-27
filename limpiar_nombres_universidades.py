import pandas as pd
import re

def limpiar_nombres_universidades():
    """
    Limpia los números del formato "1. ", "2. ", etc. del inicio de los nombres de universidades
    en los archivos Destinos.csv y ReporteGestionPlazas.csv
    """
    
    # Función para limpiar el nombre
    def limpiar_nombre(nombre):
        # Usar regex para eliminar el patrón "número. " del inicio
        return re.sub(r'^\d+\.\s*', '', str(nombre))
    
    print("🧹 Limpiando nombres de universidades...")
    
    # 1. Limpiar Destinos.csv
    print("   📄 Procesando Destinos.csv...")
    destinos_df = pd.read_csv('data/Destinos.csv')
    destinos_df['NombreDestino'] = destinos_df['NombreDestino'].apply(limpiar_nombre)
    destinos_df.to_csv('data/Destinos.csv', index=False)
    print(f"   ✅ Limpiados {len(destinos_df)} destinos")
    
    # 2. Limpiar ReporteGestionPlazas.csv
    print("   📄 Procesando ReporteGestionPlazas.csv...")
    reporte_df = pd.read_csv('data/ReporteGestionPlazas.csv')
    reporte_df['NombreDestino'] = reporte_df['NombreDestino'].apply(limpiar_nombre)
    reporte_df.to_csv('data/ReporteGestionPlazas.csv', index=False)
    print(f"   ✅ Limpiados {len(reporte_df)} registros del reporte")
    
    # Mostrar algunos ejemplos de antes y después
    print("\n📋 Ejemplos de nombres limpiados:")
    ejemplos = [
        "1. Universidad de Heidelberg",
        "25. Universidad de Ljubljana", 
        "100. Universidad de Aveiro",
        "372. Universidad de Última"
    ]
    
    for ejemplo in ejemplos:
        limpio = limpiar_nombre(ejemplo)
        print(f"   • '{ejemplo}' → '{limpio}'")
    
    print("\n✅ Limpieza completada. Los archivos han sido actualizados.")

if __name__ == "__main__":
    limpiar_nombres_universidades() 